"""Real-warehouse regression checks; no synthetic banking observations."""
from datetime import date
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from bank.db import engine, read_engine
from bank.query import Clarification, QueryPlan, compile_query, execute_plan, rules_plan


@pytest.mark.parametrize("question,metric,group,province", [
    ("สินเชื่อสูงสุด 5 จังหวัด", "credits", "province", None),
    ("เงินฝากสูงสุด 10 อันดับ", "deposits", "province", None),
    ("สาขาสูงสุด 5 จังหวัด", "branches", "province", None),
    ("สินเชื่อต่อเงินฝากสูงสุด 10", "credit_deposit_ratio", "province", None),
    ("สาขาต่อประชากรสูงสุด 10", "branches_per_100k", "province", None),
    ("เงินฝากต่อหัวสูงสุด 10", "deposits_per_person", "province", None),
    ("GPP สูงสุด 10", "gpp", "province", None),
    ("แนวโน้มสินเชื่อย้อนหลัง", "credits", "period", None),
    ("แนวโน้มเงินฝากย้อนหลัง", "deposits", "period", None),
    ("สาขารายเดือน", "branches", "period", None),
    ("แนวโน้มสินเชื่อต่อเงินฝาก", "credit_deposit_ratio", "period", None),
    ("แนวโน้มสาขาต่อประชากร", "branches_per_100k", "period", None),
    ("แนวโน้มเงินฝากต่อคน", "deposits_per_person", "period", None),
    ("แนวโน้มสินเชื่อจังหวัดเชียงใหม่", "credits", "period", "เชียงใหม่"),
    ("เงินฝากจังหวัดเชียงใหม่", "deposits", "province", "เชียงใหม่"),
    ("สาขาจังหวัดภูเก็ต", "branches", "province", "ภูเก็ต"),
    ("สินเชื่อต่อเงินฝากจังหวัดขอนแก่น", "credit_deposit_ratio", "province", "ขอนแก่น"),
    ("deposits trend", "deposits", "period", None),
    ("credits Bangkok", "credits", "province", "กรุงเทพมหานคร"),
    ("policy rate", "policy_rate", "period", None),
    ("แนวโน้มดอกเบี้ยนโยบาย", "policy_rate", "period", None),
    ("ผลิตภัณฑ์จังหวัดสูงสุด 5", "gpp", "province", None),
    ("สินเชื่อต่ำสุด 5", "credits", "province", None),
    ("branches trend", "branches", "period", None),
    ("เงินฝากต่อคนจังหวัดระยอง", "deposits_per_person", "province", "ระยอง"),
])
def test_rules_intent_and_execution(question, metric, group, province):
    plan = rules_plan(question)
    assert (plan.metric, plan.group_by, plan.province) == (metric, group, province)
    result = execute_plan(plan)
    assert result["rows"]
    assert all(row["value"] is not None for row in result["rows"])


def test_policy_month_end_asof_has_no_lookahead():
    with engine().connect() as conn:
        events = conn.execute(text("SELECT COUNT(*), MIN(event_date), MAX(event_date) FROM fact_policy_event")).one()
        lookahead = conn.execute(text("""
            SELECT COUNT(*) FROM mart_province_month m
            WHERE m.policy_event_date > (date_trunc('month', m.period) + interval '1 month - 1 day')::date
        """)).scalar_one()
        mismatches = conn.execute(text("""
            SELECT COUNT(*) FROM mart_province_month m
            JOIN LATERAL (
              SELECT event_date, policy_rate_pct FROM fact_policy_event e
              WHERE e.event_date <= (date_trunc('month', m.period) + interval '1 month - 1 day')::date
              ORDER BY event_date DESC LIMIT 1
            ) e ON TRUE
            WHERE m.policy_event_date IS DISTINCT FROM e.event_date
               OR m.policy_rate_pct IS DISTINCT FROM e.policy_rate_pct
        """)).scalar_one()
    assert events[0] >= 100 and events[2] >= date(2026, 8, 26)
    assert lookahead == mismatches == 0


def test_annual_vintage_no_lookahead_and_coverage():
    with engine().connect() as conn:
        row = conn.execute(text("""
            SELECT COUNT(*) FILTER (WHERE population IS NOT NULL),
                   COUNT(*) FILTER (WHERE gpp_million_baht IS NOT NULL),
                   COUNT(*) FILTER (WHERE inflation_pct IS NOT NULL),
                   COUNT(*) FILTER (WHERE population_reference_year >= EXTRACT(YEAR FROM period)),
                   COUNT(*) FILTER (WHERE gpp_reference_year > EXTRACT(YEAR FROM period)),
                   COUNT(*) FILTER (WHERE inflation_reference_year >= EXTRACT(YEAR FROM period))
            FROM mart_province_month
        """)).one()
    assert row[:3] == (1925, 385, 77)
    assert row[3:] == (0, 0, 0)


def test_read_role_cannot_write_and_catalog_rejects_unsafe():
    with read_engine().connect() as conn:
        assert conn.execute(text("SELECT has_table_privilege(current_user, 'mart_province_month', 'SELECT')")).scalar_one()
        assert not conn.execute(text("SELECT has_table_privilege(current_user, 'mart_province_month', 'INSERT')")).scalar_one()
    with pytest.raises(ValueError):
        compile_query(QueryPlan(metric="policy_rate", group_by="province"))
    with pytest.raises(Clarification):
        rules_plan("ยอด NPL ของธนาคาร A")


def test_all_grafana_panel_queries_execute():
    dashboard = json.loads((Path(__file__).parents[1] / "grafana/dashboards/regional-banking.json").read_text(encoding="utf-8"))
    assert len(dashboard["panels"]) == 13
    with read_engine().connect() as conn:
        for panel in dashboard["panels"]:
            sql = panel["targets"][0]["rawSql"].replace("$__timeFilter(period)", "TRUE")
            assert conn.execute(text(sql)).fetchall(), panel["title"]


def test_trend_limit_returns_most_recent_months():
    result = execute_plan(QueryPlan(metric="credits", group_by="period", limit=3))
    assert [r["period"] for r in result["rows"]] == ["2026-05-01", "2026-06-01", "2026-07-01"]
    policy = execute_plan(QueryPlan(metric="policy_rate", group_by="period", limit=1))
    assert policy["rows"][0]["period"] == "2026-07-01"
    assert "บริบทระดับประเทศ" in policy["caveat"]
