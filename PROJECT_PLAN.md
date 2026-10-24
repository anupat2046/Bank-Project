# Project roadmap

This document separates implemented capabilities from future work. It is not a delivery promise, a runtime status page, or evidence of uninterrupted scheduling. Current usage is documented in the [README](README.md) and [documentation index](docs/README.md).

## Implemented baseline

As verified on 11 October 2026 (Asia/Bangkok):

- Five real public-data adapters with explicit province mapping, raw hashes, and transactional loading.
- A 77-province, 25-month warehouse with source-grain facts and a province–month mart.
- A daily Airflow DAG, three provisioned Grafana operations dashboards (pipeline health, data quality, AI/API performance), and a five-page Next.js analytical application.
- Ten predefined business analyses with SQL and recorded results.
- A bounded conversation router, hybrid analytical planner, read-only execution, and confirmed session context.
- An 80-question deterministic regression corpus, a separate 24-turn live planner comparison, and allowlisted operational telemetry.

Implementation does not imply that every service is running or every upstream source is fresh. See [verification scope](docs/verification.md).

## Next priorities

| Priority | Work | Acceptance evidence |
| --- | --- | --- |
| 1 | Broader conversation-router evaluation | Unseen Thai paraphrases, mixed intents, topic switches, and repeated trials; report route errors separately from planner errors |
| 1 | Improve residual LLM planning errors | Buddhist-year conversion, inclusive/strict filters, and year-only clarification; use new development cases and a newly frozen held-out split |
| 1 | Reproducible dependency setup | Tested Python constraints/lock strategy and clean-machine startup checks |
| 2 | Historical publication vintages | Verifiable archived datasets and availability metadata; no fabricated publication dates |
| 2 | Scheduler operations evidence | Actual consecutive scheduled-run records, observed source coverage, and dated screenshots |
| 2 | Production access boundaries | Authentication, session ownership, retention/deletion, rate limits, secret management, and deployment-specific checks |
| 3 | Durable observability | Controlled metrics export, log retention, alerting, and calibrated cost estimates |
| 3 | Additional context sources | Documented definitions and geographic/temporal compatibility before extending the mart |

## Evaluation discipline

The existing held-out planner outcomes have already been inspected and must not be reused as an untouched evaluation set for future tuning. Keep their historical reports, create a new split, freeze the implementation, and publish both improvements and failures.

Live model requests require explicit opt-in and a call budget. Offline regressions should not depend on provider availability. Router accuracy, query-plan correctness, numerical correctness, and user-facing explanation quality are distinct measurements.

## Outside the analytical scope

Customer-level data, individual-bank market share, credit approvals, forecasts, causal attribution, branch ROI, unrestricted SQL/code execution, and autonomous multi-agent analysis are not supported. An authenticated BOT API adapter is not currently implemented; the public table/workbook adapters are the existing ingestion paths.

The roadmap tracks planned work without assigning dates to unimplemented features. Release decisions depend on verified deployment checks and operational evidence.
