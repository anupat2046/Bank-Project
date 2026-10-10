# Competency questions: executed SQL and recorded results

Recorded on 2026-10-10 (Asia/Bangkok) from the existing warehouse; no source refresh was performed

Snapshot: **77 provinces × 25 months = 1,925 rows**; periods 2024-07-01–2026-07-01

All questions read `mart_province_month`, integrating dim_province/dim_month and fact_bank_month, fact_population_year, fact_gpp_year, fact_macro_year, fact_policy_event under the grain/availability rules in [data model](architecture.md). Queries use PostgreSQL role `bank_reader` in a read-only transaction. Thai question wording matches the application.

[All ten SQL queries](../sql/competency_questions.sql) · [Machine-readable results](evidence/competency-results.json)

| ID | Competency question | Sources | Application view | Returned rows |
|---|---|---|---|---|
| CQ01 | จังหวัดใดมีสินเชื่อเติบโต YoY ต่อเนื่องใน 12 เดือนล่าสุด? | BOT | Business questions; Grafana panel 13 | 10 |
| CQ02 | จังหวัดใดเงินฝากโตเร็วกว่าสินเชื่อ YoY มากที่สุด? | BOT | Business questions; Grafana panel 8 | 10 |
| CQ03 | จังหวัดใดมีความหนาแน่นสาขาต่อประชากรแสนคนสูงที่สุด? | BOT + DOPA | Business questions; Grafana panel 3 / เปรียบเทียบจังหวัด | 10 |
| CQ04 | จังหวัดที่ GPP ต่างกันไม่เกิน 15% มีขนาดสินเชื่อต่างกันเท่าไร? | BOT + NESDC | Business questions; GPP เทียบตลาด / หน้า 10 คำถามธุรกิจ | 10 |
| CQ05 | สินเชื่อและเงินฝากรวมเคลื่อนไหวอย่างไรในช่วงที่ดอกเบี้ยนโยบายเปลี่ยน? | BOT + BOT MPC workbook | Business questions; ภาพรวมตลาด / Grafana panels 1,10 | 25 |
| CQ06 | จังหวัดใดจำนวนสาขาลดลงแต่สินเชื่อเพิ่มขึ้นเมื่อเทียบปีก่อน? | BOT | Business questions; Grafana panel 9 | 6 |
| CQ07 | จังหวัดใดผ่านเกณฑ์ GPP ≥100,000 ลบ., สาขาต่อแสน ≤15 และสินเชื่อ ≥50,000 ลบ.? | BOT + DOPA + NESDC | Business questions; คัดพื้นที่ศึกษา / Grafana panel 12 | 22 |
| CQ08 | จังหวัดใดมีอัตราสินเชื่อต่อเงินฝากสูงที่สุด? | BOT | Business questions; จัดอันดับ / Grafana panel 4 | 10 |
| CQ09 | จังหวัดใดมีเงินฝากต่อผู้มีชื่อในทะเบียนสูงที่สุด? | BOT + DOPA | Business questions; จัดอันดับ / Grafana panel 5 | 10 |
| CQ10 | สินเชื่อรวมกระจุกตัวในกรุงเทพฯ และ 5 จังหวัดอันดับแรกเท่าไร? | BOT | Business questions; หน้า 10 คำถามธุรกิจ | 1 |

## CQ01 — จังหวัดใดมีสินเชื่อเติบโต YoY ต่อเนื่องใน 12 เดือนล่าสุด?

**Fields:** province_code, period, credits_million_baht

**Interpretation:** เปรียบเทียบเดือนเดียวกันปีก่อน และต้องมีคู่ข้อมูลครบ 12 งวด

```sql
WITH yoy AS (
  SELECT n.province_code, n.name_th, n.period,
    100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0) AS yoy_pct
  FROM mart_province_month n JOIN mart_province_month p
    ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
  WHERE n.period >= (SELECT MAX(period)-INTERVAL '11 months' FROM mart_province_month)
)
SELECT name_th, COUNT(*) FILTER (WHERE yoy_pct>0) AS positive_months,
  COUNT(*) AS observed_months, ROUND(AVG(yoy_pct)::numeric,2) AS average_yoy_pct
FROM yoy GROUP BY province_code,name_th HAVING COUNT(*)=12
ORDER BY positive_months DESC, average_yoy_pct DESC, name_th LIMIT 10;
```

| name_th | positive_months | observed_months | average_yoy_pct |
| --- | --- | --- | --- |
| ปทุมธานี | 12 | 12 | 1.47 |
| อุทัยธานี | 10 | 12 | 1.82 |
| กรุงเทพมหานคร | 8 | 12 | 0.32 |
| สมุทรสงคราม | 8 | 12 | -1.12 |
| พังงา | 8 | 12 | -1.14 |
| สุโขทัย | 7 | 12 | -0.40 |
| สิงห์บุรี | 6 | 12 | 0.57 |
| นครนายก | 4 | 12 | -1.07 |
| อุตรดิตถ์ | 4 | 12 | -1.31 |
| ยโสธร | 3 | 12 | -0.77 |

## CQ02 — จังหวัดใดเงินฝากโตเร็วกว่าสินเชื่อ YoY มากที่สุด?

**Fields:** province_code, period, deposits_million_baht, credits_million_baht

**Interpretation:** ผลต่างอัตราเติบโตเป็นจุดเปอร์เซ็นต์ ไม่ใช่เปอร์เซ็นต์ของเปอร์เซ็นต์

```sql
SELECT n.name_th,
  ROUND((100.0*(n.deposits_million_baht-p.deposits_million_baht)/NULLIF(p.deposits_million_baht,0))::numeric,2) AS deposit_yoy_pct,
  ROUND((100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS credit_yoy_pct,
  ROUND((100.0*(n.deposits_million_baht-p.deposits_million_baht)/NULLIF(p.deposits_million_baht,0)
    -100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS growth_gap_pp
FROM mart_province_month n JOIN mart_province_month p
  ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
WHERE n.period=(SELECT MAX(period) FROM mart_province_month)
ORDER BY growth_gap_pp DESC, n.province_code LIMIT 10;
```

| name_th | deposit_yoy_pct | credit_yoy_pct | growth_gap_pp |
| --- | --- | --- | --- |
| ร้อยเอ็ด | 3.10 | -10.04 | 13.14 |
| ระยอง | 6.95 | -3.84 | 10.79 |
| กระบี่ | 5.83 | -4.75 | 10.58 |
| ประจวบคีรีขันธ์ | 4.91 | -5.16 | 10.07 |
| ตราด | -0.88 | -10.06 | 9.18 |
| หนองบัวลำภู | 0.32 | -8.73 | 9.05 |
| เลย | 3.50 | -5.51 | 9.00 |
| เพชรบูรณ์ | 1.44 | -7.47 | 8.90 |
| ฉะเชิงเทรา | 3.25 | -5.57 | 8.82 |
| นครราชสีมา | 2.30 | -6.40 | 8.71 |

## CQ03 — จังหวัดใดมีความหนาแน่นสาขาต่อประชากรแสนคนสูงที่สุด?

**Fields:** branches, population, population_reference_year

**Interpretation:** ประชากรตามทะเบียนเป็นตัวหาร; ไม่ใช่จำนวนลูกค้าหรือการวัดการเข้าถึงบริการโดยตรง

```sql
SELECT name_th, branches, population, population_reference_year,
  ROUND(branches_per_100k::numeric,2) AS branches_per_100k
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND branches_per_100k IS NOT NULL
ORDER BY branches_per_100k DESC, province_code LIMIT 10;
```

| name_th | branches | population | population_reference_year | branches_per_100k |
| --- | --- | --- | --- | --- |
| กรุงเทพมหานคร | 1246 | 5422568 | 2025 | 22.98 |
| ภูเก็ต | 85 | 432464 | 2025 | 19.65 |
| ชลบุรี | 239 | 1645985 | 2025 | 14.52 |
| สมุทรสาคร | 70 | 587367 | 2025 | 11.92 |
| นนทบุรี | 147 | 1322280 | 2025 | 11.12 |
| สมุทรปราการ | 152 | 1383924 | 2025 | 10.98 |
| ระยอง | 83 | 789730 | 2025 | 10.51 |
| นครปฐม | 88 | 926318 | 2025 | 9.50 |
| ปทุมธานี | 116 | 1246062 | 2025 | 9.31 |
| สุราษฎร์ธานี | 95 | 1075977 | 2025 | 8.83 |

## CQ04 — จังหวัดที่ GPP ต่างกันไม่เกิน 15% มีขนาดสินเชื่อต่างกันเท่าไร?

**Fields:** gpp_million_baht, gpp_reference_year, credits_million_baht

**Interpretation:** ไม่รวมกรุงเทพฯ; ผลต่าง GPP หารด้วยค่าที่มากกว่า; GPP รายปีต่างงวดจากสินเชื่อรายเดือน

```sql
WITH snapshot AS (
  SELECT * FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
    AND province_code<>10 AND gpp_million_baht>0 AND credits_million_baht>0
)
SELECT a.name_th AS province_a, b.name_th AS province_b,
  a.gpp_reference_year, a.gpp_million_baht AS gpp_a_million, b.gpp_million_baht AS gpp_b_million,
  ROUND((100.0*ABS(a.gpp_million_baht-b.gpp_million_baht)/GREATEST(a.gpp_million_baht,b.gpp_million_baht))::numeric,2) AS gpp_gap_pct,
  a.credits_million_baht AS credits_a_million, b.credits_million_baht AS credits_b_million,
  ROUND((GREATEST(a.credits_million_baht,b.credits_million_baht)/LEAST(a.credits_million_baht,b.credits_million_baht))::numeric,2) AS credit_size_ratio
FROM snapshot a JOIN snapshot b ON a.province_code<b.province_code
  AND ABS(a.gpp_million_baht-b.gpp_million_baht)/GREATEST(a.gpp_million_baht,b.gpp_million_baht)<=0.15
ORDER BY credit_size_ratio DESC, a.province_code, b.province_code LIMIT 10;
```

| province_a | province_b | gpp_reference_year | gpp_a_million | gpp_b_million | gpp_gap_pct | credits_a_million | credits_b_million | credit_size_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ปราจีนบุรี | ภูเก็ต | 2024 | 243,656.28 | 272,395.45 | 10.55 | 32,506.00 | 176,806.00 | 5.44 |
| ปราจีนบุรี | สงขลา | 2024 | 243,656.28 | 268,678.68 | 9.31 | 32,506.00 | 146,695.00 | 4.51 |
| นนทบุรี | ฉะเชิงเทรา | 2024 | 405,296.10 | 433,363.00 | 6.48 | 267,194.00 | 59,581.00 | 4.48 |
| ร้อยเอ็ด | พังงา | 2024 | 89,232.99 | 82,457.56 | 7.59 | 48,648.00 | 11,191.00 | 4.35 |
| ปราจีนบุรี | ขอนแก่น | 2024 | 243,656.28 | 238,726.55 | 2.02 | 32,506.00 | 137,557.00 | 4.23 |
| สระบุรี | เชียงใหม่ | 2024 | 252,148.93 | 293,809.40 | 14.18 | 52,858.00 | 203,282.00 | 3.85 |
| กระบี่ | พังงา | 2024 | 95,008.02 | 82,457.56 | 13.21 | 39,566.00 | 11,191.00 | 3.54 |
| ยโสธร | อุทัยธานี | 2024 | 34,496.29 | 34,341.51 | 0.45 | 18,517.00 | 5,296.00 | 3.50 |
| สุรินทร์ | พังงา | 2024 | 93,062.15 | 82,457.56 | 11.40 | 38,638.00 | 11,191.00 | 3.45 |
| ปทุมธานี | ฉะเชิงเทรา | 2024 | 467,878.37 | 433,363.00 | 7.38 | 201,871.00 | 59,581.00 | 3.39 |

## CQ05 — สินเชื่อและเงินฝากรวมเคลื่อนไหวอย่างไรในช่วงที่ดอกเบี้ยนโยบายเปลี่ยน?

**Fields:** period, policy_rate_pct, credits_million_baht, deposits_million_baht

**Interpretation:** policy rate ใช้มติล่าสุดไม่เกินสิ้นเดือน; การเคลื่อนไหวร่วมกันไม่พิสูจน์เหตุและผล

```sql
SELECT period, MAX(policy_rate_pct) AS policy_rate_pct,
  SUM(credits_million_baht) AS credits_million, SUM(deposits_million_baht) AS deposits_million
FROM mart_province_month GROUP BY period ORDER BY period;
```

| period | policy_rate_pct | credits_million | deposits_million |
| --- | --- | --- | --- |
| 2024-07-01 | 2.50 | 17,903,788.00 | 17,195,799.00 |
| 2024-08-01 | 2.50 | 17,917,229.00 | 16,973,713.00 |
| 2024-09-01 | 2.50 | 17,666,891.00 | 17,039,596.00 |
| 2024-10-01 | 2.25 | 18,078,339.00 | 17,399,538.00 |
| 2024-11-01 | 2.25 | 18,007,664.00 | 17,323,154.00 |
| 2024-12-01 | 2.25 | 18,120,079.00 | 17,382,795.00 |
| 2025-01-01 | 2.25 | 18,112,082.00 | 17,441,681.00 |
| 2025-02-01 | 2.00 | 18,151,087.00 | 17,482,252.00 |
| 2025-03-01 | 2.00 | 17,964,272.00 | 17,479,805.00 |
| 2025-04-01 | 1.75 | 18,111,967.00 | 17,500,861.00 |
| 2025-05-01 | 1.75 | 18,130,974.00 | 17,468,148.00 |
| 2025-06-01 | 1.75 | 18,088,854.00 | 17,392,524.00 |
| 2025-07-01 | 1.75 | 18,130,581.00 | 17,457,834.00 |
| 2025-08-01 | 1.50 | 18,010,228.00 | 17,447,155.00 |
| 2025-09-01 | 1.50 | 17,632,717.00 | 17,382,173.00 |
| 2025-10-01 | 1.50 | 17,731,397.00 | 17,543,912.00 |
| 2025-11-01 | 1.50 | 17,861,102.00 | 17,649,277.00 |
| 2025-12-01 | 1.25 | 17,965,474.00 | 17,813,846.00 |
| 2026-01-01 | 1.25 | 17,798,460.00 | 17,851,124.00 |
| 2026-02-01 | 1.00 | 17,800,336.00 | 17,852,455.00 |
| 2026-03-01 | 1.00 | 17,926,515.00 | 18,026,496.00 |
| 2026-04-01 | 1.00 | 18,066,501.00 | 18,255,047.00 |
| 2026-05-01 | 1.00 | 18,297,193.00 | 18,075,859.00 |
| 2026-06-01 | 1.00 | 18,041,166.00 | 17,992,368.00 |
| 2026-07-01 | 1.00 | 18,100,244.00 | 18,136,237.00 |

## CQ06 — จังหวัดใดจำนวนสาขาลดลงแต่สินเชื่อเพิ่มขึ้นเมื่อเทียบปีก่อน?

**Fields:** province_code, period, branches, credits_million_baht

**Interpretation:** เป็นจุดเริ่มตรวจช่องทางบริการเพิ่มเติม; ไม่สรุปว่าสาขาทำให้สินเชื่อเปลี่ยน

```sql
SELECT n.name_th, n.branches-p.branches AS branch_change,
  ROUND((100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS credit_yoy_pct
FROM mart_province_month n JOIN mart_province_month p
  ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
WHERE n.period=(SELECT MAX(period) FROM mart_province_month)
  AND n.branches<p.branches AND n.credits_million_baht>p.credits_million_baht
ORDER BY n.credits_million_baht-p.credits_million_baht DESC, n.province_code LIMIT 20;
```

| name_th | branch_change | credit_yoy_pct |
| --- | --- | --- |
| กรุงเทพมหานคร | -80 | 0.75 |
| ปทุมธานี | -14 | 0.73 |
| พังงา | -2 | 1.47 |
| สิงห์บุรี | -1 | 1.39 |
| นครนายก | -1 | 0.60 |
| อ่างทอง | -1 | 0.05 |

## CQ07 — จังหวัดใดผ่านเกณฑ์ GPP ≥100,000 ลบ., สาขาต่อแสน ≤15 และสินเชื่อ ≥50,000 ลบ.?

**Fields:** gpp_million_baht, branches_per_100k, credits_million_baht

**Interpretation:** ไม่รวมกรุงเทพฯ; เกณฑ์ตัวอย่างเพื่อ shortlist และทำ due diligence เพิ่ม

```sql
SELECT name_th, gpp_million_baht, credits_million_baht,
  ROUND(branches_per_100k::numeric,2) AS branches_per_100k
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND province_code<>10 AND gpp_million_baht>=100000 AND branches_per_100k<=15
  AND credits_million_baht>=50000
ORDER BY gpp_million_baht DESC, province_code;
```

| name_th | gpp_million_baht | credits_million_baht | branches_per_100k |
| --- | --- | --- | --- |
| ชลบุรี | 1,234,302.75 | 450,683.00 | 14.52 |
| ระยอง | 1,099,856.24 | 147,746.00 | 10.51 |
| สมุทรปราการ | 769,369.65 | 296,751.00 | 10.98 |
| ปทุมธานี | 467,878.37 | 201,871.00 | 9.31 |
| สมุทรสาคร | 433,722.43 | 104,319.00 | 11.92 |
| ฉะเชิงเทรา | 433,363.00 | 59,581.00 | 6.68 |
| นนทบุรี | 405,296.10 | 267,194.00 | 11.12 |
| พระนครศรีอยุธยา | 403,410.91 | 83,263.00 | 8.39 |
| นครปฐม | 402,264.62 | 117,007.00 | 9.50 |
| นครราชสีมา | 349,213.48 | 158,006.00 | 4.67 |
| เชียงใหม่ | 293,809.40 | 203,282.00 | 7.78 |
| สุราษฎร์ธานี | 272,251.39 | 103,568.00 | 8.83 |
| สงขลา | 268,678.68 | 146,695.00 | 7.07 |
| สระบุรี | 252,148.93 | 52,858.00 | 7.52 |
| ขอนแก่น | 238,726.55 | 137,557.00 | 5.10 |
| นครศรีธรรมราช | 201,035.53 | 77,359.00 | 5.03 |
| ราชบุรี | 192,031.72 | 55,436.00 | 6.15 |
| อุบลราชธานี | 148,641.74 | 89,021.00 | 3.06 |
| อุดรธานี | 132,615.23 | 84,676.00 | 3.81 |
| นครสวรรค์ | 128,697.39 | 54,424.00 | 4.96 |
| เชียงราย | 121,375.94 | 62,450.00 | 4.78 |
| พิษณุโลก | 116,057.88 | 57,952.00 | 5.63 |

## CQ08 — จังหวัดใดมีอัตราสินเชื่อต่อเงินฝากสูงที่สุด?

**Fields:** credits_million_baht, deposits_million_baht, credit_deposit_ratio_pct

**Interpretation:** อัตราระดับพื้นที่ไม่ใช่ liquidity ratio ของธนาคารแต่ละแห่ง

```sql
SELECT name_th, deposits_million_baht, credits_million_baht,
  ROUND(credit_deposit_ratio_pct::numeric,2) AS credit_deposit_ratio_pct
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND deposits_million_baht>0
ORDER BY credit_deposit_ratio_pct DESC, province_code LIMIT 10;
```

| name_th | deposits_million_baht | credits_million_baht | credit_deposit_ratio_pct |
| --- | --- | --- | --- |
| ร้อยเอ็ด | 38,197.00 | 48,648.00 | 127.36 |
| กรุงเทพมหานคร | 11,449,577.00 | 13,825,081.00 | 120.75 |
| บึงกาฬ | 9,198.00 | 10,722.00 | 116.57 |
| ยโสธร | 17,097.00 | 18,517.00 | 108.31 |
| อุบลราชธานี | 82,412.00 | 89,021.00 | 108.02 |
| อุตรดิตถ์ | 20,051.00 | 21,516.00 | 107.31 |
| สกลนคร | 35,314.00 | 36,930.00 | 104.58 |
| อำนาจเจริญ | 8,762.00 | 8,895.00 | 101.52 |
| ขอนแก่น | 135,836.00 | 137,557.00 | 101.27 |
| กำแพงเพชร | 27,845.00 | 28,041.00 | 100.70 |

## CQ09 — จังหวัดใดมีเงินฝากต่อผู้มีชื่อในทะเบียนสูงที่สุด?

**Fields:** deposits_million_baht, population, population_reference_year

**Interpretation:** ยอดบันทึกสำนักงานใหญ่และประชากรตามทะเบียนมีผล; ไม่ใช่เงินออมเฉลี่ยของลูกค้าจริง

```sql
SELECT name_th, population_reference_year, population,
  ROUND(deposits_baht_per_person::numeric,2) AS deposits_baht_per_person
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND population>0
ORDER BY deposits_baht_per_person DESC, province_code LIMIT 10;
```

| name_th | population_reference_year | population | deposits_baht_per_person |
| --- | --- | --- | --- |
| กรุงเทพมหานคร | 2025 | 5422568 | 2,111,467.67 |
| นนทบุรี | 2025 | 1322280 | 510,914.48 |
| ภูเก็ต | 2025 | 432464 | 485,420.75 |
| สมุทรปราการ | 2025 | 1383924 | 437,073.86 |
| ชลบุรี | 2025 | 1645985 | 415,352.51 |
| สมุทรสาคร | 2025 | 587367 | 348,443.14 |
| ปทุมธานี | 2025 | 1246062 | 301,439.25 |
| ระยอง | 2025 | 789730 | 257,922.33 |
| นครปฐม | 2025 | 926318 | 256,149.62 |
| จันทบุรี | 2025 | 535563 | 174,603.17 |

## CQ10 — สินเชื่อรวมกระจุกตัวในกรุงเทพฯ และ 5 จังหวัดอันดับแรกเท่าไร?

**Fields:** province_code, period, credits_million_baht

**Interpretation:** ใช้ยอดจังหวัดในเดือนเดียวกัน; การบันทึกสำนักงานใหญ่ไม่ใช่ตำแหน่งผู้กู้หรือส่วนแบ่งรายธนาคาร

```sql
WITH ranked AS (
  SELECT province_code, credits_million_baht,
    ROW_NUMBER() OVER (ORDER BY credits_million_baht DESC, province_code) AS rank
  FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
)
SELECT SUM(credits_million_baht) AS national_credits_million,
  ROUND((100.0*SUM(credits_million_baht) FILTER (WHERE province_code=10)/NULLIF(SUM(credits_million_baht),0))::numeric,2) AS bangkok_share_pct,
  ROUND((100.0*SUM(credits_million_baht) FILTER (WHERE rank<=5)/NULLIF(SUM(credits_million_baht),0))::numeric,2) AS top5_share_pct
FROM ranked;
```

| national_credits_million | bangkok_share_pct | top5_share_pct |
| --- | --- | --- |
| 18,100,244.00 | 76.38 | 83.11 |

This evidence records SQL/results for the stated snapshot. It does not verify current upstream freshness or a month of continuous Airflow scheduling. Application screenshots are linked from the README; Gemini is optional and is not required to execute these ten questions.
