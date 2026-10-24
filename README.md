# Thailand Regional Banking Intelligence

A public-data analytics platform for comparing Thailand's provincial banking markets. It combines a PostgreSQL warehouse, daily ETL orchestration, a Next.js dashboard, Grafana operational monitoring, and a provider-configurable analytical assistant.

Supports regional strategy and channel planning through traceable public-data analysis.

[ภาษาไทย](README_TH.md) · [Feature walkthrough](docs/demo.md) · [Quick start](docs/getting-started.md) · [Documentation](docs/README.md)

![Market overview with loan and deposit balances, branch counts, and monthly trends](output/playwright/demo-overview.webp)

## Business problem

Provincial loan balances alone are a poor basis for comparing markets: Bangkok dominates recorded balances, while provinces differ in population, economic scale, and branch coverage. The relevant publications also use different geographic names, reporting grains, units, and release dates.

The platform integrates five public datasets from four institutions into a province–month mart so analysts can compare market size, growth, and scale-adjusted measures with visible calculation rules and provenance. Screening results identify areas for further investigation; assessing unmet demand or profitability requires additional evidence.

## What the application supports

- **Market overview:** national loan/deposit balances, branch counts, YoY changes, trends, and concentration.
- **Province analysis:** detailed histories, comparisons of up to four provinces, GPP context, and adjustable screening criteria.
- **Analytical assistant:** Thai questions, ratio-aware rankings, filters, comparisons, YoY, and follow-ups; capability guidance, grounded definitions, and chart/table changes.
- **Business questions:** ten predefined analyses with actual results, SQL, parameters, and interpretation.
- **Source quality:** coverage, reference periods, retrieval metadata, availability rules, and redacted ETL status.

The assistant supports Groq, Gemini and OpenAI adapters. Explicit provider selection never silently switches to another provider; the latest live integration checks used Groq with `openai/gpt-oss-20b`. Analytical requests use a hybrid planner: known wording is resolved with semantic rules, unresolved paraphrases can use LLM-generated plans, and only validated plans reach read-only SQL. Groq uses JSON Object Mode with Pydantic and semantic validation, not a strict-decoding guarantee. No-key mode remains usable with narrower offline routing and deterministic analytical coverage.

## Feature walkthrough

[![Open the narrated walkthrough: English voice and Thai subtitles](output/playwright/demo-narrated-walkthrough.webp)](docs/media/bank-intelligence-walkthrough-en-th.mp4)

**[Open or download the 4:40 MP4](docs/media/bank-intelligence-walkthrough-en-th.mp4)** — English narration and Thai subtitles, edited and rendered with HyperFrames from actual application recordings and verified captures.

Follow market overview, province comparison and screening, AI analysis and follow-ups, all ten business questions, sources, Grafana, Airflow, and mobile views. The film includes close views and reading holds. Captures are dated **24 October 2026**, with banking data through **July 2026**.

[Chapter guide and screenshots](docs/demo.md) · [Thai subtitles](docs/media/bank-intelligence.th.srt) · [English transcript](docs/media/bank-intelligence.en.srt) · [Video verification](docs/evidence/narrated-video-qa-2026-10-24.md)

The final MP4, compressed documentation images and subtitle text are versioned in this repository. Full-resolution masters and the editable HyperFrames project are maintained separately.

## Data and technology

Verified snapshot: **77 provinces × 25 months = 1,925 analytical rows**, covering **July 2024–July 2026**. These are dated observations, not a guarantee of current upstream freshness.

| Source | Ingestion | Purpose |
| --- | --- | --- |
| Bank of Thailand, FI_CB_011_S5 | Public web table over HTTP GET/form POST | Monthly loans, deposits, and branches |
| Department of Provincial Administration | Official TXT downloads | Annual registered population |
| NESDC | Official GPP workbook | Annual provincial economic context |
| World Bank Indicators | Public JSON REST API | Inflation source is loaded; historical mart values are unavailable in the recorded snapshot under availability rules |
| Bank of Thailand MPC decisions | Official workbook | National policy-rate history |

The BOT adapters use published tables/workbooks, **not authenticated BOT REST APIs**. See [sources, units, mapping, and temporal joins](docs/data-sources.md).

| Layer | Implementation |
| --- | --- |
| Application | Next.js App Router, TypeScript, Recharts |
| API and ingestion | Python, FastAPI, pandas, SQLAlchemy, psycopg |
| Warehouse | PostgreSQL; dimensions, source-grain facts, province–month mart |
| Orchestration and monitoring | Apache Airflow; Grafana dashboards for pipeline health, data quality, and AI/API operations |
| Assistant | Configurable Groq/Gemini/OpenAI adapters, LangChain, LangGraph checkpoints, Pydantic plans, SQLGlot validation |
| Verification | pytest, independent arithmetic checks, authored LLM evaluation, timing/token telemetry |

## Architecture

![High-level architecture: tiers, data pipeline (A–D) and user request path (1–6)](docs/design/system-architecture.drawio.svg)

Lettered steps (A–D) are the data pipeline; numbered steps (1–6) follow a user request. This is the original editable draw.io diagram. Its Gemini label predates configurable Groq/Gemini/OpenAI support; see the [current provider contract](docs/conversation-routing.md). Source snapshots are hashed with SHA-256, geographic mapping is explicit, and unavailable values remain `NULL`. Provider responses cannot execute arbitrary SQL: the application validates bounded plans and compiles parameterized, read-only queries. See [architecture and data model](docs/architecture.md) for routes, modules, tables, and database roles.

## Run locally

Prerequisite: Docker Desktop with Linux containers.

From the repository root in PowerShell:

```powershell
docker compose up -d --build postgres api web
docker compose exec api python -m bank.etl all
```

The import uses live public sources, requires internet access, and may take several minutes. Check its final status before using the dashboard. Open [the application](http://127.0.0.1:3000) or [API documentation](http://127.0.0.1:8000/docs).

For optional LLM provider configuration, Grafana/Airflow setup, development, verification, and troubleshooting, follow the [setup guide](docs/getting-started.md). No LLM key is required to load data or explore the dashboards. Keep keys in a private `.env`, never in browser-visible `NEXT_PUBLIC_*` variables.

## Product views

| Provincial comparison and screening | Analytical assistant |
| --- | --- |
| ![Selected-province comparison and normalized measures](output/playwright/demo-comparison.webp) | ![Actual assistant result with units, scope and inspectable query details](output/playwright/demo-assistant.webp) |

Additional captures: [province detail](output/playwright/nextjs-provinces.png), [business question](output/playwright/nextjs-questions.png), [source quality](output/playwright/nextjs-sources.png), and [mobile overview](output/playwright/nextjs-mobile.png). Grafana now provides [operational monitoring](docs/operations.md); previous Grafana captures show the retired business-reporting view.

The walkthrough captures document the local application on 24 October 2026. See the [feature catalogue](docs/demo.md) for coverage and recording details, and the [UI verification record](docs/evidence/ux-qa-2026-10-24.md) for earlier checks. Screenshots and recordings are not an LLM accuracy benchmark or proof of continuous scheduled operation.

## Verification

Latest recorded checks: **24 October 2026 (Asia/Bangkok)**.

| Check | Recorded result | What it establishes |
| --- | --- | --- |
| Python regression | 212 passed | Database-backed analytics and deterministic/mocked provider checks |
| Thai analytical corpus | 80 offline cases passed | Status, plan and independently calculated results |
| Conversation regression | 60/60 offline turns passed | Routing, context, clarification, presentation and warehouse arithmetic |
| Groq live integration | Router/planner checks and three-turn HTTP smoke passed | Integration evidence, not general model accuracy |
| Frontend | TypeScript and Docker production build passed | Build verification, not a load or accessibility certification |

The historical **11 October Gemini planner comparison** is retained separately: 10 development and 14 held-out turns across three strategies. Hybrid passed 14/14 held-out turns with **zero model calls** on that split; LLM-only passed 6/14 under the strict rubric. Those scores do not measure the later conversational router or establish Groq accuracy. Account-specific provider failures remain in the dated evidence, not product capability claims.

See [verification status](docs/verification.md), [evaluation methodology](docs/llm-evaluation.md), and [full results with retained failures](docs/evidence/llm/results.md).

## Scope and limitations

- **Deployment configuration:** the supplied Compose setup binds services to loopback and uses development credentials. Shared access requires authentication, session ownership, rate limiting, secret management, and retention controls; these are not implemented in the supplied configuration.
- Loan/deposit balances are month-end stocks: aggregate across provinces within a month, never sum across months. Per-person loans are not personal debt; branch density is not a complete measure of financial access.
- Bangkok may reflect head-office booking. Registered population is not the number of customers. GPP and banking balances have different reference periods; associations do not establish causation.
- The observed World Bank vintage is **8 October 2026**, later than all banking months in this snapshot. Conservative availability rules therefore leave historical inflation unavailable; archived publication vintages are not reconstructed.
- A 25-month warehouse history does **not** prove a month of continuous scheduled Airflow operation. That requires separate observed run history.
- LLM calls can send authored questions and conversation context to the configured provider. Checkpoints store chat history; starting a new conversation does not delete old checkpoints. Never enter customer data or secrets.

## Repository guide

```text
bank/                 ingestion, API, analytical compiler, assistant, telemetry
frontend/             Next.js application and same-origin API proxy
airflow/dags/         daily source-loading and mart-building DAG
db/                   development database bootstrap and read-only role
grafana/              provisioned datasource and dashboard definitions
sql/                  competency-question SQL
tests/                regression tests and labelled question fixtures
tools/                evidence export, evaluation, and log aggregation
docs/                 guides, design notes, dated verification, and raw reports
output/playwright/    selected working-application screenshots
```

Start with the [documentation index](docs/README.md). Future work is separated in the [roadmap](PROJECT_PLAN.md). See [contribution guidance](CONTRIBUTING.md) for verification and publishing evidence.

## Author

**Anupat Suttilert** — Fourth-year Data Science student at Thammasat University, focused on data engineering and verifiable analytics.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/anupat-suttilert-888a73348)
[![GitHub](https://img.shields.io/badge/GitHub-anupat2046-black?logo=github)](https://github.com/anupat2046)
[![Website](https://img.shields.io/badge/Website-anupatsuttilert.com-teal)](https://anupatsuttilert.com/)

Interested in reliable data pipelines, analytical data modeling, and AI-assisted analytics with verifiable results.

- **Project focus:** Integrating Thai public data into a province-month warehouse for banking-market analysis, with interactive dashboards and a validated analytical assistant.
- **Core stack in this project:** Python, SQL, PostgreSQL, Apache Airflow, FastAPI, Next.js, and Docker.
- **AI and reporting:** Configurable LLM providers, LangChain, LangGraph, and Grafana.

## License

Project code is available under the [MIT License](LICENSE). Third-party datasets and dependencies retain their own licenses or published usage terms; the project license does not relicense provider data. See the [source catalogue](docs/data-sources.md).
