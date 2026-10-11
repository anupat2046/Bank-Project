# Operational dashboards

Next.js serves business analysis. Grafana serves pipeline health, data quality,
and observed AI/API operation. The former provincial reporting dashboard is
replaced, retaining its UID so existing bookmarks open Pipeline Health.

## Dashboards

| Dashboard | Local URL | Scope |
| --- | --- | --- |
| Pipeline Health | http://127.0.0.1:3001/d/thai-bank-regions | Job outcomes, recorded duration, recent failures, last successful load |
| Data Quality & Freshness | http://127.0.0.1:3001/d/bank-data-quality | Source references, retrieval/revision dates, coverage and current integrity checks |
| AI & API Performance | http://127.0.0.1:3001/d/bank-ai-operations | HTTP status, latency, assistant outcomes, model failures and usage coverage |

Each dashboard has six SQL panels and an explanatory panel. The datasource uses
the existing SELECT-only `bank_reader` role. These are polling dashboards, not
configured alerts. No Prometheus or log collection service is required.

## Deploy and verify

```powershell
docker compose up -d --build postgres api grafana
```

API startup applies additive schema changes: `operation_metric` and nullable
`etl_run.duration_ms`. Existing rows and warehouse facts are preserved. New table
SELECT privileges follow the database bootstrap's default privileges.

`OPERATIONS_METRICS_ENABLED=true` is set only for the Compose API. It is off by
default for local scripts. Direct benchmark calls do not persist operational
chat rows; HTTP smoke tests do count as traffic. Restart/rebuild the API when
changing instrumentation. No LLM request is required to open the dashboards.

```powershell
python tools/build_operations_dashboards.py
python -m pytest tests/test_operations.py -q
```

The integration test executes every dashboard query using the reader role.
Grafana's provisioning folder polls the generated JSON files. Edit the generator
rather than saving a divergent UI-only dashboard.

## Metric meanings and limitations

- `etl_run.started_at` is a legacy name: the existing ETL writes the row after
  completion. Panels therefore call it `recorded_at`, not actual start time.
  Duration measures the job after schema initialization and before logging.
  Historical duration stays NULL. A process killed before logging has no result
  row, so latest-job state alone cannot detect every interrupted run.
- ETL results are source/mart job records, not Airflow scheduled DAG evidence.
  Use Airflow run history to verify scheduling continuity.
- Last successful load, source reference period, and publication/revision date
  are different. No universal stale threshold is imposed on monthly, annual,
  and event-based sources. Snapshot panels deliberately ignore the time picker.
- Missing annual context can follow temporal availability rules. Current unmapped
  rows are not historical mapping failures. No historical quality measurements
  are fabricated.
- HTTP latency measures time until response production, not browser rendering or
  streaming completion. API counts and chat-turn counts must not be added together.
  A chat can return HTTP 200 with an analytical error; assistant outcome panels
  show that separately. Clarification is not necessarily an error.
- Model failures count captured failed provider calls. They do not represent all
  validation failures. This version does not publish a validation-rejection rate.
- Unknown usage and cost stay NULL. Known-only sums are partial when coverage is
  incomplete. Cost requires configured input/output rates and provider usage;
  it is an estimate, not a billing invoice. Operational success is not accuracy:
  see the separate dated [LLM evaluation](llm-evaluation.md).

## Privacy, reliability, and retention

Stored fields are allowlisted numeric metrics, bounded outcome labels, route
templates, and server timestamps. No request body, query string, session ID,
prompt, raw exception, credential, or checkpoint content is copied to this table.
Unknown HTTP paths are grouped as `unmatched`.

Writes are synchronous, best-effort database transactions in a worker thread;
failures log a generic warning and do not replace the analytical result. This is
local prototype instrumentation, not a durable event queue. Missing writes mean
the dashboard can undercount activity. There is no automatic retention cleanup
yet: monitor table growth and choose a retention policy before persistent use.

Earlier Grafana screenshots in [docs/evidence](evidence/README.md) show the
historical business reporting dashboard. They are not evidence of these
operational dashboards.

## Verification snapshot: 11 October 2026

- 175 Python tests passed, including all 18 provisioned SQL queries executed as
  `bank_reader`, privacy filtering, and HTTP-to-chat metric context propagation.
- The deployed `/health` endpoint returned 25 months and latest banking period
  `2026-07-01`. Its real HTTP requests appeared in the API metric table.
- Browser review confirmed the three provisioned dashboards render query results.
  No live Gemini call was made for this change. Chat panels correctly had no
  observed turns; old ETL durations remained NULL.
- [Pipeline screenshot](../output/playwright/grafana-pipeline-operations.png),
  [data-quality screenshot](../output/playwright/grafana-data-quality.png), and
  [AI/API screenshot](../output/playwright/grafana-ai-operations.png).
- The installed optional `grafana-lokiexplore-app` emitted a browser preload error
  for `react/jsx-runtime`. These dashboards use PostgreSQL and rendered without
  SQL errors. The unrelated plugin was not upgraded or removed.
