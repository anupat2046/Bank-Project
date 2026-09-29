# Verification snapshot — 28 กันยายน 2569 (Asia/Bangkok)

## Data

- BOT fact/mart: 77 จังหวัด × 25 เดือน = 1,925 แถว; งวดล่าสุด ก.ค. 2569
- DOPA: 231 แถว (77 จังหวัด × 3 ปี)
- NESDC: 77 แถว (GPP 2024p)
- World Bank API: 65 ปีที่มีค่า; response metadata `lastupdated=2026-07-13`
- BOT MPC official XLSX: 191 มติ; มติล่าสุดในไฟล์ 26 ส.ค. 2569 (1.00%); mart ก.ค. 2569 ใช้มติ 24 มิ.ย. 2569 (1.00%) เพราะไม่มองล่วงหน้า
- `mart_province_month` ล่าสุด: 77 จังหวัดมี population, GPP และ inflation context ไม่เป็น NULL
- งวด ก.ค. 2569: 4,516 สาขา; สินเชื่อรวม 18,100,244 ล้านบาท; เงินฝากรวมจากยอดจังหวัด 18,136,237 ล้านบาท (ต่างจาก Grand Total ธปท. 4 ล้านบาทเพราะปัดเศษ)

## Pipeline

Airflow metadata ใช้ PostgreSQL ฐาน `airflow`; หลังย้ายสำเร็จมี run ดังนี้:

| run ID (UTC) | สถานะ |
|---|---|
| `scheduled__2026-09-26T00:00:00+00:00` | success |
| `manual__2026-09-27T22:58:53+00:00` | success |
| `manual__2026-09-27T22:59:57+00:00` | success |
| `manual__2026-09-27T23:15:09+00:00` | success (รวม `load_bot_policy_workbook` เป็น task ที่ 5 ก่อน mart) |
| `scheduled__2026-09-27T00:00:00+00:00` | success; เริ่มจริง 28 ก.ย. 2569 เวลา 07:00 Asia/Bangkok และจบ 07:00:34 |

รอบ manual สุดท้ายหลัง mount `./data:/app/data` สำเร็จ และไฟล์ดิบที่ source_manifest อ้างถึงตรวจว่ามีบน host แล้ว ตาราง `etl_run` เก็บผลราย source. นี่เป็นหลักฐานการรันทดสอบ ไม่ใช่หลักฐานว่า Airflow รันต่อเนื่องครบหนึ่งเดือน

## Quality / UI

- `pytest -q`: **34 passed** รวม 25 คำถาม rules mode, SQL ของทั้ง 13 Grafana panels, no-lookahead join, trend window, DB read-only role
- FastAPI `/health`: `months_loaded=25`, `latest_period=2026-07-01`
- Grafana: **13 panels** provisioned และอ่านกลับผ่าน Grafana API; SQL ของทุก panel ทดสอบคืนแถวจริง
- PostgreSQL `bank_reader`: SELECT บน mart ได้, INSERT ไม่ได้
- ตรวจ Streamlit ใน browser: เมนูภาพรวม แผนภูมิ ตาราง, chatbot คำถาม `แนวโน้มเงินฝากย้อนหลัง` ได้ 25 เดือนพร้อมกราฟ, SQL และป้าย rules mode
- ตรวจ Streamlit ใน browser เพิ่ม: GPP scatter และ screening ปรับเกณฑ์ default ได้ 22 จังหวัด; screenshots `gpp-scatter-qa.png`, `screening-qa.png`
- ตรวจ Grafana ใน browser: panels 1–13 render; ภาพใหม่ `grafana-policy-qa.png`, `grafana-new-panels-qa.png`
- ตรวจ Airflow Graph ใน browser: 6 tasks success ใน run ล่าสุด; ภาพ `airflow-graph-qa.png`

เปิดดูสถานะปัจจุบันอีกครั้ง:

```powershell
docker compose ps
docker exec bank-airflow-1 airflow dags list-runs -d bank_regional_daily --no-backfill
Invoke-RestMethod http://127.0.0.1:8000/health
```
