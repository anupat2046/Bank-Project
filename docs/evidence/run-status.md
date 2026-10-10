# Historical verification snapshot — 28 September 2026

[Documentation index](../README.md) · [Current verification status](../verification.md)

This preserves observations from 28 September 2026 (Asia/Bangkok). It is **not current status**: the later World Bank vintage, assistant behavior, frontend, and test count differ. Do not replace these historical observations with newer values or infer uninterrupted scheduling from them.

## Imported data at that date

- BOT fact/mart: 77 provinces × 25 months = 1,925 rows; latest banking period July 2026.
- DOPA: 231 rows, 77 provinces × three years.
- NESDC: 77 rows, GPP 2024p.
- World Bank: 65 non-null annual observations; metadata `lastupdated=2026-07-13`.
- BOT MPC workbook: 191 decisions, latest file event 26 August 2026 at 1.00%. The July mart used the 24 June 2026 decision at 1.00%, not the later event.
- In that vintage, all 77 latest-month province rows had population, GPP, and inflation context. This inflation observation is superseded by the later 8 October vintage and its conservative availability result.
- July provincial totals: 4,516 branches; loans 18,100,244 million THB; deposits 18,136,237 million THB, 4 million above the independently rounded BOT Grand Total.

## Recorded Airflow runs

Airflow metadata used the separate PostgreSQL `airflow` database. The observed records were:

| Run ID (UTC) | Observed status |
| --- | --- |
| `scheduled__2026-09-26T00:00:00+00:00` | success |
| `manual__2026-09-27T22:58:53+00:00` | success |
| `manual__2026-09-27T22:59:57+00:00` | success |
| `manual__2026-09-27T23:15:09+00:00` | success, including the fifth source task for the policy workbook |
| `scheduled__2026-09-27T00:00:00+00:00` | success; observed execution began 28 September at 07:00 Bangkok and ended at 07:00:34 |

Run identifiers reflect scheduler data intervals, not necessarily execution start times. These records contain manual and scheduled runs and do not prove a continuous month.

After the API data bind mount was configured, referenced raw snapshots were found on the host. Per-source outcomes were recorded in `etl_run`.

## Quality and interface checks

- Python suite: **34 passed** at this stage, including 25 rules-mode questions, all 13 Grafana panel queries, no-lookahead joins, trend windows, and read-only DB checks.
- API health: 25 months, latest period `2026-07-01`.
- Grafana: 13 provisioned panels read through its API; panel SQL returned warehouse rows.
- `bank_reader` could SELECT the mart but could not INSERT.
- Browser checks observed Grafana panels and six successful Airflow tasks.

Captured historical evidence: [Grafana policy/GPP](grafana-policy-qa.png), [growth consistency](grafana-new-panels-qa.png), and [Airflow graph](airflow-graph-qa.png). Older dashboard/chatbot images in this directory are not evidence of the current Next.js/router behavior.

## Inspect current state separately

```powershell
docker compose ps
docker compose exec airflow airflow dags list-runs -d bank_regional_daily --no-backfill
Invoke-RestMethod http://127.0.0.1:8000/health
```

The Airflow command requires the service to be running. Current results must be recorded as new evidence, not silently written into this snapshot.
