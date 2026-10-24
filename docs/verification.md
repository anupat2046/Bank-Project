# Verification status and evidence

[Documentation index](README.md) · [Setup commands](getting-started.md)

Latest recorded assistant checks: **25 October 2026 (Asia/Bangkok)**; see [the router contract correction](evidence/llm/router-contract-fix-2026-10-24.md) and [earlier hardening record](evidence/llm/hardening-2026-10-24.md). New raw artifact filenames use the UTC date, 24 October. Other rows retain their historical evidence scope. This page distinguishes what was tested from what remains unverified; it is not a live service-health page.

## Evidence map

| Check | Observed evidence | What it does not establish |
| --- | --- | --- |
| Python regression | 235 tests passed on the populated local database | General natural-language accuracy or production readiness |
| Deterministic analytics | 80 authored Thai cases: status, plan, and independent numerical checks passed | Live LLM accuracy on those 80 cases |
| Frontend build | TypeScript checks and Next.js Docker production build passed | Load performance, accessibility certification, or user acceptance |
| Browser workflows | Dated desktop/mobile checks and screenshots | A permanent automated browser test suite |
| Live planner comparison | 24 turns, dev 10 / held-out 14, three strategies, retained failures | New-router accuracy or representative population accuracy |
| Conversation service | Seven-turn HTTP smoke check with live Gemini and persisted context | Exhaustive router evaluation |
| Current conversation regression | October 24: 60/60 authored offline HTTP turns passed with real warehouse arithmetic | Live Gemini accuracy or held-out generalization; the earlier Gemini live attempt was quota-blocked |
| Groq full live conversation | [60/60 authored HTTP turns, 40/40 arithmetic checks](evidence/llm/router-contract-fix-2026-10-24.md), 64 model calls; one policy-chart guard fallback retained | Held-out or LLM-only accuracy, repeated-run stability, load performance or verified account billing tier |
| Final policy-chart correction | Same record: targeted C16 passed 3/3, two arithmetic checks, three calls, no repair/fallback after the narrow guard correction | A new full-corpus live rerun on that last revision; source fingerprints distinguish the stages |
| Warehouse coverage | 77 provinces, 25 months, 1,925 rows | A month of scheduled-run continuity or verified upstream freshness |
| Airflow/Grafana | Historical successful task/panel checks | Current uptime or uninterrupted daily scheduling |

## Recorded warehouse snapshot

Range: **2024-07-01–2026-07-01**. Latest-month provincial totals: loans **18,100,244 million THB**, deposits **18,136,237 million THB**, branches **4,516**.

Source facts: population 231 rows, GPP 77, annual inflation 66, policy events 191. Population context is complete; GPP is missing in 1,540 historical rows and inflation in all 1,925 rows under conservative availability rules. See [data sources](data-sources.md).

## Planner scores versus router behavior

Final hybrid and rules-only each passed 14/14 held-out turns with zero model calls in that split. LLM-only passed 6/14 all-checks turns, with 8/10 numerical checks on expected-ready cases. These are different denominators and should not be reduced to an unqualified accuracy percentage.

The subsequent conversation router is outside that benchmark. Its recorded seven-turn integration check covers guidance, analytics, explanation, presentation changes, unsupported NPL, and preserved results. It does not establish robust intent classification across unseen Thai wording.

## Reproduce checks

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.evaluate_chat
.\.venv\Scripts\python.exe -m tools.check_docs
```

The tests need the local warehouse; expected arithmetic is derived from its current rows. A changed source snapshot may change results. Live evaluations require separate opt-in and account quota; see [methodology](llm-evaluation.md).

## Scheduler operations

The DAG is configured for 07:00 Asia/Bangkok daily, but the most recent assistant verification ran only PostgreSQL/API/web. Historical Airflow run IDs are in the [September snapshot](evidence/run-status.md).

To claim uninterrupted operation, inspect actual scheduled runs for the entire claimed interval, task statuses, source outcomes, and warehouse coverage. Manual/backfilled runs are not substitutes. This documentation review does not start Airflow, create historical runs, or assert a completed month.

## Dated artifacts

- [UI wording, responsive layout, and conversation navigation checks — 24 October](evidence/ux-qa-2026-10-24.md)
- [Competency query SQL/results](competency-questions.md)
- [Next.js browser verification](evidence/nextjs-qa.md)
- [Analytical assistant checks](chatbot-analytics.md)
- [Conversation routing/service smoke](conversation-routing.md)
- [Live planner report and raw JSON](evidence/llm/results.md)
- [Single pre-router service smoke](evidence/llm/service-smoke.md)
- [September pipeline/Grafana snapshot](evidence/run-status.md)

Older documents retain their original observation dates and counts. Use the current guides for behavior; use historical artifacts only for the specific checks and builds they record.
