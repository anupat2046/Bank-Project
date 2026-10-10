# Next.js UX/UI specification

This specification defines the five-page analytical application. AI-generated screen references are visual concepts, not working-product screenshots or evidence of measured data. Their sample copy and numbers do not override warehouse results or the competency-question catalogue. See [implemented-workflow verification](../../evidence/nextjs-qa.md).

## System

- Framework: Next.js App Router + TypeScript. Existing Python FastAPI, ETL, warehouse, Grafana and LangGraph retained.
- Main background: true white `#ffffff`; sidebar `#f6f8fa`; text `#10244b`; primary `#087d65`; active selection `#e1f0ed`; muted `#62718a`; border `#e2e8ef`.
- Fonts: locally bundled Noto Sans Thai 400/600/700, 15–16px body, 30px h1, 20px h2, 13–14px controls, tabular numeric cells.
- Layout: 230px sidebar, 64px utility header, 32px main gutters, 20–24px region gaps. Open KPI strips, restrained single-border chart/table surfaces, no nested cards, gradients, illustrations or marketing hero.
- Icons: Lucide outline, 18–20px, 1.8px navigation stroke. BarChart3 / MapPin / MessageSquare / ListChecks / Database; Download / Search / Menu / X / ArrowRight for actual controls.
- Components: Shell, PageHeading, DataState, Footer, DataTable, TrendChart, Bars, GppScatter. Shared loading/error/empty states and keyboard-visible focus.
- Mobile: menu drawer at <=850px, single-column primary work areas, scrollable tables with sticky names, chat conversation/result tabs, compact question selector.

## Page structure and Thai interface copy

Navigation: ภาพรวมตลาด / วิเคราะห์จังหวัด / ผู้ช่วยวิเคราะห์ / คำถามธุรกิจ / แหล่งข้อมูล. Brand: Bank Intelligence. Month selector: งวดข้อมูล.

1. `overview-concept.png`: ภาพรวมตลาดธนาคาร; subtitle สินเชื่อ เงินฝาก และเครือข่ายสาขาระดับประเทศ; three KPI columns; แนวโน้มสินเชื่อและเงินฝาก with 12 เดือน/ทั้งหมด; separate policy timeline; ตลาดรายจังหวัด table; ข้อสังเกตจากข้อมูล concentration rail.
2. `provinces-concept.png`: วิเคราะห์จังหวัด; subtitle เปรียบเทียบตลาดและคัดพื้นที่ศึกษาต่อ; province select; รายละเอียดจังหวัด/เปรียบเทียบ/คัดกรองพื้นที่; filter rail; real result count and table; GPP scatter; shortlist caveat.
3. `assistant-concept.png`: ผู้ช่วยวิเคราะห์; 40/60 conversation/result split; explicit mode; textarea + ส่งคำถาม; result graph/table; sources/caveat; SQL disclosure. Real provider errors never presented as successful answers.
4. `questions-concept.png`: คำถามธุรกิจ; 10 คำถาม พร้อมผลจริงและวิธีคำนวณ; 10-question rail; actual selected question; chart/table; business purpose and next investigation; SQL disclosure.
5. `sources-concept.png`: แหล่งข้อมูลและคุณภาพ; ตรวจที่มา ช่วงเวลา และกติกาการเชื่อมข้อมูล; coverage strip; five-source table; join rules; public ETL history.

## Deliberate departures from generated references

- All chart data, result rows, question wording, reference years, growth and timestamps must be real. Generated illustrations of charts and table values are not implementation seeds.
- The existing ten CQ IDs and meanings are preserved; generated question names are not authoritative.
- Actual YoY and calculation disclosure are included in the implementation.
- AI mode is displayed, not a provider-selection dropdown: selection remains backend configuration. The global month selector is hidden in chat because the existing planner determines its own scope; every answer reveals actual query parameters/results. No fake selected-month claim.
- Sources show retrieval timestamps but explicitly say upstream freshness is not checked. No invented green freshness status.
- SQL disclosures for CQ show the executed scoped SQL and bound as-of parameter, rather than implying a latest-only query matched an older month.
- Public HTTP proxy only permits analytical reads and chat. It never forwards ETL writes or credentials.
- Next.js is the sole application frontend.

## Image generation brief

One AI-generated desktop concept per page was used for visual exploration at 1440 × 1000, with shared white/navy/teal colors, a 230px sidebar, Thai navigation labels, and restrained analytical surfaces. Concepts do not supply application data. Inspect the [concept images](overview-concept.png), [province concept](provinces-concept.png), [assistant concept](assistant-concept.png), [question concept](questions-concept.png), and [source concept](sources-concept.png) separately from the working screenshots linked in the root README.
