# Next.js UX/UI specification

The user approved the written five-page migration plan with “ทำเลย”. The five generated screen references are visual development concepts, not screenshots of a working product and not independently user-approved images. Generated copy and sample numbers never override actual warehouse results or the existing CQ catalog.

## System

- Framework: Next.js App Router + TypeScript. Existing Python FastAPI, ETL, warehouse, Grafana and LangGraph retained.
- Main background: true white `#ffffff`; sidebar `#f6f8fa`; text `#10244b`; primary `#087d65`; active selection `#e1f0ed`; muted `#62718a`; border `#e2e8ef`.
- Fonts: locally bundled Noto Sans Thai 400/600/700, 15–16px body, 30px h1, 20px h2, 13–14px controls, tabular numeric cells.
- Layout: 230px sidebar, 64px utility header, 32px main gutters, 20–24px region gaps. Open KPI strips, restrained single-border chart/table surfaces, no nested cards, gradients, illustrations or marketing hero.
- Icons: Lucide outline, 18–20px, 1.8px navigation stroke. BarChart3 / MapPin / MessageSquare / ListChecks / Database; Download / Search / Menu / X / ArrowRight for actual controls.
- Components: Shell, PageHeading, DataState, Footer, DataTable, TrendChart, Bars, GppScatter. Shared loading/error/empty states and keyboard-visible focus.
- Mobile: menu drawer at <=850px, single-column primary work areas, scrollable tables with sticky names, chat conversation/result tabs, compact question selector.

## Locked structure and visible copy

Navigation: ภาพรวมตลาด / วิเคราะห์จังหวัด / ผู้ช่วยวิเคราะห์ / คำถามธุรกิจ / แหล่งข้อมูล. Brand: Bank Intelligence. Month selector: งวดข้อมูล.

1. `overview-concept.png`: ภาพรวมตลาดธนาคาร; subtitle สินเชื่อ เงินฝาก และเครือข่ายสาขาระดับประเทศ; three KPI columns; แนวโน้มสินเชื่อและเงินฝาก with 12 เดือน/ทั้งหมด; separate policy timeline; ตลาดรายจังหวัด table; ข้อสังเกตจากข้อมูล concentration rail.
2. `provinces-concept.png`: วิเคราะห์จังหวัด; subtitle เปรียบเทียบตลาดและคัดพื้นที่ศึกษาต่อ; province select; รายละเอียดจังหวัด/เปรียบเทียบ/คัดกรองพื้นที่; filter rail; real result count and table; GPP scatter; shortlist caveat.
3. `assistant-concept.png`: ผู้ช่วยวิเคราะห์; 40/60 conversation/result split; explicit mode; textarea + ส่งคำถาม; result graph/table; sources/caveat; SQL disclosure. Real provider errors never presented as successful answers.
4. `questions-concept.png`: คำถามธุรกิจ; 10 คำถาม พร้อมผลจริงและวิธีคำนวณ; 10-question rail; actual selected question; chart/table; business purpose and next investigation; SQL disclosure.
5. `sources-concept.png`: แหล่งข้อมูลและคุณภาพ; ตรวจที่มา ช่วงเวลา และกติกาการเชื่อมข้อมูล; coverage strip; five-source table; join rules; public ETL history.

## Deliberate departures from generated references

- All chart data, result rows, question wording, reference years, growth and timestamps must be real. Generated illustrations of charts and table values are not implementation seeds.
- The existing ten CQ IDs and meanings are preserved; generated question names are not authoritative.
- Actual YoY and calculation disclosure are included per the user-approved plan.
- AI mode is displayed, not a provider-selection dropdown: selection remains backend configuration. The global month selector is hidden in chat because the existing planner determines its own scope; every answer reveals actual query parameters/results. No fake selected-month claim.
- Sources show retrieval timestamps but explicitly say upstream freshness is not checked. No invented green freshness status.
- SQL disclosures for CQ show the executed scoped SQL and bound as-of parameter, rather than implying a latest-only query matched an older month.
- Public HTTP proxy only permits analytical reads and chat. It never forwards ETL writes or credentials.
- Next.js is the sole application frontend.

## Image generation brief

Built-in Image Gen, one fresh desktop concept per page. Each brief requested a full 1440x1000-composition readable Thai analytical screen, shared white/navy/teal palette, a 230px pale sidebar, exact five navigation labels, locally implementable controls/text, thin dividers, restrained surfaces, no fake product claims, avatars, hero badges, gradients or decorations. Per-page prompts requested the structures listed above. Only known public snapshot summary values (18.10/18.14 trillion, 4,516 branches, 76.38% Bangkok, 83.11% top five, 77 provinces/25 months) were supplied; any other generated sample numbers are discarded.
