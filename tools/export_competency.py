"""Generate public CQ evidence from actual read-only warehouse queries."""
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from bank.competency import QUESTIONS, queries, run_question
from bank.db import read_engine


def cell(value):
    if value is None:
        return "NULL"
    if isinstance(value, (float, Decimal)):
        return f"{value:,.2f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-date", default=datetime.now(ZoneInfo("Asia/Bangkok")).date().isoformat())
    verified_date = parser.parse_args().verified_date
    datetime.strptime(verified_date, "%Y-%m-%d")
    root = Path(__file__).resolve().parents[1]
    with read_engine().connect() as conn:
        snapshot = dict(conn.execute(text(
            "SELECT MIN(period) AS first_period, MAX(period) AS latest_period, "
            "COUNT(DISTINCT period) AS months, COUNT(DISTINCT province_code) AS provinces, COUNT(*) AS rows "
            "FROM mart_province_month"
        )).mappings().one())
    results = {qid: run_question(qid) for qid, *_ in QUESTIONS}
    if any(not rows for rows in results.values()):
        raise RuntimeError("A competency query returned no rows; review before publishing evidence")
    lines = ["# Competency questions: executed SQL and recorded results", "",
             f"Recorded on {verified_date} (Asia/Bangkok) from the existing warehouse; no source refresh was performed", "",
             f"Snapshot: **{snapshot['provinces']} provinces × {snapshot['months']} months = {snapshot['rows']:,} rows**; "
             f"periods {snapshot['first_period']}–{snapshot['latest_period']}", "",
             "All questions read `mart_province_month`, integrating dim_province/dim_month and fact_bank_month, "
             "fact_population_year, fact_gpp_year, fact_macro_year, fact_policy_event under the grain/availability rules in "
             "[data model](architecture.md). Queries use PostgreSQL role `bank_reader` in a read-only transaction. Thai question wording matches the application.", "",
             "[All ten SQL queries](../sql/competency_questions.sql) · "
             "[Machine-readable results](evidence/competency-results.json)", "",
             "| ID | Competency question | Sources | Application view | Returned rows |",
             "|---|---|---|---|---|"]
    for qid, title, sources, fields, location, caveat in QUESTIONS:
        lines.append(f"| {qid} | {title} | {sources} | Business questions; {location} | {len(results[qid])} |")
    sql = queries()
    for qid, title, sources, fields, location, caveat in QUESTIONS:
        rows = results[qid]
        keys = list(rows[0])
        lines += ["", f"## {qid} — {title}", "", f"**Fields:** {fields}", "",
                  f"**Interpretation:** {caveat}", "", "```sql", sql[qid] + ";", "```", "",
                  "| " + " | ".join(keys) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
        lines += ["| " + " | ".join(cell(row[k]) for k in keys) + " |" for row in rows]
    lines += ["", "This evidence records SQL/results for the stated snapshot. It does not verify current upstream freshness "
              "or a month of continuous Airflow scheduling. Application screenshots are linked from the README; Gemini is optional "
              "and is not required to execute these ten questions.", ""]
    (root / "docs/competency-questions.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "docs/evidence/competency-results.json").write_text(
        json.dumps({"verified_date": verified_date, "snapshot": snapshot, "results": results},
                   ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Verified {len(results)} queries; rows returned: " + ", ".join(f"{qid}={len(rows)}" for qid, rows in results.items()))


if __name__ == "__main__":
    main()
