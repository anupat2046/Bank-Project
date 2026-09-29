# Architecture & Data Warehouse Design

```mermaid
flowchart LR
  BOT[ธปท. ตารางจังหวัดรายเดือน] --> RAW[Raw files + SHA-256]
  DOPA[DOPA ประชากรทะเบียน] --> RAW
  NESDC[สศช. GPP XLSX] --> RAW
  WB[World Bank JSON API เงินเฟ้อ] --> RAW
  MPC[ธปท. MPC official XLSX มติดอกเบี้ย] --> RAW
  RAW --> ETL[Python adapters + strict validation]
  AIR[Airflow 07:00 Bangkok] --> API[FastAPI protected ETL endpoints]
  API --> ETL
  ETL --> PG[(PostgreSQL bank warehouse)]
  PG --> GRAF[Grafana 13 panels]
  PG --> UI[Streamlit dashboard]
  UI --> GRAPH[LangGraph chatbot]
  GRAPH --> PLAN[LangChain structured plan / Thai rules fallback]
  PLAN --> SQL[Bounded SQL compiler + SQLGlot]
  SQL --> RO[(bank_reader SELECT only)]
  GRAPH --> CP[(PostgreSQL checkpoints)]
```

```mermaid
erDiagram
  DIM_PROVINCE ||--o{ FACT_BANK_MONTH : province_code
  DIM_MONTH ||--o{ FACT_BANK_MONTH : period
  DIM_PROVINCE ||--o{ FACT_POPULATION_YEAR : province_code
  DIM_PROVINCE ||--o{ FACT_GPP_YEAR : province_code
  DIM_PROVINCE ||--o{ MART_PROVINCE_MONTH : province_code
  DIM_MONTH ||--o{ MART_PROVINCE_MONTH : period
  FACT_BANK_MONTH ||--|| MART_PROVINCE_MONTH : province_period
  FACT_MACRO_YEAR ||--o{ MART_PROVINCE_MONTH : reference_year_context
  FACT_POLICY_EVENT ||--o{ MART_PROVINCE_MONTH : latest_event_asof_month_end
  DIM_PROVINCE {
    int province_code PK
    string name_en
    string name_th
  }
  DIM_MONTH {
    date period PK
    int year_ce
    int year_be
    int month_number
  }
  FACT_BANK_MONTH {
    int province_code PK
    date period PK
    float deposits_million_baht
    float credits_million_baht
    int branches
    string source_sha256
  }
  FACT_POPULATION_YEAR {
    int province_code PK
    int reference_year PK
    int population
  }
  FACT_GPP_YEAR {
    int province_code PK
    int reference_year PK
    float gpp_million_baht
    date source_last_modified
  }
  FACT_MACRO_YEAR {
    int reference_year PK
    float inflation_pct
    date source_last_updated
  }
  FACT_POLICY_EVENT {
    date event_date PK
    float policy_rate_pct
    string decision
    string source_sha256
  }
  MART_PROVINCE_MONTH {
    int province_code PK
    date period PK
    float credit_deposit_ratio_pct
    float branches_per_100k
    float deposits_baht_per_person
    int population_reference_year
    int gpp_reference_year
    int inflation_reference_year
    float policy_rate_pct
    date policy_event_date
  }
```

หลักการ: จังหวัดเป็น crosswalk แบบตรวจมือ 77 code, ไม่ใช้ fuzzy match; แยก grain จังหวัด–เดือนจากจังหวัด–ปีและประเทศ–ปี; ค่า annual เป็น context ล่าสุดที่ทราบตามกติกา availability ไม่ใช่ข้อเท็จจริงรายเดือน. `NULL` หมายถึงไม่มี/ยังใช้ไม่ได้. `source_manifest` และ `etl_run` ผูก provenance และผลรัน แต่ไม่ใช่ fact เชิงธุรกิจ

```mermaid
flowchart LR
  B[load_bot] --> M[build_mart]
  D[load_dopa] --> M
  N[load_nesdc] --> M
  W[load_worldbank_api] --> M
  P[load_bot_policy_workbook] --> M
```

Airflow DAG ไม่สร้างค่ารายวันจากชุดรายเดือน: รันทุกวันเพื่อตรวจการเผยแพร่หรือ revision และโหลด fact ตามงวดต้นฉบับ การตั้งเวลาใช้ timezone Asia/Bangkok; metadata ของ Airflow อยู่ PostgreSQL ฐาน `airflow` แยกจากฐาน `bank`
