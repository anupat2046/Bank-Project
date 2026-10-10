"""Check question answers and cross-question consistency against the real warehouse."""
from bank.competency import QUESTIONS, queries, run_question


def test_ten_competency_queries_and_business_invariants():
    assert len(QUESTIONS) == 10
    assert set(queries()) == {q[0] for q in QUESTIONS}
    answers = {qid: run_question(qid) for qid, *_ in QUESTIONS}
    assert all(answers.values())
    assert all(row["observed_months"] == 12 and 0 <= row["positive_months"] <= 12 for row in answers["CQ01"])
    assert all(0 <= row["gpp_gap_pct"] <= 15 and row["credit_size_ratio"] >= 1 for row in answers["CQ04"])
    assert len({row["period"] for row in answers["CQ05"]}) == len(answers["CQ05"])
    assert all(row["branch_change"] < 0 and row["credit_yoy_pct"] > 0 for row in answers["CQ06"])
    assert all(row["gpp_million_baht"] >= 100000 and row["credits_million_baht"] >= 50000 for row in answers["CQ07"])
    national = sum(row["credits_million"] for row in answers["CQ05"][-1:])
    concentration = answers["CQ10"][0]
    assert concentration["national_credits_million"] == national
    assert 0 <= concentration["bangkok_share_pct"] <= concentration["top5_share_pct"] <= 100
