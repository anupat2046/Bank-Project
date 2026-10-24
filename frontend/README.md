# Bank Intelligence web application

Next.js App Router + TypeScript, React, Recharts, Lucide outline icons and locally bundled Noto Sans Thai. Five routes: `/`, `/provinces`, `/assistant`, `/questions`, `/sources`.

This is the sole application frontend.

## Run with the existing warehouse

From the project root:

```powershell
docker compose up -d --build postgres api web
```

Open http://127.0.0.1:3000. Initial warehouse loading is documented in the root README. The web image runs as the non-root `node` user. It contains no provider or database credentials.

## Local frontend development

With the Python API running at port 8000:

```powershell
cd frontend
npm ci
npm run dev
```

The server-side proxy defaults to `http://127.0.0.1:8000`. If needed, copy `.env.example` to `.env.local` and change `API_BASE_URL`. Never add provider keys to browser-visible `NEXT_PUBLIC_*` variables. The Docker service sets `API_BASE_URL=http://api:8000`.

```powershell
npm run typecheck
npm run build
```

## Interaction contracts

- Month and province/shortlist/comparison filters are URL-backed. Navigation preserves the month and up to four comparison selections.
- Monthly stocks are not summed over time. YoY always compares the same month in the previous year; missing base periods are not displayed as zero growth.
- Comparison index mode normalizes each province to its first displayed period (100); zero/null baselines stay unavailable.
- Chat determines its own scope and reveals actual query parameters. Its month selector is hidden because analytical scope comes from the question and confirmed conversation context. A root-layout provider preserves the transcript, draft, selected answer, and pending response during client-side navigation. Reloading starts a new browser conversation. Confirmed analytical context is persisted server-side by LangGraph session ID; starting again generates a new ID without deleting old database checkpoints.
- Chat supports ratio-aware clarification, multi-metric tables/CSV, filters, province comparison, YoY and contextual follow-ups. The chart selector separates different units, while multi-province trends use distinct series. See [analytics contracts and evaluation](../docs/chatbot-analytics.md).
- A bounded conversation router selects capability guidance, greetings, analytical questions, clarification, explanation, presentation changes, or refusal. Explanations use the last confirmed metric definition; chart/table changes reuse its rows without querying again. Router and planner identifiers are available in the expandable system details. See [conversation routing](../docs/conversation-routing.md).
- CQ SQL is constrained to `period <= :as_of`, including peer pairs and 12-month growth cohorts. Empty historical results are explained, not replaced with latest data.
- Public sources and ETL history omit internal paths/errors. Retrieval time is not called upstream freshness.
- Tables sort, search and export filtered rows with units and UTF-8 BOM; values are escaped against spreadsheet-formula interpretation.

The UI remains a loopback-only analytical prototype, not an authenticated or production banking system. Authentication, deployment-grade throttling and shared-user chat-history policies are not claimed.

See [design references and specification](../docs/design/nextjs/design-spec.md) and [verification](../docs/evidence/nextjs-qa.md).
