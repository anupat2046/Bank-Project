# Documentation

Use this index to find application guides, architecture, operational procedures, and dated verification records for the public-data analytics platform. Runtime status and upstream freshness are checked separately from the documentation.

## Start here

| Document | Purpose |
| --- | --- |
| [Project overview](../README.md) / [Thai overview](../README_TH.md) | Business purpose, capabilities, screenshots, and scope |
| [Setup and troubleshooting](getting-started.md) | First import, optional services, development, and verification commands |
| [Business findings](business-report.md) | Ten business questions, observed findings, and appropriate next investigations |
| [Sources and temporal joins](data-sources.md) | Actual ingestion methods, grains, units, mapping, and missing data |
| [Architecture](architecture.md) | Data model, service boundaries, ETL, and chat workflow |
| [Verification status](verification.md) | Latest recorded checks and the limits of each evidence type |
| [Operational monitoring](operations.md) | Grafana pipeline, data-quality and AI/API dashboards; privacy and metric definitions |

## Analytical assistant

- [Metric and query contract](chatbot-analytics.md): formulas, filters, context, SQL limits, and analytical screenshots.
- [Conversation routing](conversation-routing.md): action selection, bounded fallback, explanation/presentation behavior, and service smoke checks.
- [LLM evaluation](llm-evaluation.md): corpora, rubric, strategy comparison, telemetry, and reproduction.
- [Measured planner results](evidence/llm/results.md): strict development/held-out scores, failures, and raw reports.

## Application and query evidence

- [Evidence catalogue](evidence/README.md): scope and status of historical reports, screenshots, and raw artifacts.
- [Ten competency questions](competency-questions.md): Thai question wording, SQL, and results from the recorded warehouse snapshot.
- [Frontend guide](../frontend/README.md): routes, development, and interaction contracts.
- [Design specification](design/nextjs/design-spec.md): visual references and intentional implementation differences. Concept images are not working-product evidence.
- [Next.js verification](evidence/nextjs-qa.md): dated October checks and screenshots; not a live status page.
- [September verification snapshot](evidence/run-status.md): historical ingestion/Grafana/Airflow checks. Source vintages and test counts have since changed.
- [Planner service smoke](evidence/llm/service-smoke.md): one pre-router HTTP integration request, distinct from benchmark results.

## Maintaining the repository

See [contribution guidance](../CONTRIBUTING.md) and the [roadmap](../PROJECT_PLAN.md). Public evidence must state the date, warehouse/model scope, and what was actually checked. Keep raw evaluation artifacts unchanged when editing their explanatory documents.

### Screenshot conventions

Selected current-application captures are in `output/playwright/`; older verification images are in `docs/evidence/`. Filenames alone do not establish capture dates or current feature coverage. Root READMEs use a small selected gallery rather than embedding every historical image.

### Document language

The root overview is available in English and Thai. Technical guides use English; Thai analytical questions, interface labels, and province names remain in their original language to match the product and test fixtures.
