"""Idempotent, source-isolated ETL. Failed parses never replace good facts."""
from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import date

from sqlalchemy import delete, insert, select

from . import sources
from .db import (bank, engine, etl_run, gpp, init_db, macro, mart, month,
                 policy, population, province, source_manifest)
from .provinces import BOT_TO_CODE


def _record_manifest(conn, name: str, meta: dict):
    conn.execute(insert(source_manifest).values(source=name, url=meta["url"],
                 raw_path=meta["raw_path"], sha256=meta["sha256"],
                 reference=str(meta.get("reference_year", meta.get("latest", "")))))


def run_source(name: str) -> dict:
    init_db()
    try:
        if name == "bot":
            records, meta = sources.fetch_bot()
            with engine().begin() as conn:
                conn.execute(delete(bank))
                conn.execute(insert(bank), [{**r, "source_sha256": meta["sha256"]} for r in records])
                periods = sorted({r["period"] for r in records})
                conn.execute(delete(month))
                conn.execute(insert(month), [
                    {"period": p, "year_ce": p.year, "year_be": p.year + 543,
                     "month_number": p.month} for p in periods])
                _record_manifest(conn, name, meta)
                for eng, code in BOT_TO_CODE.items():
                    existing = conn.execute(select(province.c.province_code).where(
                        province.c.province_code == code)).scalar_one_or_none()
                    if existing is None:
                        conn.execute(insert(province).values(province_code=code, name_en=eng))
        elif name == "dopa":
            records, metas = sources.fetch_dopa()
            meta_by_year = {m["reference_year"]: m for m in metas}
            with engine().begin() as conn:
                conn.execute(delete(population))
                conn.execute(insert(population), [
                    {k: r[k] for k in ("province_code", "reference_year", "population")}
                    | {"source_sha256": meta_by_year[r["reference_year"]]["sha256"]}
                    for r in records])
                for meta in metas:
                    _record_manifest(conn, name, meta)
                for r in records:
                    conn.execute(province.update().where(province.c.province_code == r["province_code"])
                                 .values(name_th=r["province_th"]))
        elif name == "nesdc":
            records, meta = sources.fetch_nesdc()
            with engine().begin() as conn:
                conn.execute(delete(gpp))
                conn.execute(insert(gpp), [{**r, "source_last_modified": meta["last_modified"],
                                           "source_sha256": meta["sha256"]} for r in records])
                _record_manifest(conn, name, meta)
        elif name == "worldbank":
            records, meta = sources.fetch_world_bank()
            with engine().begin() as conn:
                conn.execute(delete(macro))
                conn.execute(insert(macro), [
                    {**r, "source_last_updated": meta["last_updated"],
                     "source_sha256": meta["sha256"]} for r in records])
                _record_manifest(conn, name, meta)
        elif name == "policy":
            records, meta = sources.fetch_policy_events()
            with engine().begin() as conn:
                conn.execute(delete(policy))
                conn.execute(insert(policy), [{**r, "source_sha256": meta["sha256"]} for r in records])
                _record_manifest(conn, name, meta)
        else:
            raise ValueError(f"Unknown source {name}")
        result = {"source": name, "status": "success", "rows_loaded": len(records)}
    except Exception as exc:
        result = {"source": name, "status": "failed", "rows_loaded": 0,
                  "detail": f"{type(exc).__name__}: {exc}"}
    with engine().begin() as conn:
        conn.execute(insert(etl_run).values(**result))
    return result


def build_mart() -> dict:
    init_db()
    try:
        with engine().connect() as conn:
            bank_rows = conn.execute(select(bank)).mappings().all()
            provinces = {r["province_code"]: r for r in conn.execute(select(province)).mappings()}
            pops = {}
            for row in conn.execute(select(population)).mappings():
                pops.setdefault(row["province_code"], []).append(row)
            gpps = {}
            for row in conn.execute(select(gpp)).mappings():
                gpps.setdefault(row["province_code"], []).append(row)
            macro_rows = conn.execute(select(macro)).mappings().all()
            policy_rows = conn.execute(select(policy)).mappings().all()
        if not bank_rows or len(provinces) != 77:
            raise ValueError("BOT facts and 77 mapped provinces are required")
        rows = []
        for b in bank_rows:
            code, period = b["province_code"], b["period"]
            p = provinces[code]
            end = date(period.year, period.month, monthrange(period.year, period.month)[1])
            available_pop = [x for x in pops.get(code, [])
                             if date(x["reference_year"] + 1, 1, 1) <= end]
            pop = max(available_pop, key=lambda x: x["reference_year"]) if available_pop else None
            # The workbook's HTTP Last-Modified acts as a conservative availability date.
            available_gpp = [x for x in gpps.get(code, [])
                             if x["reference_year"] <= period.year and x["source_last_modified"]
                             and x["source_last_modified"] <= end]
            regional_gpp = max(available_gpp, key=lambda x: x["reference_year"]) if available_gpp else None
            # API metadata supplies the source revision date. Never show today's vintage
            # as if it had been available during earlier historical snapshots.
            available_macro = [x for x in macro_rows if x["reference_year"] < period.year
                               and x["source_last_updated"] <= end]
            inflation = max(available_macro, key=lambda x: x["reference_year"]) if available_macro else None
            available_policy = [x for x in policy_rows if x["event_date"] <= end]
            policy_event = max(available_policy, key=lambda x: x["event_date"]) if available_policy else None
            deposits, credits, branches = b["deposits_million_baht"], b["credits_million_baht"], b["branches"]
            people = pop["population"] if pop else None
            rows.append({"province_code": code, "period": period,
                         "name_en": p["name_en"], "name_th": p["name_th"],
                         "branches": branches, "deposits_million_baht": deposits,
                         "credits_million_baht": credits,
                         "credit_deposit_ratio_pct": credits / deposits * 100 if deposits else None,
                         "population": people,
                         "population_reference_year": pop["reference_year"] if pop else None,
                         "branches_per_100k": branches / people * 100000 if people and branches is not None else None,
                         "deposits_baht_per_person": deposits * 1000000 / people if people and deposits is not None else None,
                         "gpp_million_baht": regional_gpp["gpp_million_baht"] if regional_gpp else None,
                         "gpp_reference_year": regional_gpp["reference_year"] if regional_gpp else None,
                         "inflation_pct": inflation["inflation_pct"] if inflation else None,
                         "inflation_reference_year": inflation["reference_year"] if inflation else None,
                         "policy_rate_pct": policy_event["policy_rate_pct"] if policy_event else None,
                         "policy_event_date": policy_event["event_date"] if policy_event else None})
        if len(rows) != len(bank_rows):
            raise ValueError("Mart lost BOT province-month rows")
        with engine().begin() as conn:
            conn.execute(delete(mart))
            conn.execute(insert(mart), rows)
        result = {"source": "mart", "status": "success", "rows_loaded": len(rows)}
    except Exception as exc:
        result = {"source": "mart", "status": "failed", "rows_loaded": 0,
                  "detail": f"{type(exc).__name__}: {exc}"}
    with engine().begin() as conn:
        conn.execute(insert(etl_run).values(**result))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=["bot", "dopa", "nesdc", "worldbank", "policy", "mart", "all"])
    args = parser.parse_args()
    names = ["bot", "dopa", "nesdc", "worldbank", "policy", "mart"] if args.job == "all" else [args.job]
    for name in names:
        result = build_mart() if name == "mart" else run_source(name)
        print(result)
        if result["status"] != "success":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
