from __future__ import annotations

from sqlalchemy import text

from bank.chat import ask
from bank.db import engine
from bank.provinces import BOT_TO_CODE, province_code_from_nesdc
from bank.query import QueryPlan, _validate_query, execute_plan


def test_province_crosswalk_is_complete():
    assert len(BOT_TO_CODE) == 77
    assert len(set(BOT_TO_CODE.values())) == 77
    assert province_code_from_nesdc("0701 BANGKOK METROPOLIS") == 10
    assert province_code_from_nesdc("0606 PHRA NAKHON SRI AYUTHAYA") == 14


def test_warehouse_periods_and_joins():
    with engine().connect() as conn:
        count, periods, provinces = conn.execute(text(
            "SELECT COUNT(*), COUNT(DISTINCT period), COUNT(DISTINCT province_code) FROM mart_province_month"
        )).one()
        latest = conn.execute(text("SELECT MAX(period) FROM mart_province_month")).scalar_one()
        total = conn.execute(text(
            "SELECT SUM(branches), SUM(deposits_million_baht), SUM(credits_million_baht) "
            "FROM mart_province_month WHERE period=:p"), {"p": latest}).one()
        populated = conn.execute(text(
            "SELECT COUNT(*) FROM mart_province_month WHERE period=:p AND population IS NOT NULL "
            "AND gpp_million_baht IS NOT NULL AND inflation_pct IS NOT NULL"), {"p": latest}).scalar_one()
    assert count == periods * 77 and periods >= 2 and provinces == 77
    # BOT publishes rounded province-million figures. Summing can differ
    # slightly from its independently rounded national grand total.
    assert total[0] == 4516
    assert abs(total[1] - 18136233.0) <= 77
    assert abs(total[2] - 18100244.0) <= 77
    assert populated == 77


def test_query_is_bounded_and_read_only():
    result = execute_plan(QueryPlan(metric="credits", group_by="province", limit=5))
    assert len(result["rows"]) == 5
    assert result["rows"][0]["name_en"] == "Bangkok"
    assert result["rows"][0]["value"] == 13825081.0
    try:
        _validate_query("DELETE FROM mart_province_month")
        assert False, "DELETE must be rejected"
    except ValueError:
        pass


def test_langgraph_rules_mode():
    response = ask("แนวโน้มเงินฝากย้อนหลัง", "test-graph")
    assert response["error"] is None
    assert response["result"]["plan"]["group_by"] == "period"
    assert len(response["result"]["rows"]) >= 2
    assert "ไม่ใช้ AI" in response["mode"]
