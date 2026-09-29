"""Build the Thai assignment hand-in PDF from verified project facts.

Run with the bundled Codex Python runtime (reportlab installed).
"""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/thailand-regional-banking-intelligence-report.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont("TahomaThai", r"C:\Windows\Fonts\tahoma.ttf"))
pdfmetrics.registerFont(TTFont("TahomaThai-Bold", r"C:\Windows\Fonts\tahomabd.ttf"))
pdfmetrics.registerFontFamily("TahomaThai", normal="TahomaThai", bold="TahomaThai-Bold")

navy = colors.HexColor("#10244b")
teal = colors.HexColor("#087d65")
grey = colors.HexColor("#526078")
border = colors.HexColor("#dce5e9")
styles = {
    "title": ParagraphStyle("title", fontName="TahomaThai-Bold", fontSize=21, leading=31,
                             textColor=navy, alignment=TA_CENTER, wordWrap="CJK", spaceAfter=9),
    "subtitle": ParagraphStyle("subtitle", fontName="TahomaThai", fontSize=10, leading=17,
                                textColor=grey, alignment=TA_CENTER, wordWrap="CJK", spaceAfter=13),
    "h": ParagraphStyle("h", fontName="TahomaThai-Bold", fontSize=13, leading=21,
                         textColor=navy, wordWrap="CJK", spaceBefore=12, spaceAfter=6),
    "body": ParagraphStyle("body", fontName="TahomaThai", fontSize=9.2, leading=16,
                            textColor=navy, wordWrap="CJK", spaceAfter=5),
    "small": ParagraphStyle("small", fontName="TahomaThai", fontSize=8.2, leading=13.4,
                             textColor=navy, wordWrap="CJK", spaceAfter=3),
    "thead": ParagraphStyle("thead", fontName="TahomaThai-Bold", fontSize=8.3, leading=13,
                             textColor=colors.white, wordWrap="CJK"),
}


def p(value, kind="body"):
    return Paragraph(escape(value), styles[kind])


def table(rows, widths, header=True):
    cells = [[p(str(v), "thead" if header and i == 0 else "small") for v in row]
             for i, row in enumerate(rows)]
    t = Table(cells, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, border),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), navy),
                     ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f7f7")])]
    t.setStyle(TableStyle(commands))
    return t


def scaled_image(path, max_w=170*mm, max_h=113*mm):
    image = Image(str(ROOT / path))
    factor = min(max_w / image.imageWidth, max_h / image.imageHeight)
    image.drawWidth, image.drawHeight = image.imageWidth * factor, image.imageHeight * factor
    return image


story = [
    Spacer(1, 8*mm),
    p("Thailand Regional Banking Intelligence", "title"),
    p("Data Warehouse + Airflow + Grafana + Chatbot | รายงานส่งงาน 28 กันยายน 2569", "subtitle"),
    p("โจทย์ธุรกิจ", "h"),
    p("ทีมกลยุทธ์ธนาคารต้องการเปรียบเทียบขนาดและการเติบโตของตลาดธนาคารพาณิชย์รายจังหวัด ก่อนคัดพื้นที่เพื่อศึกษาต่อ โครงการรวมข้อมูลสาธารณะจริงจากหลายหน่วยงาน โดยเก็บกติกา join ตามรหัสจังหวัดและเวลาที่ข้อมูลพร้อมใช้งาน"),
    p("ขอบเขต: ข้อมูลรวม ไม่ใช่ข้อมูลรายธนาคารหรือลูกค้า; ผลลัพธ์เป็น screening ไม่ใช่คำแนะนำเปิดสาขาหรืออนุมัติสินเชื่อ"),
    p("แหล่งข้อมูลและ grain", "h"),
    table([
        ["แหล่ง", "วิธีดึง / grain", "แถวที่โหลดและบทบาท"],
        ["ธปท. FI_CB_011_S5", "ตารางเว็บทางการ; จังหวัด-เดือน", "1,925 แถว / สินเชื่อ เงินฝาก สาขา"],
        ["กรมการปกครอง", "TXT ทางการ; จังหวัด-ปี", "231 แถว / ประชากรทะเบียน"],
        ["สศช. GPP 2024p", "XLSX ทางการ; จังหวัด-ปี", "77 แถว / ขนาดเศรษฐกิจ"],
        ["World Bank Indicators", "REST JSON API จริง; ประเทศ-ปี", "65 ปีที่มีค่า / เงินเฟ้อไทย"],
        ["ธปท. MPC", "XLSX ทางการ; วันมติ", "191 มติ / อัตราดอกเบี้ยนโยบาย"],
    ], [39*mm, 61*mm, 72*mm]),
    p("ETL และคลังข้อมูล", "h"),
    p("Python adapters บันทึก raw snapshot พร้อม SHA-256; ตรวจ 77 จังหวัดครบและชื่อที่ map ไม่ได้; โหลด fact ใน transaction. PostgreSQL มีมิติ จังหวัด/เดือน, fact แยก grain และ mart จังหวัด-เดือน. ประชากรใช้ snapshot ธันวาคมที่ทราบแล้ว; GPP และเงินเฟ้อใช้ availability date; ดอกเบี้ยเลือกมติล่าสุดก่อนหรือเท่ากับสิ้นงวด. Airflow รัน 07:00 Asia/Bangkok และมี 6 tasks; DAG ล่าสุดสำเร็จ"),
    PageBreak(),
    p("คำตอบเชิงธุรกิจจากข้อมูลจริง", "h"),
    p("งวดล่าสุด กรกฎาคม 2569 เทียบกรกฎาคม 2568; ยอดธนาคารเป็น stock ณ เดือน ไม่บวกข้ามเดือน"),
    table([
        ["#", "คำถาม", "คำตอบจาก warehouse / ข้อควรระวัง"],
        ["1", "สินเชื่อโตต่อเนื่อง?", "ปทุมธานี YoY เป็นบวก 12 จาก 12 เดือนล่าสุด (เฉลี่ย +1.47%); มุกดาหารโตสูงสุดเดือนล่าสุด +1.61%"],
        ["2", "เงินฝากเทียบสินเชื่อ?", "เงินฝากรวม +3.89% YoY; สินเชื่อรวม -0.17% YoY ต่าง 4.06 จุดเปอร์เซ็นต์"],
        ["3", "เครือข่ายสาขา?", "สาขารวม 4,516 จาก 4,790 แห่ง (-5.72% YoY). สาขาต่อประชากรแสนคนเป็น proxy"],
        ["4", "GPP ใกล้กัน ตลาดต่างกัน?", "ชลบุรี GPP 1.234 ล้านล้านบาท / สินเชื่อ 450,683 ล้านบาท; ระยอง GPP 1.100 ล้านล้านบาท / สินเชื่อ 147,746 ล้านบาท"],
        ["5", "ดอกเบี้ยนโยบาย?", "สิ้น ก.ค. 2568 = 1.75%; สิ้น ก.ค. 2569 = 1.00%. เป็นบริบทเวลา ไม่พิสูจน์ผลเชิงสาเหตุ"],
        ["6", "สาขาลด สินเชื่อเพิ่ม?", "ปทุมธานีสาขา -14 แต่สินเชื่อ +0.73%; พังงาสาขา -2 แต่สินเชื่อ +1.47%"],
        ["7", "คัดพื้นที่ศึกษา?", "เกณฑ์ GPP >=100,000 ลบ., สาขาต่อแสน <=15, สินเชื่อ >=50,000 ลบ., ไม่รวม กทม. ได้ 22 จังหวัด"],
    ], [9*mm, 51*mm, 112*mm]),
    p("ข้อจำกัดสำคัญ", "h"),
    p("ประชากรตามทะเบียนไม่เท่าจำนวนผู้ใช้บริการ; GPP 2024p และยอดธนาคาร 2026 ต่างปี; กรุงเทพฯ อาจสะท้อนการบันทึกที่สำนักงานใหญ่; เงินเฟ้อ/ดอกเบี้ยเป็นบริบทระดับประเทศ. ตัวเลขสรุปจังหวัดอาจต่างจาก Grand Total ธปท. เล็กน้อยเพราะปัดเศษ"),
    PageBreak(),
    p("ผลระบบและหลักฐาน", "h"),
    p("Grafana มี 13 panels ตอบ 7 คำถาม; Streamlit มีแนวโน้ม จังหวัด GPP scatter และเกณฑ์คัดพื้นที่ปรับได้. Chatbot แสดงตาราง กราฟ SQL และ provenance ด้วย QueryPlan ที่จำกัดค่า, SQLGlot ตรวจ SELECT และ PostgreSQL role อ่านอย่างเดียว. ปัจจุบันใช้กฎภาษาไทยที่ติดป้ายว่าไม่ใช่ AI; โหมด LangChain/OpenAI เตรียมไว้แต่ยังไม่ live test เพราะไม่มี API key"),
    p("การตรวจสอบ: 34 automated tests ผ่าน รวม 25 คำถาม rules mode, SQL 13 panels, as-of/no-lookahead, trend window และสิทธิ์ read-only. Airflow manual run ล่าสุด 6 tasks success; ภาพด้านล่างเป็นหน้าจอรันจริง"),
    scaled_image("docs/evidence/airflow-graph-qa.png", max_w=170*mm, max_h=105*mm),
    p("สิ่งที่ต้องทำหลังวันนี้", "h"),
    p("ข้อมูลย้อนหลัง 25 เดือนผ่านเงื่อนไขข้อมูลอย่างน้อยหนึ่งเดือนแล้ว แต่ยังไม่มีหลักฐานว่า scheduler รันต่อเนื่องหนึ่งเดือนจริง. ต้องปล่อย Docker/Airflow ทำงานต่อและเก็บ run history ถึงอย่างน้อย 28 ตุลาคม 2569. เมื่อได้ OpenAI API key ให้ใส่ใน .env บนเครื่องและทดสอบ LLM จริงพร้อมค่าใช้จ่าย/สิทธิ์โมเดล"),
    p("เอกสารและต้นทาง", "h"),
    p("รายละเอียดเต็ม: PROJECT_PLAN.md, README.md, docs/business-report.md, docs/architecture.md และ docs/evidence/run-status.md ในโฟลเดอร์โปรเจกต์. ต้นทาง: bot.or.th, app.bot.or.th, stat.bora.dopa.go.th, nesdc.go.th, api.worldbank.org"),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(border)
    canvas.line(19*mm, 17*mm, 191*mm, 17*mm)
    canvas.setFont("TahomaThai", 7.5)
    canvas.setFillColor(grey)
    canvas.drawString(19*mm, 12*mm, "Thailand Regional Banking Intelligence | 28 Sep 2026")
    canvas.drawRightString(191*mm, 12*mm, f"{doc.page}")
    canvas.restoreState()


SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=19*mm, rightMargin=19*mm,
                  topMargin=18*mm, bottomMargin=21*mm,
                  title="Thailand Regional Banking Intelligence").build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
