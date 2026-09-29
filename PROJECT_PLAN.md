# Thailand Regional Banking Intelligence

## 1. สรุปโครงการ

โครงการ Data Warehouse และ Dashboard สำหรับวิเคราะห์ตลาดธนาคารพาณิชย์รายจังหวัดในประเทศไทย โดยรวมข้อมูลจริงจากธนาคารแห่งประเทศไทย (ธปท.), กรมการปกครอง และสำนักงานสภาพัฒนาการเศรษฐกิจและสังคมแห่งชาติ (สภาพัฒน์) ผ่าน API และไฟล์เผยแพร่ทางการ

ระบบหลักใช้ Python, PostgreSQL, Apache Airflow และ Grafana ส่วนต่อยอดเป็น Chatbot ภาษาไทยสำหรับถามข้อมูล สร้าง SQL และแสดงตาราง/กราฟด้วย FastAPI, LangChain, LangGraph, Streamlit และ Plotly

- วันที่จัดทำแผน: 28 กันยายน 2569
- กำหนดส่งที่ปรากฏในภาพ Assignment: 12 พฤศจิกายน 2569 — ควรตรวจสอบกำหนดจริงกับผู้สอน
- ขอบเขตหลัก: ข้อมูลระดับจังหวัดและช่วงเวลา เป็นภาพรวมตลาดธนาคารพาณิชย์
- ใช้ข้อมูลจริงที่เผยแพร่ทางการ ไม่สร้างข้อมูลจำลองมาใช้เป็นผลวิเคราะห์
- สถานะ: MVP ลงมือทำและโหลดข้อมูลจริงแล้ว; ดู [README.md](README.md) สำหรับสิ่งที่ทดสอบสำเร็จและสิ่งที่ยังไม่เสร็จ

> สถานะหลังลงมือทำ: API ที่ใช้งานสดโดยไม่ต้องรอคีย์คือ World Bank Indicators JSON API (เงินเฟ้อไทย). อัตราดอกเบี้ยนโยบาย ธปท. **เชื่อมแล้วจาก XLSX ทางการ** 191 มติและทำ as-of join เข้าคลัง; แต่ **BOT Policy Rate API ตามแผนเดิมยังไม่เชื่อม** เพราะไม่มี credentials. โหมด LLM เตรียมไว้แต่ยังไม่ live test; rules mode และ 13 Grafana panels ตรวจแล้ว. ดู [รายงานผลจริง](docs/business-report.md) และ [README](README.md) ซึ่งเป็นสถานะ implementation ล่าสุด

## 2. Business Problem และผู้ใช้งาน

> ทีมกลยุทธ์ของธนาคารต้องการเปรียบเทียบขนาดตลาด การเติบโตของสินเชื่อและเงินฝาก และความหนาแน่นของสาขาในแต่ละจังหวัด เพื่อจัดลำดับพื้นที่ที่ควรเข้าไปศึกษาตลาดเพิ่มเติม

ผู้ใช้เป้าหมาย ได้แก่ทีม Strategy, Regional Business Development, Product และ Channel Planning

ผลลัพธ์เป็นข้อมูลประกอบการศึกษาตลาด เช่น จังหวัดที่เงินฝากเติบโตสูง หรือจังหวัดที่สินเชื่อเพิ่มขึ้นขณะที่จำนวนสาขาลดลง ยังไม่ใช่ข้อสรุปว่าควรเปิดสาขาหรืออนุมัติสินเชื่อทันที

ข้อมูลชุดหลักเป็นยอดรวมของธนาคารพาณิชย์หลายแห่ง จึงไม่แสดง market share ของธนาคารใดธนาคารหนึ่ง ประวัติธุรกรรมลูกค้า DPD หรือ NPL รายจังหวัด

## 3. ขอบเขตและลำดับความสำคัญ

### 3.1 ระบบหลักที่ต้องเสร็จก่อน

1. ตรวจความเป็นไปได้ของแหล่งข้อมูลจริงและ API
2. โหลดข้อมูลย้อนหลังและสร้าง mapping จังหวัด
3. ออกแบบ Star Schema และโหลด Data Warehouse
4. ตั้ง Airflow ให้ตรวจและโหลดข้อมูลอัตโนมัติ
5. สร้าง Grafana ที่ตอบคำถามธุรกิจอย่างน้อย 5 ข้อ
6. เก็บประวัติการทำงานต่อเนื่องอย่างน้อย 1 เดือน และจัดทำรายงาน

### 3.2 ส่วนต่อยอดหลังระบบหลักตรวจสอบแล้ว

1. Chatbot ภาษาไทยสำหรับจัดอันดับ ดูแนวโน้ม และเปรียบเทียบจังหวัด
2. Text-to-SQL ที่มีการตรวจ query ก่อนรัน
3. กราฟแบบโต้ตอบ พร้อม SQL นิยาม KPI และช่วงเวลาของข้อมูล
4. การถามต่อโดยจำจังหวัด ช่วงเวลา และ KPI จากบทสนทนา
5. การบันทึก trace และชุดคำถามทดสอบ

## 4. แหล่งข้อมูลจริงและวิธีเข้าถึง

| ชุดข้อมูล | หน่วยงาน | ข้อมูลที่ใช้ | ช่องทาง | ความถี่ต้นทาง |
|---|---|---|---|---|
| FI_CB_011_S5 | ธปท. | เงินฝาก สินเชื่อ จำนวนสาขา แยกรายจังหวัด | ตรวจ series ใน Statistics API; หากไม่มี series ที่ใช้ได้ครบ ให้ดาวน์โหลดไฟล์ทางการ | รายเดือน |
| ประชากรรายจังหวัด | กรมการปกครอง | จำนวนประชากรตามทะเบียนบ้าน รหัสและชื่อจังหวัด | Text/Excel ทางการ; เลือกชุดรายเดือนถ้าเข้าถึงได้ หรือรายปีพร้อมระบุปีอ้างอิง | ตามชุดที่เลือก |
| Policy Rate | ธปท. | อัตราดอกเบี้ยนโยบายและวันที่มีผล | implementation ใช้ XLSX ทางการ; REST API เป็นทางเลือกเมื่อมี API key | ตามการประกาศอัตรา |
| GPP รายจังหวัด | สภาพัฒน์ | ผลิตภัณฑ์จังหวัด ขนาดเศรษฐกิจ และ GPP ต่อหัว | Excel ทางการ | รายปี |

### 4.1 ธปท.: สินเชื่อ เงินฝาก และสาขา

- ตารางหลัก: [FI_CB_011_S5](https://app.bot.or.th/BTWS_STAT/statistics/BOTWEBSTAT.aspx?language=ENG&reportID=1008)
- นิยามและความถี่: [Metadata FI_CB_011_S5](https://app.bot.or.th/BTWS_STAT/statistics/DownloadFile.aspx?file=FI_CB_011_S5_ENG.PDF)
- [BOT Statistics API](https://portal.api.bot.or.th/portal/catalogue-products/statistics-1)
- [Observations API documentation](https://portal.api.bot.or.th/portal/catalogue-products/statistics-1/e2dcfd41460e49a86276db01aeb3cd1f/docs)

API Statistics ให้เลือก observations ด้วย series code และต้องใช้ API key แต่ยังต้องทดลองว่าตารางจังหวัดและคอลัมน์ที่ต้องการมี series ให้เรียกครบหรือไม่ รหัสตาราง FI_CB_011_S5 ไม่ควรถูกสมมติว่าเป็น series code ของ API

เริ่ม backfill ด้วยช่วงของ FI_CB_011_S5 ที่มีข้อมูลจริงร่วมกับแหล่งอื่นอย่างน้อย 12 เดือน หากมีประวัติครบให้ใช้ประมาณ 24 เดือน เพื่อรองรับ YoY การขยายไปตารางรุ่นเก่าต้องตรวจการเปลี่ยนนิยามก่อนเชื่อมประวัติ

### 4.2 กรมการปกครอง: ประชากร

- [หน้าดาวน์โหลดประชากรและโครงสร้างข้อมูล](https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php/statByAgeMonth.php)
- [ตัวอย่างหน้าข้อมูลประชากรรายเดือน](https://stat.bora.dopa.go.th/new_stat/webPage/statByMooBan.php?month=04&year=68)

เลือกข้อมูลระดับจังหวัดเป็นหลัก ตรวจปี/เดือน encoding ตัวคั่นฟิลด์ รหัสจังหวัด และนิยามประชากรจริงก่อนสร้าง adapter ข้อมูลตามทะเบียนบ้านไม่เท่ากับจำนวนคนที่อาศัยอยู่จริงทั้งหมด โดยเฉพาะจังหวัดที่มีประชากรแฝง

ยังไม่ยืนยันว่ามี public API ที่ใช้งานได้สำหรับชุดประชากรที่เลือก จึงวางแผนช่องทางหลักเป็นไฟล์เผยแพร่ทางการ การดาวน์โหลดไฟล์ด้วย HTTP ต้องเรียกให้ตรงกับชนิดแหล่งข้อมูล ไม่เรียกแทนว่า REST API

### 4.3 ธปท.: ดอกเบี้ยนโยบาย

**ที่ทำจริง:** โหลด [official MPC decision workbook](https://www.bot.or.th/en/our-roles/monetary-policy/mpc-publication/policy-interest-rate.html) 191 มติ โดยไม่ต้องใช้คีย์; เก็บ raw SHA-256, วันที่มติและอัตรา แล้วเลือกมติล่าสุดก่อนสิ้นเดือน. ข้อความ API ด้านล่างเป็นแผนขยายที่ยังไม่ทำ

- [Policy Rate API documentation](https://portal.api.bot.or.th/portal/catalogue-products/interest-rates-1/9dcfd6baf6804c3c65dc8b026cb64e6/docs)
- Base URL ที่เอกสารระบุ: `https://gateway.api.bot.or.th/PolicyRate/v3/policy_rate`
- ตรวจพารามิเตอร์และรูปแบบ response จาก specification ก่อนเขียน request จริง
- API key อยู่ใน environment variable ฝั่ง server

ดอกเบี้ยนโยบายเปลี่ยนตามการประกาศ ไม่ได้มีอัตราใหม่ทุกวัน ให้เก็บวันที่มีผลและคำนวณอัตราที่มีผล ณ วันสิ้นเดือน

### 4.4 สภาพัฒน์: GPP

- [Table of Gross Regional and Provincial Product 2024](https://www.nesdc.go.th/en/download/table-of-gross-regional-and-provincial-product-2024-excel/)

ใช้เป็นบริบทเปรียบเทียบขนาดเศรษฐกิจจังหวัด ตรวจ sheet หน่วยราคาและปีอ้างอิงก่อนโหลด ค่า GPP ต่อหัวจากต้นทางอาจใช้ฐานประชากรต่างจากกรมการปกครอง จึงเก็บค่าที่ต้นทางเผยแพร่พร้อมนิยาม และไม่แทน denominator เองโดยไม่อธิบาย

### 4.5 เกณฑ์ผ่านการทดลองแหล่งข้อมูล

- ได้ credentials และเรียก Policy Rate API สำเร็จ
- ยืนยันช่องทางดึงข้อมูลจังหวัด ธปท. ว่าเป็น API หรือไฟล์
- อ่านไฟล์ประชากรและ GPP ได้จริง
- มีช่วงเวลาที่ใช้วิเคราะห์ร่วมกันและข้อมูลย้อนหลังพอสำหรับ KPI
- สร้างรายการจังหวัดที่ map ได้ครบ หรือระบุจังหวัด/งวดที่ขาดอย่างชัดเจน
- บันทึก URL, retrieval time, รูปแบบข้อมูล, หน่วย, ความถี่ และข้อกำหนดการใช้ข้อมูล

ถ้าผู้สอนกำหนดว่าทุกแหล่งต้องเป็น API ต้องทบทวนชุดข้อมูลก่อนล็อกหัวข้อ แผนนี้มี API ร่วมกับไฟล์ทางการหลายหน่วยงาน ไม่ได้ยืนยันว่าทั้งสี่ชุดเป็น API

## 5. คำถามเชิงวิเคราะห์

| ข้อ | คำถาม | ข้อมูลที่ต้องใช้ | การแสดงผล |
|---|---|---|---|
| 1 | จังหวัดใดมีสินเชื่อเติบโต YoY สูง และต่อเนื่องกี่เดือน? | สินเชื่อรายจังหวัด | อันดับและ line chart |
| 2 | จังหวัดใดเงินฝากโตเร็วกว่าสินเชื่อ? | เงินฝากและสินเชื่อ | กราฟเปรียบเทียบ growth |
| 3 | จำนวนสาขาต่อประชากรตามทะเบียนต่างกันอย่างไร? | สาขาและประชากร | ตาราง/แผนที่ |
| 4 | จังหวัดที่ GPP ใกล้กันมีขนาดตลาดธนาคารต่างกันหรือไม่? | GPP เงินฝาก สินเชื่อ | Scatter และกลุ่มจังหวัด |
| 5 | ในช่วงที่ดอกเบี้ยนโยบายเปลี่ยน สินเชื่อและเงินฝากเคลื่อนไหวอย่างไร? | ดอกเบี้ยและข้อมูลธนาคาร | แนวโน้มพร้อมเหตุการณ์ประกาศ |
| 6 | จังหวัดใดสินเชื่อเพิ่มแต่จำนวนสาขาลด? | สินเชื่อและสาขา | ตารางคัดกรอง |
| 7 | จังหวัดใดเข้าเกณฑ์ศึกษาตลาดเพิ่มเติมที่ผู้ใช้กำหนด? | KPI ใน mart | ตารางปรับตัวกรองได้ |

ใช้คำว่า “ความเคลื่อนไหวร่วมกัน” สำหรับดอกเบี้ยกับการเติบโต ไม่สรุปเหตุและผลจากกราฟหรือ correlation เพียงอย่างเดียว

## 6. กติกา Mapping และ Join

### 6.1 จังหวัด

สร้าง `dim_province` และ `map_province_alias` ใช้รหัสจังหวัดเป็นคีย์กลาง เก็บรหัสเป็นข้อความเพื่อรักษารูปแบบ ไม่ join ด้วยชื่อที่ผู้ใช้พิมพ์โดยตรง

| ตัวอย่างชื่อจากแหล่งข้อมูล | ชื่อกลาง |
|---|---|
| Chiengmai / Chiang Mai / เชียงใหม่ | เชียงใหม่ |
| Ayuthaya / พระนครศรีอยุธยา | พระนครศรีอยุธยา |
| Bangkok / กรุงเทพมหานคร | กรุงเทพมหานคร |

ขั้นตอน: normalize ช่องว่างและข้อความ → exact alias mapping → ตรวจรหัส → ส่งชื่อที่ไม่รู้จักเข้า quarantine เพื่อแก้ mapping หลีกเลี่ยง fuzzy match อัตโนมัติที่อาจเชื่อมผิดจังหวัด

แยก `geography_level` ของแถวจังหวัด ภาค ประเทศ และรายการย่อยกรุงเทพฯ เลือกจังหวัดหนึ่งแถวต่อเดือนสำหรับ province mart อย่ารวมยอดจังหวัดกับยอดภาคหรือยอดประเทศซ้ำ

### 6.2 ช่วงเวลา

- แปลง พ.ศ. เป็น ค.ศ. โดยตรวจรูปแบบต้นทางก่อน ไม่ลบ 543 จากปีทุกชนิด
- เก็บเดือนหลักเป็นวันที่แรกของเดือน เช่น `2026-07-01`
- ประชากรรายเดือน: join จังหวัดและเดือนเดียวกันก่อน
- หากงวดประชากรไม่ตรง: ใช้ค่าล่าสุดก่อนหรือเท่ากับงวดธนาคารตามกติกาที่กำหนด พร้อม `population_reference_period` และสถานะความล่าช้า
- ประชากรรายปี: แสดงปีอ้างอิงทุกครั้ง ไม่อ้างว่าเป็นประชากรรายเดือน
- ดอกเบี้ย: เลือกวันที่มีผลล่าสุดที่ไม่เกินสิ้นเดือน
- GPP: เก็บ `gpp_reference_year` และวันที่เผยแพร่ ใช้ค่าที่เผยแพร่ล่าสุดตามมุมมองรายงาน
- MVP เป็นการวิเคราะห์ย้อนหลังด้วยข้อมูลที่ปรับปรุงล่าสุด หากต่อยอดพยากรณ์ ต้องใช้เฉพาะข้อมูลที่ทราบจริงในวันนั้นเพื่อป้องกัน look-ahead bias

### 6.3 หน่วยและการรวมข้อมูล

- เก็บหน่วยล้านบาทของต้นทางไว้อย่างชัดเจน; หากคำนวณบาทต่อคนต้องคูณ 1,000,000
- จำนวนสาขาเป็นจำนวน ไม่ใช่มูลค่าเงิน
- ไม่แทนข้อมูลไม่เปิดเผยหรือ `n.a.` ด้วยศูนย์
- อัตราส่วนรวมต้องคำนวณจากผลรวม numerator/denominator ไม่เฉลี่ยเปอร์เซ็นต์จังหวัดโดยตรง
- ยอดเงินฝาก สินเชื่อ และจำนวนสาขา ณ สิ้นงวดไม่บวกข้ามเดือนเพื่อเรียกว่า “ยอดทั้งปี”
- ตรวจผลรวมจังหวัดกับยอดประเทศเมื่อขอบเขตตรงกัน และบันทึกข้อแตกต่างจาก suppression/rounding/นิยาม

## 7. Data Warehouse และ Star Schema

### 7.1 ชั้นข้อมูล

```text
BOT API / Official downloads / DOPA / NESDC
                    ↓
Raw snapshots + source metadata
                    ↓
Staging: types, dates, units, aliases
                    ↓
Warehouse facts + conformed dimensions
                    ↓
mart_province_month + KPI views
             ↙              ↘
          Grafana        Chatbot API
```

### 7.2 ตารางหลักและ Grain

| ตาราง | Grain | คีย์/ข้อมูลสำคัญ |
|---|---|---|
| `dim_province` | หนึ่งจังหวัด | surrogate key, province code, ชื่อไทย/อังกฤษ, ภาค |
| `dim_month` | หนึ่งเดือน | month key, ปี, ไตรมาส, วันสิ้นเดือน |
| `dim_date` | หนึ่งวัน | date key สำหรับวันที่มีผลของดอกเบี้ย |
| `dim_source` | หนึ่งชุดข้อมูลต้นทาง | หน่วยงาน URL หน่วย ความถี่ นิยาม |
| `map_province_alias` | หนึ่ง alias ต่อแหล่ง | source, raw name/code, province key |
| `fact_bank_province_month` | จังหวัด × เดือน × ขอบเขตการรายงาน | deposits, credits, branch count, source version |
| `fact_population_province_period` | จังหวัด × งวด × นิยามประชากร | population count, frequency, reference period |
| `fact_policy_rate_event` | วันที่มีผล × series | policy rate |
| `fact_gpp_province_year` | จังหวัด × ปี × นิยามราคา | GPP, source GPP per capita, reference year |
| `mart_province_month` | จังหวัด × เดือน | banking metrics และ reference fields ของข้อมูลประกอบ |
| `etl_run_log` | หนึ่ง task/run | counts, status, duration, error, timestamps |
| `data_quality_result` | หนึ่ง check/run | rule, expected, actual, severity, status |

เริ่มจาก fact ธนาคารแบบ wide เพื่อให้ query เข้าใจง่าย แยก fact ประชากร GPP และดอกเบี้ยตาม grain ของต้นทาง แล้วค่อยสร้าง mart ที่ join แล้ว หลีกเลี่ยง join facts หลายแถวต่อคีย์ซึ่งทำให้ยอดถูกคูณ

คอลัมน์ metadata ที่ควรมี: `source_id`, `source_version`, `ingested_at`, `source_published_at` เมื่อทราบจริง, `is_preliminary`, `record_hash` และ `quality_status`

## 8. KPI Definitions

| KPI | สูตร | เงื่อนไข |
|---|---|---|
| Credit growth YoY | `(credit_t / credit_t_minus_12 - 1) × 100` | มีสองงวดและฐานไม่เป็นศูนย์ |
| Deposit growth YoY | `(deposit_t / deposit_t_minus_12 - 1) × 100` | มีสองงวดและฐานไม่เป็นศูนย์ |
| Credit-to-deposit ratio | `credits / deposits × 100` | denominator > 0 |
| Branches per 100,000 registered residents | `branches / population × 100000` | ระบุนิยามและงวดประชากร |
| Credits per registered resident | `credits_million × 1000000 / population` | เป็น proxy ขนาดตลาด ไม่ใช่หนี้เฉลี่ยรายบุคคล |
| Deposits per registered resident | `deposits_million × 1000000 / population` | ไม่ตีความเป็นเงินออมเฉลี่ยของลูกค้าหนึ่งคน |
| Growth difference | `credit_growth_yoy - deposit_growth_yoy` | หน่วย percentage points |
| Branch change YoY | `branches_t - branches_t_minus_12` | เปรียบเทียบงวดเดียวกัน |
| Month-end policy rate | อัตราล่าสุดที่มีผลก่อน/เท่ากับสิ้นเดือน | เก็บ effective date |

เก็บคำอธิบาย KPI และสูตรกลางไว้ใน semantic catalog เพื่อให้ SQL, Grafana และ Chatbot ใช้สูตรเดียวกัน

## 9. ETL และ Airflow

### 9.1 Backfill

1. ทดลอง source adapter ทีละแหล่ง
2. โหลดช่วงที่มีข้อมูลจริงร่วมกันอย่างน้อย 12 เดือน; ถ้าจะดู YoY หลายเดือนให้มีประวัติมากกว่า 12 เดือน
3. บันทึกข้อมูลดิบและ checksum
4. normalize และตรวจ mapping
5. โหลด dimension/fact และสร้าง mart
6. เทียบตัวเลขบางจังหวัดกับหน้าเว็บ/ไฟล์ต้นทาง

### 9.2 DAG รายวัน

```text
extract_bot_bank_stats ─┐
extract_population ────┤
extract_policy_rate ───┼→ validate_raw → normalize → load_dw
extract_gpp ───────────┘                         ↓
                                      build_mart → quality_checks
                                                   ↓
                                              write_run_log
```

การรันทุกวันเป็นการตรวจข้อมูลใหม่หรือ revision ไม่ได้ทำให้ชุดรายเดือนกลายเป็นข้อมูลรายวัน ถ้าไฟล์/API ไม่เปลี่ยน ให้ log ว่า `no_change` โดยไม่เพิ่ม observation ซ้ำ

- ดึงช่วงล่าสุดซ้ำตาม revision policy ที่พบจริง เช่น งวดล่าสุดและเดือนก่อนหน้า
- ใช้ upsert ด้วย natural key และเก็บเวอร์ชัน raw
- HTTP timeout, retry พร้อม backoff และเคารพ quota
- fail เมื่อ schema เปลี่ยนสำคัญหรือจังหวัด map ไม่ได้
- ถ้าแหล่งประกอบยังไม่ออกงวดใหม่ ให้แสดง reference period และ freshness status
- Grafana อ่าน mart ล่าสุดโดยตรง ไม่จำเป็นต้องสร้าง task “refresh Grafana” หากไม่ได้ใช้ cache/materialization เพิ่มเติม

### 9.3 Data-quality checks

- จำนวนจังหวัดและ uniqueness ตามขอบเขตของแต่ละงวด
- ไม่มี duplicate natural key
- ไม่มีแถวภาค/ประเทศปะปนใน province mart
- จำนวนสาขาและประชากรไม่ติดลบ
- ค่าที่หายหรือไม่เปิดเผยไม่กลายเป็นศูนย์
- การ join ไม่เพิ่มจำนวนแถวจากหนึ่งจังหวัดต่อเดือน
- ไม่ใช้วันที่มีผลของดอกเบี้ยในอนาคต
- YoY เป็น null เมื่อประวัติไม่ครบ
- สูตรอัตราส่วนตรงกับตัวเลขต้นทางภายใน tolerance ที่อธิบายได้
- บันทึก freshness, source failures และ revisions ที่ตรวจพบ

### 9.4 หลักฐานสะสมข้อมูลอย่างน้อย 1 เดือน

เริ่มรันตั้งแต่ 1 ตุลาคมถึงอย่างน้อย 1 พฤศจิกายน 2569 เก็บ DAG run history, source checks, raw versions และจำนวน record ใหม่/แก้ไข

รายงานแยก “ระยะเวลาที่ pipeline ทำงาน”, “ช่วงเวลาของข้อมูลย้อนหลัง” และ “จำนวนงวดใหม่ที่ต้นทางเผยแพร่” การโหลดไฟล์เดิม 30 ครั้งไม่ใช่ 30 งวดข้อมูลใหม่ และ backfill ไม่แทนประวัติการรันจริง

## 10. Grafana Dashboard

### หน้า 1: Executive Overview

- สินเชื่อ เงินฝาก จำนวนสาขา และ Credit-to-deposit ratio ณ งวดที่เลือก
- แนวโน้มรายเดือนและ YoY
- แสดงเดือนข้อมูลและเวลาที่ ETL ตรวจล่าสุดแยกกัน
- ตัวกรองจังหวัด ภาค และช่วงเวลา

### หน้า 2: Province Comparison

- ตารางอันดับ growth และสาขาต่อประชากร
- กราฟเปรียบเทียบสินเชื่อกับเงินฝาก
- Scatter: GPP กับขนาดตลาดธนาคาร พร้อมปี GPP
- แผนที่จังหวัดเป็นส่วนเสริม หากมี boundary file ที่ใช้ได้และ license ชัดเจน

### หน้า 3: Opportunity Screening

- ผู้ใช้เลือกเกณฑ์ เช่น growth สูงกว่าค่ากลาง สาขาต่อประชากรต่ำกว่าค่ากลาง
- แสดงรายชื่อจังหวัดและค่าที่ทำให้ผ่านเกณฑ์
- เจาะดูประวัติจังหวัด และลิงก์ไปหน้า Chatbot
- กฎคัดกรองเป็นสมมติฐานสำหรับศึกษาต่อ ไม่ใช่ credit score หรือโมเดลคาดการณ์ความเสี่ยง

## 11. Chatbot: Ask Your Banking Data

### 11.1 ความสามารถ

- ถามภาษาไทย: อันดับจังหวัด แนวโน้ม เปรียบเทียบ และคัดกรอง
- ตอบจากผล query จริง พร้อมกราฟและตาราง
- แสดง SQL สูตร KPI หน่วย และงวดข้อมูล
- ถามกลับเมื่อจังหวัด ช่วงเวลา หรือ metric กำกวม
- อธิบายเมื่อข้อมูลไม่มี เช่น NPL รายจังหวัด
- ถามต่อได้ เช่น “แล้วเปลี่ยนเป็นเงินฝากล่ะ” โดยรักษาจังหวัดและช่วงเวลาเดิม

### 11.2 Tech Stack

| ส่วน | เครื่องมือ | หน้าที่ |
|---|---|---|
| UI | Streamlit | Chat input, history, tables, SQL expander |
| Charts | Plotly | line, bar, scatter, chart interactions |
| Backend | Python + FastAPI | API และควบคุม application logic |
| Model integration | LangChain components + provider adapter | prompts, structured output, model calls |
| Workflow | LangGraph `StateGraph` | nodes, state, conditional routing, bounded retries |
| Output validation | Pydantic | query plan, chart spec, API contracts |
| SQL inspection | SQLGlot | ตรวจ AST และ dialect PostgreSQL |
| Database access | SQLAlchemy + psycopg | parameter binding และ query execution |
| Data | PostgreSQL mart views | ชุดข้อมูลที่อนุญาตให้อ่าน |
| Conversation persistence | LangGraph PostgreSQL checkpointer | จำ state ตาม session/thread |
| Observability | app logs; LangSmith optional | trace, latency, errors, evaluations |

โมเดลภาษาแยกเป็น configuration ไม่ผูกกับ graph ทั้งหมด ค่าเริ่มต้น implementation คือ `gpt-4.1-mini` ซึ่งเอกสาร OpenAI ระบุว่ารองรับ Structured Outputs; ยังไม่ได้ live test เพราะไม่มี API key ของผู้ใช้ เปรียบเทียบรุ่นอื่นเมื่อได้คีย์และมี evaluation จริง โดยตรวจ availability และราคาอีกครั้งก่อนใช้งาน

### 11.3 บทบาท LangChain, LangGraph และ Airflow

- LangChain: ส่วนเชื่อมโมเดล prompt และ tools
- LangGraph: ลำดับการตอบคำถามในหนึ่ง request และ state ของบทสนทนา
- Airflow: ตารางเวลาและการโหลดข้อมูลจากภายนอกเข้า DW
- LangSmith: ระบบ tracing/evaluation ที่เลือกเพิ่มได้ ไม่ใช่ข้อบังคับสำหรับรัน local

LangGraph ไม่จำเป็นต้องมีหลาย agent ใช้ workflow เดียวที่มี node ชัดเจนได้ และ node ไม่ได้แปลว่าต้องเรียก LLM ทุกขั้น

### 11.4 Graph ที่เสนอ

```text
resolve_question
       ↓
check_supported_metrics
   ├─ ข้อมูลไม่มี → explain_unavailable → END
   ├─ กำกวม → request_clarification → รอคำตอบ
   └─ ตอบได้ → build_query_plan
                    ↓
                compile_sql
                    ↓
                validate_sql
                    ↓
                execute_query
                    ↓
                build_chart_spec
                    ↓
                compose_answer → END
```

State เก็บคำถามล่าสุด, จังหวัดที่ resolve แล้ว, metric, ช่วงเวลา, query plan, SQL, validation result, result reference, chart spec, source metadata และจำนวน retry ใช้ session/thread ID แยกแต่ละผู้ใช้

### 11.5 แนวทาง Text-to-SQL

MVP ใช้ LLM แปลงคำถามเป็น query plan แบบจำกัดค่า แล้ว Python สร้าง SQL จาก KPI catalog

```json
{
  "metric": "deposit_growth_yoy",
  "group_by": "province",
  "period": "latest_available",
  "sort": "descending",
  "limit": 5,
  "chart": "bar"
}
```

นี่เป็นการแปลงข้อความเป็น SQL ผ่าน structured plan ไม่ใช่เปิดให้สร้าง SQL อิสระทุกแบบ ข้อดีคือคุมสูตรและความหมายได้ชัด ส่วนต่อยอดสามารถให้โมเดลสร้าง SQL บน schema ที่อนุญาต พร้อมตรวจและแก้ข้อผิดพลาดได้ไม่เกิน 1–2 รอบ

อย่านำ SQL agent tutorial มาใช้กับฐานทั้งหมดโดยไม่ปรับสิทธิ์และกติกาธุรกิจ

### 11.6 กติกา SQL execution

- อนุญาตเฉพาะ mart/views และคอลัมน์ที่ประกาศไว้
- ใช้ database role สำหรับ Chatbot ที่อ่านอย่างเดียวและไม่เป็น owner ของตาราง
- ตรวจหนึ่ง statement, AST, tables, columns และ functions ที่อนุญาต ไม่ตรวจเพียงว่าขึ้นต้นด้วย SELECT
- ตรวจ CTE/subquery เพื่อไม่ให้ซ่อนคำสั่งแก้ไขข้อมูล
- ไม่รันโค้ด Python หรือโค้ดกราฟที่โมเดลสร้าง
- ใช้ parameter binding สำหรับค่าตัวกรอง และ whitelist สำหรับชื่อคอลัมน์/การ sort
- ตั้ง timeout และ row limit ฝั่งแอป/ฐาน; LIMIT อย่างเดียวไม่ได้จำกัดต้นทุนการ scan
- จำกัด retry และจบด้วยข้อความที่ตรวจสอบได้เมื่อแก้ไม่สำเร็จ

### 11.7 กราฟและคำตอบ

เลือกชนิดกราฟจากโครงสร้างผลลัพธ์และ chart spec ที่ validate แล้ว:

- เวลา + ตัวเลข → line chart
- จังหวัด + ตัวเลข → bar chart
- ตัวเลขสองแกน → scatter
- ผลลัพธ์หลายคอลัมน์หรือรายละเอียด → table

คำตอบประกอบด้วยข้อความสรุป กราฟ ตาราง SQL และ provenance ให้ backend คำนวณตัวเลขสรุปก่อนส่งให้ LLM เขียนคำอธิบาย เพื่อไม่ให้โมเดลคำนวณเปอร์เซ็นต์เองจากข้อความ

### 11.8 API endpoints ที่เสนอ

- `POST /chat/query`: question + session ID → answer, SQL, rows, chart spec, reference periods, status
- `GET /metrics`: นิยาม KPI และรูปแบบคำถามที่รองรับ
- `GET /data-status`: ช่วงข้อมูลล่าสุดของแต่ละ source
- `GET /health`: สถานะบริการ

ไม่เปิด endpoint สำหรับรัน SQL อิสระให้ browser ส่งโดยตรง

### 11.9 RAG และ vector database

MVP มี schema และ KPI ไม่มาก จึงใช้ catalog/config เป็น context ได้โดยตรง หากภายหลังเพิ่มเอกสารนิยามจำนวนมาก ค่อยเพิ่ม RAG เพื่อค้นนิยามและแหล่งข้อมูล ตัวเลขวิเคราะห์ยังต้องมาจาก SQL query

## 12. การทดสอบและเกณฑ์รับงาน

### ระบบข้อมูล

- รัน ETL ซ้ำงวดเดิมแล้วไม่เพิ่มแถวซ้ำ
- ประวัติ revision ทำให้เห็นก่อน/หลังและที่มาของการเปลี่ยนแปลง
- mapping ไม่คูณแถวและแยก summary rows ถูกต้อง
- สูตร KPI ถูกทดสอบกับกรณีฐานศูนย์ ประวัติไม่ครบ และค่า missing
- ตัวเลขตัวอย่างบน Grafana เทียบกับต้นทางได้

### Chatbot

เตรียมคำถาม 20–30 ข้อพร้อม expected filters, period, SQL หรือผลตัวเลข รวมคำถามไทยหลายสำนวน คำถามต่อ ข้อมูลไม่มี และคำถามกำกวม

- วัดความถูกต้องของผล query ไม่วัดเพียงว่า SQL รันสำเร็จ
- เป้าหมายเริ่มต้น: คำถามที่รองรับอย่างน้อย 90% ให้ผลและช่วงเวลาถูกต้อง
- ทุก query ที่ถูกปฏิเสธต้องไม่ถูก execute
- ทดสอบคำถามขอแก้ตาราง ขออ่าน schema นอก whitelist และ functions ที่ไม่ได้อนุญาต
- บันทึก latency, จำนวน model calls และ token usage เพื่อประเมินต้นทุนจริง
- นิยาม “เดือนล่าสุด” เป็นเดือนที่มีข้อมูลจริงในฐาน

## 13. แผนเวลา

| ช่วงเวลา | งาน | หลักฐาน/ผลลัพธ์ |
|---|---|---|
| 28–30 ก.ย. | ทดลอง API, credentials, ไฟล์และ field definitions | Source feasibility checklist |
| 1–7 ต.ค. | เริ่ม ingestion จริง, mapping, schema, backfill | Raw snapshots, diagram, run logs |
| 8–14 ต.ค. | DW, mart, quality checks, DAG | Pipeline รันซ้ำได้ |
| 15–21 ต.ค. | Grafana และตรวจตัวเลข/สูตร | Dashboard ตอบ 5 ข้อ |
| 22–28 ต.ค. | เมื่อระบบหลักผ่าน เริ่ม Chatbot MVP | ถามอันดับ แนวโน้ม เปรียบเทียบ |
| 29 ต.ค.–1 พ.ย. | ตรวจประวัติสะสมข้อมูลครบเดือน, chatbot eval | Run history, evaluation report |
| 2–11 พ.ย. | แก้ข้อผิดพลาด สรุป insight รายงานและเดโม | Deliverables พร้อมส่ง |

งานต่อยอด Chatbot ลดขอบเขตได้หากระบบหลักยังไม่ผ่าน โดยรักษารายงาน DW, Airflow และ Grafana ให้ครบก่อน ไม่มีการตั้ง automation หรือเริ่มรัน 30 วันจากการเขียนแผนนี้

## 14. โครงสร้าง Repository ที่เสนอ

```text
regional-banking-intelligence/
  README.md
  docker-compose.yml
  .env.example
  docs/
    business_questions.md
    data_dictionary.md
    kpi_definitions.md
    source_catalog.md
    architecture.md
  config/
    sources.yaml
    province_aliases.csv
    metrics.yaml
  etl/
    sources/
    transforms/
    loaders/
    quality/
  airflow/dags/
  sql/
    dimensions/
    facts/
    marts/
  grafana/
    provisioning/
    dashboards/
  chatbot/
    api/
    graph/
    schemas/
    sql_guard/
    charts/
    ui/
  tests/
    data_quality/
    chatbot_evals/
  data/raw/             # ไม่ commit ไฟล์ขนาดใหญ่หรือ credentials
  outputs/              # รายงาน ภาพ และ evaluation results
```

Chatbot checkpoints ใช้ schema/สิทธิ์แยกจาก analytics เพื่อให้บริการบันทึกบทสนทนาได้โดยไม่เปิดสิทธิ์เขียนตารางวิเคราะห์

## 15. Deliverables

1. Business Problem, เป้าหมาย และคำถามอย่างน้อย 5 ข้อ
2. Source catalog พร้อม URL ช่องทางเข้าถึง ความถี่ หน่วย และช่วงเวลา
3. ER Diagram/Star Schema และ grain ของทุกตาราง
4. ETL code, Airflow DAG และคำอธิบายการแปลง/map/join
5. Screenshot DAG, สถานะและประวัติการรันจริงครบเดือน
6. Screenshot Grafana และ insight ที่อ้างอิงข้อมูลจริง
7. README วิธีรันและตัวอย่าง environment variables
8. ข้อจำกัดและบทเรียนจากโครงการ
9. ส่วนเสริม: Chatbot demo, graph diagram, SQL/provenance และ evaluation report
10. รายงานหรือสไลด์ PDF ตามรูปแบบที่ผู้สอนกำหนด

## 16. ข้อจำกัดที่ต้องอธิบายในรายงาน

- ข้อมูลจังหวัด ธปท. สะท้อนการรายงานของสถาบันการเงิน การบันทึกที่สำนักงานใหญ่ทำให้กรุงเทพฯ ต่างจากจังหวัดอื่น ควรมีมุมเปรียบเทียบที่แยกกรุงเทพฯ และไม่ตีความทั้งหมดเป็นที่อยู่ผู้กู้
- ประชากรเป็นตามทะเบียน ไม่ใช่ลูกค้าธนาคารทั้งหมดหรือประชากรที่อยู่จริง
- จำนวนสาขาเป็นภาพรวมตลาด ไม่ใช่จำนวนสาขาของธนาคารที่ผู้ใช้สังกัด
- สินเชื่อ/เงินฝากต่อประชากรเป็น proxy ไม่ใช่ยอดเฉลี่ยของบุคคล
- ความถี่และเวลาที่ข้อมูลเผยแพร่ต่างกัน ต้องแสดง reference periods
- GPP มีทั้งราคาและฐานประชากรที่ต้องอ่านนิยามก่อนใช้
- การเปลี่ยนรุ่นตาราง/วิธีรายงานอาจทำให้ series ไม่ต่อเนื่อง
- จำนวนสาขาน้อยไม่ได้พิสูจน์ว่าพื้นที่ขาดบริการ เพราะมี mobile banking, ATM และช่องทางอื่น
- โครงการยังไม่มีข้อมูลต้นทุนสาขา market share รายธนาคาร หรือพฤติกรรมลูกค้า จึงไม่สรุป ROI หรือการตัดสินใจอนุมัติสินเชื่อ

## 17. เอกสารอ้างอิงด้านเทคนิค

- [Grafana PostgreSQL configuration](https://grafana.com/docs/grafana-cloud/observe-and-act/connect-externally-hosted/data-sources/postgres/configure/)
- [Streamlit chat elements](https://docs.streamlit.io/develop/api-reference/chat)
- [Streamlit Plotly chart](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
- [FastAPI request models](https://fastapi.tiangolo.com/tutorial/body/)
- [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html)
- [SQLGlot](https://sqlglot.com/)
- [LangChain SQL agent](https://docs.langchain.com/oss/python/langchain/sql-agent)
- [LangGraph custom SQL agent](https://docs.langchain.com/oss/python/langgraph/sql-agent)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI model catalog](https://developers.openai.com/api/docs/models)

เอกสารอ้างอิงมาจากการค้นคว้าในบทสนทนาก่อนหน้า ตรวจ specification, series codes, versions, terms และ availability อีกครั้งในช่วงทดลองแหล่งข้อมูลก่อนล็อก implementation
