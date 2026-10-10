# Next.js migration verification

Follow-up on **11 October 2026**: at the user's request, the legacy Streamlit code, configuration, Compose service and UI-only dependencies were removed. The historical observations below describe the migration verification before that removal; there is no longer a `legacy` profile or port-8501 application. Screenshots are retained as historical evidence.

Removal verification: 43 local Python tests passed; `pip check` found no broken requirements; API and web images rebuilt successfully. The rebuilt API contains neither Streamlit nor Plotly nor `/app/app.py`. Next.js returned HTTP 200; warehouse health remained OK with 25 months. All ten competency-question endpoints returned results through the Next.js proxy. The old dashboard container was removed and port 8501 was no longer reachable. Database volumes and the resume draft were not changed.

Verified locally on **10 October 2026**, approximately 23:30–23:55 Asia/Bangkok. This records observed checks, not production certification, user research, or uninterrupted scheduler evidence. The approved scope was the five-page UX/UI migration; `docs/resume-draft.md` was intentionally left unchanged.

## Implementation and automated checks

- Preserved Python ETL, PostgreSQL, Airflow, Grafana and the existing constrained LangGraph/Gemini query pipeline. Added analytical FastAPI endpoints and a Next.js allowlisted same-origin server proxy.
- `.\.venv\Scripts\python.exe -m pytest -q`: **43 passed**. Tests include read API contracts, historical competency-query scoping, comparison limits, public-source redaction and mocked provider-error redaction. Automated tests do not call a paid provider.
- `npm run typecheck`: passed. Production `next build` in the Docker image: passed. `docker compose up -d --build web`: built and started successfully.
- Final `/health`: `status=ok`, `months_loaded=25`, `latest_period=2026-07-01`. Warehouse: 77 provinces, July 2024–July 2026, 1,925 province-month rows.
- Final Compose inspection: web and API running; PostgreSQL healthy. Existing legacy Streamlit and Airflow were also running. No assertion is made about a continuous month of scheduled DAG runs.
- `GET /api/etl/bot` through the web proxy returned 404: analytical navigation cannot proxy ETL endpoints. Environment files, node modules and build caches remain Git-ignored. No credentials were added to browser code or evidence.

## Browser workflow checks

The computer-use browser inventory was unavailable, so verification used the Playwright CLI with a task-specific Chromium session against the production Docker application. No Playwright test suite was added. Desktop captures used a **1505 × 1045** viewport; the mobile overview used **390 × 844**. Full-page captures extend below the viewport.

| Workflow | Observed result |
|---|---|
| Latest overview | 18.10 trillion THB loans, 18.14 trillion THB deposits, 4,516 branches; actual YoY values displayed |
| Earliest month | July 2024 loads its own totals; absent prior-year comparison is explained, not shown as zero |
| Search, sorting and CSV | Searching Chiang Mai returns 1 of 77 provinces; sort works; downloaded CSV has Thai unit-bearing headers and values 203282 / 311310 / 140 |
| Province detail | Chiang Mai history contains 25 months; GPP and population reference years are explicitly separate |
| Comparison | Chiang Mai and Chon Buri selection reflected in the URL, table and trend; index mode explains baseline 100 |
| Shortlist | Default criteria return 22 provinces; extreme GPP threshold produces an explained empty result; resetting restores 22 |
| CQ catalog | Ten real catalog questions; CQ10 renders actual 76.38% Bangkok / 83.11% top-five shares, result table and SQL disclosure |
| Sources | Five public sources, retrieval dates, join rules, coverage and redacted ETL jobs visible; retrieval is not labelled source freshness |
| Gemini smoke test | One live Thai question, “แนวโน้มเงินฝากย้อนหลัง”, returned Gemini mode, 25 monthly rows, chart, SQL/parameters and provenance; latest deposit value 18,136,237 million THB |
| Mobile | All five routes measured document width = viewport width = 390px; tables scroll internally; chat conversation/result switch works |
| Keyboard drawer | Opening focuses the close control; Shift+Tab stays inside the dialog; Escape closes it and restores focus to the menu button |
| Error recovery | Intercepted overview HTTP 503 produces the retry state; removing interception and clicking retry restores real 18.10-trillion KPI |

The live Gemini check is an end-to-end smoke test, **not** an accuracy or multi-turn benchmark. The deliberate HTTP 503 test generated an expected browser network error; a fresh final session through overview, provinces, screening, CQ10 and sources reported **0 errors and 0 warnings**. The hidden mobile chart warning found earlier was fixed by mounting charts only when their observed container has nonzero dimensions.

## Data availability observed during verification

World Bank's fetched dataset now carries a **2026-10-08** vintage and 66 non-null annual observations. The existing conservative mart rule forbids using that revised vintage in banking periods before its availability date. Consequently all 1,925 historical inflation fields are currently NULL; they are not fabricated or replaced with zero. Sources UI and root documentation disclose this. Two earlier tests assumed the old vintage/count; they now independently calculate eligible rows and validate the joined values against source records. The ETL availability rule itself was not weakened.

Under the same rule, GPP is unavailable in 1,540 historical rows, while registered-population coverage is complete. The currently selected July 2026 provincial view has GPP 2024 and population 2025. Historical source vintages would be needed to restore as-of historical inflation without lookahead. Upstream freshness was not independently audited during this UI migration.

## Design fidelity ledger

The [five generated concepts](../design/nextjs/design-spec.md) were development references, not working-product evidence or independently approved screen images. They were inspected against rendered captures; the written user-approved plan and actual results take precedence over generated sample copy/numbers. This is not a claim of pixel-identical reproduction.

| Aspect compared | Final result and adjustment |
|---|---|
| Main shell / hierarchy | Pale 230px sidebar, five outline-icon navigation items, active teal selection and consistent utility header retained; header standardized to 64px |
| Palette / surfaces | White analytical workspace, navy text, teal accents, muted axes and thin borders retained; no marketing hero or decorative gradients |
| Typography / controls | Locally bundled readable Thai font and tabular figures; table sort controls changed from oversized boxes to plain header buttons |
| KPI and chart structure | Three open overview KPIs, banking trend, separate policy plot and concentration rail retained; real YoY adds intentional vertical space |
| Chart readability | Compact chart heights, correct Thai month abbreviations, unit-aware tooltips, keyboard line toggles and a visible dot for single-month history |
| Province workspace | Detail / compare / shortlist tabs, adjustable filter rail, searchable table and GPP scatter implemented; reference years no longer display thousands separators |
| Assistant workspace | Conversation/result split, real mode, chart/table and SQL disclosure retained; mobile switches between panes rather than squeezing them together |
| Small-screen navigation | Offscreen closed menu hidden from keyboard navigation; focus trap and Escape return added; no page-level horizontal overflow observed |

Intentional differences: concept trend shapes, placeholder provincial rows and generated question wording were discarded; executed catalog SQL is shown with bound as-of scope; chat does not expose a misleading global month selector or fake provider dropdown; sources do not display invented green freshness badges. Actual source retrieval timestamps and NULL coverage replace generated status claims. The legacy Streamlit UI remains optional under the `legacy` Compose profile.

## Captured evidence

- [Market overview](../../output/playwright/nextjs-overview.png)
- [Province detail](../../output/playwright/nextjs-provinces.png)
- [Shortlist and scatter](../../output/playwright/nextjs-screening.png)
- [CQ10 result](../../output/playwright/nextjs-questions.png)
- [Live Gemini answer and SQL](../../output/playwright/nextjs-assistant.png)
- [Sources and coverage](../../output/playwright/nextjs-sources.png)
- [Mobile overview](../../output/playwright/nextjs-mobile.png)

## Remaining scope boundaries

This is a local analytical prototype. Shared-user authentication, authorization, deployment-grade throttling, accessibility certification, performance/load benchmarks and a systematic LLM evaluation are not implemented or claimed. Chat history in the frontend is page-local; a new conversation creates a new session identifier rather than claiming to delete persisted checkpoints. No public deployment, Git commit or push was performed.
