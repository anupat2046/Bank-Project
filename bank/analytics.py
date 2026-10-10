"""Read-only, bounded data contracts for the web application."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import text

from .db import read_engine


def read(sql, parameters=None):
    with read_engine().connect() as conn:
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text("SET LOCAL statement_timeout = '10s'"))
            return [dict(row) for row in conn.execute(text(sql), parameters or {}).mappings()]


def metadata():
    periods = read("SELECT DISTINCT period FROM mart_province_month ORDER BY period DESC")
    provinces = read("SELECT province_code, name_th, name_en FROM dim_province ORDER BY name_th")
    count = read("SELECT COUNT(*) AS rows FROM mart_province_month")[0]["rows"]
    return {"periods": [r["period"] for r in periods], "provinces": provinces, "rows": count}


def resolve_period(period: date | None):
    rows = read("SELECT MAX(period) AS latest FROM mart_province_month")
    latest = rows[0]["latest"]
    if latest is None:
        raise HTTPException(503, "Warehouse is empty")
    selected = period or latest
    if not read("SELECT period FROM dim_month WHERE period=:p AND EXISTS (SELECT 1 FROM mart_province_month WHERE period=:p)", {"p": selected}):
        raise HTTPException(404, "No banking data for this month")
    return selected, latest


def snapshot(period: date | None):
    selected, latest = resolve_period(period)
    rows = read("""SELECT n.*,
        100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0) AS credit_yoy_pct,
        100.0*(n.deposits_million_baht-p.deposits_million_baht)/NULLIF(p.deposits_million_baht,0) AS deposit_yoy_pct,
        n.branches-p.branches AS branch_change
        FROM mart_province_month n LEFT JOIN mart_province_month p
        ON p.province_code=n.province_code AND p.period=(n.period-interval '1 year')::date
        WHERE n.period=:p ORDER BY n.credits_million_baht DESC,n.province_code""", {"p": selected})
    return {"period": selected, "latest_period": latest, "rows": rows}


def overview_data(period: date | None):
    selected, latest = resolve_period(period)
    rows = snapshot(selected)["rows"]
    trend = read("""SELECT period,SUM(credits_million_baht) AS credits,
        SUM(deposits_million_baht) AS deposits,SUM(branches) AS branches,
        MAX(policy_rate_pct) AS policy_rate_pct,MAX(policy_event_date) AS policy_event_date
        FROM mart_province_month WHERE period<=:p GROUP BY period ORDER BY period""", {"p": selected})
    totals = trend[-1]
    previous = next((r for r in trend if r["period"] == selected.replace(year=selected.year-1)), None)
    changes = {}
    for metric in ("credits", "deposits", "branches"):
        base = previous[metric] if previous else None
        changes[metric] = 100*(totals[metric]-base)/base if base else None
    changes["branch_change"] = totals["branches"]-previous["branches"] if previous else None
    total = totals["credits"]
    return {"period": selected, "latest_period": latest, "totals": totals,
            "changes": changes, "trend": trend, "provinces": rows,
            "concentration": {"bangkok_share_pct": 100*sum(r["credits_million_baht"] for r in rows if r["province_code"]==10)/total if total else None,
                              "top5_share_pct": 100*sum(r["credits_million_baht"] for r in rows[:5])/total if total else None}}


def province_history(code: int, period: date | None):
    selected, _ = resolve_period(period)
    rows = read("SELECT * FROM mart_province_month WHERE province_code=:code AND period<=:p ORDER BY period", {"code": code, "p": selected})
    if not rows:
        raise HTTPException(404, "Province has no data")
    return {"period": selected, "rows": rows}


SOURCE_INFO = {
    "bot": ("Bank of Thailand", "Public web table", "Monthly"),
    "dopa": ("DOPA", "TXT files", "Annual December population"),
    "nesdc": ("NESDC", "XLSX workbook", "Annual GPP"),
    "worldbank": ("World Bank", "Public JSON REST API", "Annual national inflation"),
    "policy": ("BOT MPC", "XLSX workbook", "Policy decision events"),
}


def source_data():
    # Do not expose raw_path, error details, SQL connection strings or ETL tokens.
    manifests = read("""SELECT DISTINCT ON (source) source,url,sha256,reference,fetched_at
        FROM source_manifest ORDER BY source,id DESC""")
    for row in manifests:
        title, method, frequency = SOURCE_INFO.get(row["source"], (row["source"], "Public source", "See reference"))
        row.update(title=title, method=method, frequency=frequency, freshness="not_checked")
    runs = read("SELECT source,status,rows_loaded,started_at FROM etl_run ORDER BY id DESC LIMIT 30")
    coverage = read("""SELECT MIN(period) AS first_period,MAX(period) AS latest_period,
        COUNT(DISTINCT province_code) AS provinces,COUNT(DISTINCT period) AS months,COUNT(*) AS rows,
        COUNT(*) FILTER (WHERE gpp_million_baht IS NULL) AS missing_gpp_rows,
        COUNT(*) FILTER (WHERE population IS NULL) AS missing_population_rows,
        COUNT(*) FILTER (WHERE inflation_pct IS NULL) AS missing_inflation_rows FROM mart_province_month""")[0]
    coverage["macro_vintage_date"] = read("SELECT MAX(source_last_updated) AS vintage FROM fact_macro_year")[0]["vintage"]
    return {"sources": manifests, "runs": runs, "coverage": coverage}
