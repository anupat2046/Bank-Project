"""Ten documented business questions executed through the read-only DB role."""
from pathlib import Path
import re
from decimal import Decimal

from sqlalchemy import text
from .db import read_engine

QUESTIONS = [
    ("CQ01", "จังหวัดใดมีสินเชื่อเติบโต YoY ต่อเนื่องใน 12 เดือนล่าสุด?", "BOT", "province_code, period, credits_million_baht", "Grafana panel 13", "เปรียบเทียบเดือนเดียวกันปีก่อน และต้องมีคู่ข้อมูลครบ 12 งวด"),
    ("CQ02", "จังหวัดใดเงินฝากโตเร็วกว่าสินเชื่อ YoY มากที่สุด?", "BOT", "province_code, period, deposits_million_baht, credits_million_baht", "Grafana panel 8", "ผลต่างอัตราเติบโตเป็นจุดเปอร์เซ็นต์ ไม่ใช่เปอร์เซ็นต์ของเปอร์เซ็นต์"),
    ("CQ03", "จังหวัดใดมีความหนาแน่นสาขาต่อประชากรแสนคนสูงที่สุด?", "BOT + DOPA", "branches, population, population_reference_year", "Grafana panel 3 / เปรียบเทียบจังหวัด", "ประชากรตามทะเบียนเป็นตัวหาร; ไม่ใช่จำนวนลูกค้าหรือการวัดการเข้าถึงบริการโดยตรง"),
    ("CQ04", "จังหวัดที่ GPP ต่างกันไม่เกิน 15% มีขนาดสินเชื่อต่างกันเท่าไร?", "BOT + NESDC", "gpp_million_baht, gpp_reference_year, credits_million_baht", "GPP เทียบตลาด / หน้า 10 คำถามธุรกิจ", "ไม่รวมกรุงเทพฯ; ผลต่าง GPP หารด้วยค่าที่มากกว่า; GPP รายปีต่างงวดจากสินเชื่อรายเดือน"),
    ("CQ05", "สินเชื่อและเงินฝากรวมเคลื่อนไหวอย่างไรในช่วงที่ดอกเบี้ยนโยบายเปลี่ยน?", "BOT + BOT MPC workbook", "period, policy_rate_pct, credits_million_baht, deposits_million_baht", "ภาพรวมตลาด / Grafana panels 1,10", "policy rate ใช้มติล่าสุดไม่เกินสิ้นเดือน; การเคลื่อนไหวร่วมกันไม่พิสูจน์เหตุและผล"),
    ("CQ06", "จังหวัดใดจำนวนสาขาลดลงแต่สินเชื่อเพิ่มขึ้นเมื่อเทียบปีก่อน?", "BOT", "province_code, period, branches, credits_million_baht", "Grafana panel 9", "เป็นจุดเริ่มตรวจช่องทางบริการเพิ่มเติม; ไม่สรุปว่าสาขาทำให้สินเชื่อเปลี่ยน"),
    ("CQ07", "จังหวัดใดผ่านเกณฑ์ GPP ≥100,000 ลบ., สาขาต่อแสน ≤15 และสินเชื่อ ≥50,000 ลบ.?", "BOT + DOPA + NESDC", "gpp_million_baht, branches_per_100k, credits_million_baht", "คัดพื้นที่ศึกษา / Grafana panel 12", "ไม่รวมกรุงเทพฯ; เกณฑ์ตัวอย่างเพื่อ shortlist และทำ due diligence เพิ่ม"),
    ("CQ08", "จังหวัดใดมีอัตราสินเชื่อต่อเงินฝากสูงที่สุด?", "BOT", "credits_million_baht, deposits_million_baht, credit_deposit_ratio_pct", "จัดอันดับ / Grafana panel 4", "อัตราระดับพื้นที่ไม่ใช่ liquidity ratio ของธนาคารแต่ละแห่ง"),
    ("CQ09", "จังหวัดใดมีเงินฝากต่อผู้มีชื่อในทะเบียนสูงที่สุด?", "BOT + DOPA", "deposits_million_baht, population, population_reference_year", "จัดอันดับ / Grafana panel 5", "ยอดบันทึกสำนักงานใหญ่และประชากรตามทะเบียนมีผล; ไม่ใช่เงินออมเฉลี่ยของลูกค้าจริง"),
    ("CQ10", "สินเชื่อรวมกระจุกตัวในกรุงเทพฯ และ 5 จังหวัดอันดับแรกเท่าไร?", "BOT", "province_code, period, credits_million_baht", "หน้า 10 คำถามธุรกิจ", "ใช้ยอดจังหวัดในเดือนเดียวกัน; การบันทึกสำนักงานใหญ่ไม่ใช่ตำแหน่งผู้กู้หรือส่วนแบ่งรายธนาคาร"),
]


def queries():
    source = (Path(__file__).resolve().parents[1] / "sql/competency_questions.sql").read_text(encoding="utf-8")
    chunks = re.split(r"^-- (CQ\d{2})\s*$", source, flags=re.MULTILINE)
    return {chunks[i]: chunks[i + 1].strip().rstrip(";") for i in range(1, len(chunks), 2)}


def run_question(question_id):
    sql = queries()[question_id]
    with read_engine().connect() as conn:
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text("SET LOCAL statement_timeout = '10s'"))
            return [{key: float(value) if isinstance(value, Decimal) else value
                     for key, value in row.items()} for row in conn.execute(text(sql)).mappings()]
