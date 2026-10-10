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
    lines = ["# Competency Questions: 10 คำถามและผล Query จริง", "",
             f"ตรวจเมื่อ {verified_date} (Asia/Bangkok) โดยอ่าน warehouse ที่มีอยู่ ไม่โหลดข้อมูลต้นทางใหม่", "",
             f"Snapshot: **{snapshot['provinces']} จังหวัด × {snapshot['months']} เดือน = {snapshot['rows']:,} แถว**; "
             f"งวด {snapshot['first_period']} ถึง {snapshot['latest_period']}", "",
             "ทุกข้ออ่าน `mart_province_month` ซึ่งรวม dim_province/dim_month และ fact_bank_month, "
             "fact_population_year, fact_gpp_year, fact_macro_year, fact_policy_event ตาม grain/availability ใน "
             "[Data Model](architecture.md). ทุก query รันผ่าน PostgreSQL role `bank_reader` ใน read-only transaction.", "",
             "[SQL ทั้ง 10 ข้อ](../sql/competency_questions.sql) · "
             "[ผลลัพธ์ machine-readable](evidence/competency-results.json)", "",
             "| ID | Competency Question | แหล่งข้อมูล | หน้าที่แสดงผล | แถวที่คืนจริง |",
             "|---|---|---|---|---|"]
    for qid, title, sources, fields, location, caveat in QUESTIONS:
        lines.append(f"| {qid} | {title} | {sources} | 10 คำถามธุรกิจ; {location} | {len(results[qid])} |")
    sql = queries()
    for qid, title, sources, fields, location, caveat in QUESTIONS:
        rows = results[qid]
        keys = list(rows[0])
        lines += ["", f"## {qid} — {title}", "", f"**ฟิลด์:** {fields}", "",
                  f"**บริบทและการตีความ:** {caveat}", "", "```sql", sql[qid] + ";", "```", "",
                  "| " + " | ".join(keys) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
        lines += ["| " + " | ".join(cell(row[k]) for k in keys) + " |" for row in rows]
    lines += ["", "การทดสอบนี้ยืนยัน SQL และผลจาก snapshot ที่ระบุ ไม่ได้ยืนยันว่าแหล่งข้อมูลอัปเดตล่าสุด "
              "หรือ Airflow รันต่อเนื่องครบเดือน. ภาพจากหน้าแอปอยู่ใน README; Gemini เป็นช่องทางเสริม "
              "และไม่จำเป็นต่อการรัน 10 คำถามเหล่านี้.", ""]
    (root / "docs/competency-questions.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "docs/evidence/competency-results.json").write_text(
        json.dumps({"verified_date": verified_date, "snapshot": snapshot, "results": results},
                   ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Verified {len(results)} queries; rows returned: " + ", ".join(f"{qid}={len(rows)}" for qid, rows in results.items()))


if __name__ == "__main__":
    main()
