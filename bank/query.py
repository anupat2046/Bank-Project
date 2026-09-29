"""Constrained text-to-SQL: structured intent -> audited SQL templates."""
from __future__ import annotations

import re
from datetime import date
from typing import Literal

import sqlglot
from pydantic import BaseModel, Field
from sqlalchemy import text

from .db import read_engine

Metric = Literal["credits", "deposits", "branches", "credit_deposit_ratio",
                 "branches_per_100k", "deposits_per_person", "gpp", "policy_rate"]
Group = Literal["province", "period"]

METRICS = {
    "credits": ("SUM(credits_million_baht)", "สินเชื่อ", "ล้านบาท"),
    "deposits": ("SUM(deposits_million_baht)", "เงินฝาก", "ล้านบาท"),
    "branches": ("SUM(branches)", "สาขา", "แห่ง"),
    "credit_deposit_ratio": ("100.0 * SUM(credits_million_baht) / NULLIF(SUM(deposits_million_baht), 0)", "สินเชื่อต่อเงินฝาก", "%"),
    "branches_per_100k": ("100000.0 * SUM(branches) / NULLIF(SUM(population), 0)", "สาขาต่อประชากร 100,000 คน", "แห่ง"),
    "deposits_per_person": ("1000000.0 * SUM(deposits_million_baht) / NULLIF(SUM(population), 0)", "เงินฝากต่อผู้มีชื่อในทะเบียน", "บาท/คน"),
    "gpp": ("SUM(gpp_million_baht)", "GPP", "ล้านบาท"),
    "policy_rate": ("MAX(policy_rate_pct)", "อัตราดอกเบี้ยนโยบาย ณ สิ้นเดือน", "%"),
}


class QueryPlan(BaseModel):
    """Only documented metrics and dimensions can be requested."""
    metric: Metric = Field(description="Banking metric to calculate")
    group_by: Group = Field(description="province for latest cross-section; period for time trend")
    province: str | None = Field(default=None, description="Exact Thai or English province name if requested")
    start_period: date | None = None
    end_period: date | None = None
    limit: int = Field(default=10, ge=1, le=77)
    ascending: bool = False


class Clarification(ValueError):
    pass


def _provinces():
    with read_engine().connect() as conn:
        return conn.execute(text("SELECT province_code, name_th, name_en FROM dim_province ORDER BY province_code")).mappings().all()


def rules_plan(question: str) -> QueryPlan:
    """Explicitly labelled non-AI fallback when no model credentials exist."""
    q = question.strip().lower()
    if not q:
        raise Clarification("กรุณาพิมพ์คำถาม")
    metric_patterns = [
        ("credit_deposit_ratio", ["สินเชื่อต่อเงินฝาก", "เครดิตต่อเงินฝาก", "loan to deposit", "ldr"]),
        ("branches_per_100k", ["สาขาต่อประชากร", "branch density", "สาขาต่อแสน"]),
        ("deposits_per_person", ["เงินฝากต่อหัว", "เงินฝากต่อคน", "deposit per person"]),
        ("gpp", ["gpp", "ผลิตภัณฑ์จังหวัด"]),
        ("policy_rate", ["ดอกเบี้ยนโยบาย", "policy rate"]),
        ("branches", ["สาขา", "branches"]),
        ("credits", ["สินเชื่อ", "เครดิต", "credits", "loans"]),
        ("deposits", ["เงินฝาก", "deposits"]),
    ]
    metric = next((name for name, words in metric_patterns if any(w in q for w in words)), None)
    if metric is None:
        raise Clarification("เลือกตัวชี้วัด เช่น สินเชื่อ เงินฝาก สาขา หรือสินเชื่อต่อเงินฝาก")
    group = "period" if metric == "policy_rate" or any(w in q for w in ["แนวโน้ม", "ย้อนหลัง", "รายเดือน", "trend", "เวลา"]) else "province"
    province_name = None
    for p in _provinces():
        if any(name and name.lower() in q for name in [p["name_th"], p["name_en"]]):
            province_name = p["name_th"] or p["name_en"]
            break
    limit_match = re.search(r"(?:top|อันดับ|สูงสุด|ต่ำสุด)\s*(\d{1,2})", q)
    limit = min(int(limit_match.group(1)), 77) if limit_match else (25 if group == "period" else 10)
    return QueryPlan(metric=metric, group_by=group, province=province_name,
                     limit=limit, ascending=any(x in q for x in ["ต่ำสุด", "น้อยสุด", "bottom"]))


def compile_query(plan: QueryPlan) -> tuple[str, dict]:
    expr, _, _ = METRICS[plan.metric]
    with read_engine().connect() as conn:
        latest = conn.execute(text("SELECT MAX(period) FROM mart_province_month")).scalar_one()
    if latest is None:
        raise Clarification("ยังไม่มีข้อมูลในคลังข้อมูล")
    params: dict = {"limit": min(plan.limit, 77)}
    filters = []
    if plan.province:
        matches = [p for p in _provinces() if plan.province.lower() in
                   {str(p["name_th"] or "").lower(), p["name_en"].lower()}]
        if len(matches) != 1:
            raise Clarification(f"ไม่พบจังหวัดที่ตรงกับ {plan.province!r}")
        filters.append("province_code = :province_code")
        params["province_code"] = matches[0]["province_code"]
    if plan.group_by == "province":
        filters.append("period = :period")
        params["period"] = plan.end_period or latest
        grouping = "province_code, name_th, name_en"
        columns = "province_code, name_th, name_en"
        order = "value ASC" if plan.ascending else "value DESC"
    else:
        if plan.start_period:
            filters.append("period >= :start_period")
            params["start_period"] = plan.start_period
        if plan.end_period:
            filters.append("period <= :end_period")
            params["end_period"] = plan.end_period
        grouping = columns = "period"
        order = "period ASC"
    # GPP is a published annual vintage; duplicated monthly values cannot be trended.
    if plan.metric == "gpp" and plan.group_by == "period":
        raise Clarification("GPP เป็นข้อมูลรายปี ไม่ควรแสดงเป็นแนวโน้มรายเดือน")
    if plan.metric == "policy_rate" and (plan.group_by != "period" or plan.province):
        raise Clarification("อัตราดอกเบี้ยนโยบายเป็นระดับประเทศเท่านั้น กรุณาถามแนวโน้มรายเดือน")
    where = " AND ".join(filters) if filters else "TRUE"
    base = (f"SELECT {columns}, {expr} AS value FROM mart_province_month "
            f"WHERE {where} GROUP BY {grouping}")
    if plan.group_by == "period":
        # Take the most recent N observations, then display in chronological order.
        query = f"SELECT * FROM ({base} ORDER BY period DESC LIMIT :limit) recent ORDER BY period ASC"
    else:
        query = f"{base} ORDER BY {order} LIMIT :limit"
    _validate_query(query)
    return query, params


def _validate_query(query: str):
    parsed = sqlglot.parse(query, read="postgres")
    if len(parsed) != 1 or parsed[0] is None or parsed[0].key != "select":
        raise ValueError("Only one SELECT is allowed")
    tables = {t.name for t in parsed[0].find_all(sqlglot.exp.Table)}
    if tables != {"mart_province_month"}:
        raise ValueError("Only the safe mart is queryable")


def execute_plan(plan: QueryPlan) -> dict:
    sql, params = compile_query(plan)
    with read_engine().connect() as conn:
        results = [dict(r) for r in conn.execute(text(sql), params).mappings().all()]
    for r in results:
        if isinstance(r.get("period"), date):
            r["period"] = r["period"].isoformat()
    label, unit = METRICS[plan.metric][1:]
    used_sources = ["BOT FI_CB_011_S5"]
    if plan.metric in {"branches_per_100k", "deposits_per_person"}:
        used_sources.append("DOPA registered population")
    if plan.metric == "gpp":
        used_sources.append("NESDC GPP 2024p")
    if plan.metric == "policy_rate":
        used_sources = ["BOT MPC policy decision workbook"]
    return {"plan": plan.model_dump(mode="json"), "metric_label": label,
            "unit": unit, "sql": sql, "parameters": {k: str(v) for k, v in params.items()},
            "rows": results, "sources": used_sources,
            "caveat": ("อัตราดอกเบี้ยนโยบายเป็นบริบทระดับประเทศ ณ สิ้นเดือน ไม่พิสูจน์ผลเชิงสาเหตุ"
                       if plan.metric == "policy_rate" else
                       "ข้อมูลเป็นยอดคงค้าง ไม่ใช่ยอดปล่อยใหม่; เงินฝาก/สินเชื่อกรุงเทพฯ อาจรวมรายการบันทึกที่สำนักงานใหญ่ และประชากรเป็นทะเบียนบ้าน")}
