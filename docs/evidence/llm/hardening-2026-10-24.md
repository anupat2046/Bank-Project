# LLM hardening verification — 24 October 2026

This record distinguishes implemented safeguards, deterministic checks and actual provider availability. It does not replace the historical planner-only benchmark or establish production readiness.

## Implemented changes

- v4 semantic checks reject conflicts with recognized explicit metrics/ratios, provinces, dates, filters, strict comparisons, ordering, exclusions, requested measures and numbered limits. They do not use benchmark expected labels or silently repair a contradictory model plan. Coverage remains lexical, not a guarantee for arbitrary language.
- Buddhist-year ISO dates normalize to CE. Supported thresholds normalize Thai thousand/hundred-thousand/million population units and baht/million/billion/trillion monetary units. Unsupported grains, future periods and unsupported upper-bound filters no longer silently become unrelated latest-month rankings.
- Hybrid planning distinguishes genuine ambiguity/unsupported requests from unrecognized language. Recognizing a metric alone no longer blocks LLM fallback. Short month/denominator replies can resolve pending clarification even during router outages.
- Provider failures use bounded classifications, with no raw exception strings or credentials returned. Quota cooldown is 300 seconds, authentication/model cooldown 600 seconds and transient cooldown 30 seconds. Circuits are process-local and reset on API restart; a rotated credential/model has a separate identity.
- Each request admits at most three model calls, with a configured SDK timeout up to 12 seconds per call and a 45-second admission budget. These are not a hard cancellation guarantee, load test or distributed rate limiter. No provider network retries, automatic billing changes or unrequested model switching were added.
- Explanations use computed evidence (displayed extrema/gaps and same-series endpoint changes), definitions, sources and caveats. An available LLM selects allowlisted evidence IDs. The application renders the text/numbers; invalid selection or provider failure uses deterministic evidence. Endpoint changes are explicitly not mislabeled as YoY.
- API default sessions receive distinct UUIDs. Same-session graph calls serialize within a process. Multi-worker locking, authenticated session ownership, retention, distributed breakers and abuse controls remain deployment requirements.
- Chat replies include allowlisted per-request timing/token/error metadata. `/ai/health` describes the current process without probing the provider. UI status distinguishes successful analytical fallback from successful AI operation and gives the operator a recovery action.

## Recorded checks

| Check | Observed outcome | Limit |
| --- | --- | --- |
| Python regression | 207 tests passed against the populated local warehouse | Provider behavior is mocked in deterministic tests; not a live model accuracy score |
| HTTP conversation regression | 60/60 turns passed, 20 isolated sessions | Authored regression, not an untouched held-out split; no model calls |
| Numerical verification | Independent arithmetic over actual warehouse records; plan fields, row order/count, scope and values checked | Same recorded warehouse snapshot; no claim about future source vintages |
| Frontend | Docker production build and TypeScript checks passed | No new load/accessibility certification |
| Browser | Real Next.js `/api/chat` request, valid three-province ratio ranking, explicit quota/fallback notice | Quota failure is real; no successful live Gemini response established |
| Responsive notice | 1440×1000 and 375×812 captures inspected; mobile document width 375px | Limited to the changed notice/chat workflow |

Warehouse scope: **77 provinces, 25 months, 1,925 rows**, with latest period **2026-07-01**. The regression checks metric changes that retain province/date/exclusion scope, limit follow-ups, month/denominator clarification replies, help/explanation, presentation reuse, unsupported requests and independent query arithmetic. A discovered numbered-request parsing gap (`ขอ 7 จังหวัด…`) was fixed. Province-selection order is compared as a set rather than treated as a semantic error.

### Live provider result: blocked, not passed

A bounded direct diagnostic returned the allowlisted signal `RESOURCE_EXHAUSTED`. Two subsequent HTTP verification runs each stopped on their first request after `quota_exhausted`; neither continued through the remaining 59 regression turns. These are separate integration attempts, not repeated accuracy trials or successful live-model benchmarks. The later attempt recorded one actual model call and one provider error, while the rules fallback still produced an analytical answer. Unknown token usage/cost remains `null`, not zero/free.

The exact account constraint (for example, a time-window quota versus a project limit) was not established from the safe classification alone. The account owner must inspect provider usage/limits and decide whether to wait, change the permitted model/configuration, or enable paid capacity. No billing, API key, model selection or provider account setting was changed automatically.

- [First bounded live attempt](conversation-live-2026-10-24.json)
- [Live verification with request telemetry](conversation-live-verification-2026-10-24.json)
- [Offline 60-turn report](conversation-regression-2026-10-24.json)
- [Desktop quota/fallback capture](../../../output/playwright/assistant-provider-quota-desktop.png)
- [Mobile quota/fallback capture](../../../output/playwright/assistant-provider-quota-mobile.png)

The frontend was rebuilt from its normal Dockerfile. API verification reused the existing installed-dependency image and overlaid the changed application/SQL files; dependencies were not changed. A clean dependency installation/API image build was not revalidated in this check. The existing frontend dependency audit still reports a critical advisory; this task did not upgrade dependencies or establish public-deployment safety.

### Final deployed-service fallback check

After the final API update, a fresh five-turn session verified: seven-province loans-per-person ranking; a change to deposits-per-person retaining the seven-province/latest-month scope; explanation using verified evidence; clarification for a year-only loan request; and resolution to July 2025 after the user supplied the month. All five requests completed with the circuit already open and **zero additional model calls**. This verifies outage-mode continuity, not live Gemini accuracy.

An earlier final smoke request timed out at the HTTP transport. A subsequent warehouse health check and the five-turn session succeeded; the timeout's exact cause was not established. Host C: free space was only about 0.3 GB. Three explicitly identified build-cache records created during this change (about 908 MB inside Docker) were removed; source files, databases, volumes and other projects' caches were untouched. Build cache can be regenerated, but this did not immediately restore host filesystem free space. The owner should free additional host disk space before further builds; the application passing functional tests does not remove that operational risk.

## Pre-commit review

The final local review reran the Python suite (**212 passed**) and the authored offline conversation regression (**60/60 passed**). The frontend TypeScript check passed. All **218 local links** in the changed Markdown files resolved. No live model requests were made during this review. Redundant planner exception handling and an unused retry environment assignment were removed; dated live failures and screenshots remain as referenced evidence.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.evaluate_conversation --max-requests 60 --out data/eval/conversation-regression-new.json
# Requires a working configured provider. Up to three model calls per HTTP turn.
.\.venv\Scripts\python.exe -m tools.evaluate_conversation --live --max-requests 6 --out data/eval/conversation-live-new.json
Invoke-RestMethod http://localhost:8000/ai/health
```

After quota recovery, freeze the implementation and run separately reviewed held-out questions through the full router/planner/context flow. Compare current rules-only, LLM-only and hybrid strategies on identical cases before making new generalization or comparative accuracy claims. Historical v3 scores remain historical and are not evidence that v4 Gemini succeeded today.
