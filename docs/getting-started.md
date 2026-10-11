# Setup and troubleshooting

[Documentation index](README.md) · [Project overview](../README.md)

This guide targets PowerShell on Windows with Docker Desktop using Linux containers. Run commands from the repository root unless a section says otherwise. Other environments may work but have not been verified by this guide.

## 1. Start the core application

```powershell
docker compose up -d --build postgres api web
docker compose ps
```

PostgreSQL must become healthy before the API starts. Initial image builds require network access. The application can start before data is loaded; a healthy container does not mean the warehouse is populated.

## 2. Import the public data

```powershell
docker compose exec api python -m bank.etl all
```

This sequentially loads BOT banking data, DOPA population, NESDC GPP, World Bank inflation, BOT policy decisions, and then builds the mart. It requires internet access and can take several minutes. Source website changes may require adapter maintenance.

Inspect every job's reported status. Each source fact is replaced transactionally, but the complete multi-source import is not one global transaction. If a source fails, do not assume that the mart was rebuilt or that all sources share a new vintage. Review the source-quality page and logs before repeating the affected load.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

`months_loaded` and `latest_period` describe the imported warehouse, not independently verified upstream freshness. The documented October snapshot contains 25 months ending July 2026; a new import may produce a different snapshot.

## 3. Open the application

| Service | Local URL | Notes |
| --- | --- | --- |
| Next.js | http://127.0.0.1:3000 | Five-page analytical application |
| FastAPI reference | http://127.0.0.1:8000/docs | Read endpoints and chat API |
| Grafana, when started | http://127.0.0.1:3001/d/thai-bank-regions | Pipeline Health; links to Data Quality and AI/API Operations |
| Airflow, when started | http://127.0.0.1:8081 | Standalone development scheduler/UI |

All published service ports bind to `127.0.0.1`. This is not an internet-facing deployment configuration.

## 4. Enable Gemini (optional)

No key is needed for ingestion, dashboards, or supported rules-based analysis. To enable the LLM conversation router and analytical fallback:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env privately and set GEMINI_API_KEY.
docker compose up -d --build api web
```

The configured default is `gemini-2.5-flash`. Gemini takes precedence when both provider keys are present. The optional OpenAI path exists but has not been verified live. Model availability, quotas, and charges depend on the provider/account.

Do not paste keys into issues, screenshots, or prompts. Do not use browser-visible `NEXT_PUBLIC_*` variables for secrets. Questions and recent conversation context may be sent to the configured provider; use only public-data examples. Offline routing is narrower than LLM routing.

Try `ทำอะไรได้บ้าง`, then `สินเชื่อต่อประชากรสูงสุด 10 จังหวัด`, followed by `เปลี่ยนเป็นตาราง`. Explanation/presentation requests require an earlier successful analytical result.

## 5. Start Grafana and Airflow (optional)

Grafana now monitors operations rather than duplicating Next.js business charts.
For upgrades, rebuild the API first (`docker compose up -d --build api`) to create
the operational metrics table and nullable ETL duration column. See the
[operations guide](operations.md) for metric definitions and limitations.

Complete the initial import first to avoid overlapping initial loads:

```powershell
docker compose up -d grafana airflow
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags list-runs -d bank_regional_daily --no-backfill
```

The DAG is configured for **07:00 Asia/Bangkok daily**, with `catchup=False` and one active run. Daily polling does not turn monthly source observations into daily banking data. Docker and the scheduler must remain running for scheduled jobs to execute.

Grafana's initial development login is `admin` / `bank_dev_password`. An existing Grafana volume may retain a previously changed password. Airflow uses user `admin`; read its generated local password only on your own machine:

```powershell
docker compose exec airflow cat /opt/airflow/standalone_admin_password.txt
```

The output is a credential: do not publish it. Passwords and ETL tokens in Compose are development-only. Authentication, secret management, TLS, and production operational controls are separate work.

## 6. Verify and develop

For host-side Python tests, install Python 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.evaluate_chat
.\.venv\Scripts\python.exe -m tools.check_docs
```

Database-backed tests need the populated local PostgreSQL service on port 5433 and its development roles. Normal regressions do not send model requests. Do not load private provider keys into a test shell unnecessarily.

Frontend development needs Node.js compatible with the project (the Docker image uses Node 24):

```powershell
cd frontend
npm ci
npm run typecheck
npm run dev
```

The development proxy defaults to the API on port 8000. See [frontend configuration](../frontend/README.md). Python requirements use version ranges rather than a fully locked environment; a future clean install may resolve different versions.

## Persistence and shutdown

PostgreSQL and Grafana use named Docker volumes. Raw snapshots are stored under Git-ignored `data/raw/`; the API bind-mounts that directory. Chat checkpoints persist separately from the page-local transcript.

```powershell
docker compose stop
```

Stopping services preserves stored data but stops scheduling. Do not remove volumes unless you intentionally want to discard database/dashboard state.

## Common problems

| Symptom | Check |
| --- | --- |
| Docker daemon unavailable | Start Docker Desktop and confirm Linux-container mode |
| Empty dashboard / missing relations | Complete the initial import and inspect its final statuses |
| Source download or parsing failure | Check network/source publication changes; preserve prior evidence rather than fabricating replacements |
| Missing historical inflation or GPP | Inspect availability/reference dates; `NULL` can be an intentional no-lookahead result |
| AI timeout or quota failure | Verify local configuration and account status; try a supported rules-based question |
| Clarification instead of an answer | Specify metric, province, and banking month; do not confuse malformed planning with provider downtime |
| Grafana login does not match Compose | Existing volumes can retain changed credentials; changing the environment alone does not reset them |
| No new scheduled runs | Confirm Airflow is running and the DAG is unpaused; check actual history, not warehouse month count |
