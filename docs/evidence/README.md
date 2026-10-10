# Evidence catalogue

[Documentation index](../README.md) · [Current verification scope](../verification.md)

Evidence is dated and scoped. A successful past run, screenshot, or HTTP request is not a live status check or a production-readiness certificate.

## Structured evidence

| Artifact | Scope |
| --- | --- |
| [Competency results JSON](competency-results.json) / [query report](../competency-questions.md) | Ten executed questions on the recorded October warehouse |
| [Live planner reports](llm/results.md) | Versioned dev/held-out comparison; raw JSON preserves failures and usage |
| [Planner HTTP smoke](llm/service-smoke.md) | One local pre-router integration request |
| [Conversation smoke](../conversation-routing.md) | Seven subsequent routed service turns |

The incomplete `llm/dev-v1.json` records an aborted setup attempt, not a completed model benchmark. The `*-live.json` reports and hashes remain unchanged when narrative documentation is edited.

## Interface and pipeline observations

- [Next.js verification](nextjs-qa.md): desktop/mobile checks on 10–11 October 2026; working captures are linked from that report and the root README.
- [September verification](run-status.md): historical data vintage, Airflow run IDs, and Grafana checks. Its older counts are not current coverage.
- [Airflow graph](airflow-graph-qa.png): six successful tasks in an observed run, not a month of continuity.
- [Grafana overview](grafana-qa.png), [detail](grafana-detail-qa.png), [YoY](grafana-growth-qa.png), [policy/GPP](grafana-policy-qa.png), and [growth consistency](grafana-new-panels-qa.png): historical provisioned dashboard views.

Other images in this folder preserve earlier dashboard/chatbot development checks. They are not the current Next.js interface and should not be used as evidence of new routing behavior. Generated design concepts live separately in `docs/design/`.

## Updating evidence

Record a new date and artifact for a new measurement. Do not fabricate scheduled history, overwrite raw evaluation outcomes, backdate source availability, or relabel concept charts as real observations. See [contribution guidance](../../CONTRIBUTING.md).
