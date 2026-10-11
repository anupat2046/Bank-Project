// Renders the data flow / lineage diagram: one swimlane per source, one column per stage.
//   node data_flow.js  ->  docs/design/data-flow.svg and .png (4800x2700)
// Rules, grains and counts follow bank/sources.py, bank/etl.py, bank/query.py and docs/data-sources.md.

const path = require("path");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const si = require("react-icons/si");
const fa = require("react-icons/fa6");
const { ROOT, renderSvg } = require("./lib/render");

const OUT_SVG = path.join(ROOT, "docs", "design", "data-flow.svg");
const OUT_PNG = path.join(ROOT, "docs", "design", "data-flow.png");
const W = 2400, H = 1350;

const K = {
  ink: "#16191F", text: "#232F3E", muted: "#545B64", white: "#FFFFFF", line: "#C5CED6",
  panel: "#F7F8F9", navy: "#14264A", mart: "#14264A", app: "#0B7A5C",
};
const FONT = "'Segoe UI', Arial, sans-serif";
const MONO = "'Cascadia Mono', Consolas, 'Courier New', monospace";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const parts = [];
const add = (s) => parts.push(s);
function icon(Icon, x, y, size, color) {
  add(renderToStaticMarkup(React.createElement(Icon, { size, color })).replace("<svg ", `<svg x="${x}" y="${y}" `));
}
function t(x, y, s, { size = 14, weight = 400, fill = K.text, anchor = "start", mono = false, italic = false } = {}) {
  add(`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" style="white-space:pre"${mono ? ` font-family="${MONO}"` : ""}${italic ? ' font-style="italic"' : ""}>${esc(s)}</text>`);
}
function rect(x, y, w, h, { fill = K.white, stroke = K.line, rx = 6, sw = 1.3, dash = "" } = {}) {
  add(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`);
}
function arrow(d, color = K.ink, width = 1.8) {
  add(`<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round" marker-end="url(#ah)"/>`);
}
// Lines: a string is mono (a real name in the repo); [text, true] is plain prose.
function lines(x, y, list, { size = 13, gap = 19, fill = K.muted } = {}) {
  list.forEach((l, i) => {
    const [s, plain] = Array.isArray(l) ? l : [l, false];
    t(x, y + i * gap, s, { size, fill, mono: !plain });
  });
}

// ------------------------------------------------------------------ columns
const COLS = [
  [30, 270, "Source", "publisher · format"],
  [330, 230, "Raw snapshot", "data/raw/<source>/<sha256>"],
  [590, 340, "Parse & map", "bank/sources.py"],
  [960, 290, "Source-grain fact", "etl.run_source()"],
  [1280, 310, "As-of join rule", "etl.build_mart()"],
  [1630, 360, "Mart columns", "mart_province_month"],
  [2030, 340, "Query-time metrics", "bank/query.py"],
];
COLS.forEach(([x, w, title, sub], i) => {
  add(`<circle cx="${x + 16}" cy="58" r="16" fill="${K.navy}"/>`);
  t(x + 16, 64, String(i + 1), { size: 15, weight: 700, fill: K.white, anchor: "middle" });
  t(x + 42, 64, title, { size: 18, weight: 700, fill: K.ink });
  t(x + 42, 88, sub, { size: 13, fill: K.muted, mono: i > 0 });
});
add(`<path d="M30,108 H2370" stroke="${K.line}" stroke-width="1.2"/>`);

// ------------------------------------------------------------------ swimlanes
const LANES = [
  {
    color: "#2E5E9E", icon: fa.FaBuildingColumns, name: "BOT", id: "FI_CB_011_S5", fmt: "web table · monthly",
    raw: ["bot/<sha256>.html", ["one file per fetch", true]],
    parse: [["Form POST, parse the HTML table", true], ["Keep 77 provinces; drop Grand Total", true], ["and head-office rows", true], "BOT_TO_CODE → province_code", ["THB million as published", true]],
    fact: ["fact_bank_month", "province × month", "1,925", "PK province_code + period"],
    rule: [["Driver: one mart row per", true], ["fact_bank_month row (1 : 1)", true], ["build fails if any row is lost", true]],
    mart: ["province_code, period (PK)", "name_en, name_th", "branches · deposits · credits", "credit_deposit_ratio_pct", "  = credits ÷ deposits × 100"],
    cover: [1925, "all rows"],
  },
  {
    color: "#0B7A5C", icon: fa.FaIdCard, name: "DOPA", id: "registered population", fmt: "TXT · annual",
    raw: ["dopa/<sha256>.txt", ["one file per year", true]],
    parse: ["stat_c{yy}.txt, 2023–2025", ["December registered population", true], ["Thai names → dim_province.name_th", true]],
    fact: ["fact_population_year", "province × year", "231", "PK province_code + reference_year"],
    rule: [["Latest reference year usable", true], ["from 1 January of the next year", true], ["(2025 counts from Jan 2026)", true]],
    mart: ["population, population_reference_year", "branches_per_100k", "  = branches ÷ population × 100,000", "deposits_baht_per_person", "  = deposits × 1,000,000 ÷ population"],
    cover: [1925, "all rows"],
  },
  {
    color: "#C77D02", icon: fa.FaChartLine, name: "NESDC", id: "GPP 2024p", fmt: "XLSX · annual",
    raw: ["nesdc/<sha256>.xlsx", ["+ HTTP Last-Modified", true]],
    parse: [["Current-price GPP, THB million", true], "NESDC_ALIASES → province_code", ["No Last-Modified header → load fails", true]],
    fact: ["fact_gpp_year", "province × year", "77", "+ source_last_modified"],
    rule: [["Reference year ≤ banking year", true], ["and Last-Modified ≤ month-end", true]],
    mart: ["gpp_million_baht", "gpp_reference_year"],
    cover: [385, "NULL before workbook availability"],
  },
  {
    color: "#6B4FBB", icon: fa.FaGlobe, name: "World Bank", id: "FP.CPI.TOTL.ZG", fmt: "REST API · JSON",
    raw: ["worldbank/<sha256>.json", ["+ dataset lastupdated", true]],
    parse: [["Thailand annual CPI inflation, %", true], ["Null values dropped (66 kept)", true], ["Single page, no duplicate years", true]],
    fact: ["fact_macro_year", "year (national)", "66", "+ source_last_updated"],
    rule: [["Reference year < banking year", true], ["and lastupdated ≤ month-end", true]],
    mart: ["inflation_pct", "inflation_reference_year"],
    cover: [0, "vintage 8 Oct 2026 is after every month"],
  },
  {
    color: "#01A88D", icon: fa.FaPercent, name: "BOT · MPC", id: "policy-rate decisions", fmt: "XLSX · per decision",
    raw: ["policy/<sha256>.xlsx", ["link found on the MPC page", true]],
    parse: [["Decision date, rate %, decision text", true], ["National, not province-specific", true]],
    fact: ["fact_policy_event", "decision date", "191", "PK event_date"],
    rule: [["Latest decision effective on or", true], ["before banking month-end", true]],
    mart: ["policy_rate_pct", "policy_event_date"],
    cover: [1925, "all rows"],
  },
];
const LY = 126, LH = 160, LG = 14;
const laneY = (i) => LY + i * (LH + LG);

// Mart and metric columns are single tall panels shared by every lane.
const MART_X = 1630, MART_W = 360, MET_X = 2030, MET_W = 340;
const PANEL_TOP = LY - 4, PANEL_H = 5 * LH + 4 * LG + 8;
rect(MART_X, PANEL_TOP, MART_W, PANEL_H, { fill: "#EEF2F8", stroke: K.mart, sw: 2, rx: 8 });

LANES.forEach((L, i) => {
  const y = laneY(i), mid = y + LH / 2;
  // lane band across stages 1–5
  rect(20, y, 1590, LH, { fill: i % 2 ? "#FAFBFC" : "#F3F6F9", stroke: "none", rx: 6 });
  add(`<rect x="20" y="${y}" width="6" height="${LH}" fill="${L.color}"/>`);
  // 1 source
  add(`<rect x="44" y="${y + 22}" width="46" height="46" rx="8" fill="${L.color}"/>`);
  icon(L.icon, 55, y + 33, 24, K.white);
  t(104, y + 40, L.name, { size: 17, weight: 700, fill: K.ink });
  t(104, y + 62, L.id, { size: 13.5, fill: L.color, weight: 600 });
  t(104, y + 84, L.fmt, { size: 13, fill: K.muted });
  // 2 raw snapshot
  rect(330, y + 22, 230, 116);
  icon(fa.FaFileLines, 346, y + 38, 26, L.color);
  lines(382, y + 56, [L.raw[0]], { size: 12.5, fill: K.ink });
  lines(346, y + 92, [L.raw[1], ["SHA-256 named, immutable", true]], { size: 12.5 });
  // 3 parse
  rect(590, y + 14, 340, LH - 28);
  lines(606, y + 40, L.parse, { size: 13, gap: 20 });
  // 4 fact
  rect(960, y + 14, 290, LH - 28, { stroke: L.color, sw: 1.6 });
  t(976, y + 40, L.fact[0], { size: 14, weight: 700, fill: K.ink, mono: true });
  t(976, y + 62, L.fact[1], { size: 13, fill: K.muted });
  t(976, y + 98, L.fact[2], { size: 28, weight: 700, fill: L.color });
  t(976 + L.fact[2].length * 17 + 8, y + 98, "rows", { size: 13, fill: K.muted });
  t(976, y + 124, L.fact[3], { size: 12, fill: K.muted, mono: true });
  // 5 rule
  rect(1280, y + 14, 310, LH - 28, { fill: K.white, stroke: L.color, dash: "5 4" });
  icon(fa.FaClock, 1294, y + 28, 18, L.color);
  lines(1320, y + 42, L.rule, { size: 13.5, gap: 21, fill: K.text });
  // stage arrows
  arrow(`M300,${mid} H328`, L.color);
  arrow(`M560,${mid} H588`, L.color);
  arrow(`M930,${mid} H958`, L.color);
  arrow(`M1250,${mid} H1278`, L.color);
  arrow(`M1590,${mid} H1628`, L.color);
  // 6 mart section for this lane
  const mx = MART_X + 16;
  if (i > 0) add(`<path d="M${MART_X + 12},${y - LG / 2} H${MART_X + MART_W - 12}" stroke="#C9D6E8" stroke-width="1" stroke-dasharray="4 4"/>`);
  add(`<rect x="${MART_X}" y="${y + 8}" width="5" height="${LH - 16}" fill="${L.color}"/>`);
  lines(mx, y + 26, L.mart, { size: 12.5, gap: 18, fill: K.ink });
  const [n, note] = L.cover, frac = n / 1925, by = y + LH - 26;
  add(`<rect x="${mx}" y="${by}" width="150" height="8" rx="4" fill="#D8E1EC"/>`);
  if (frac > 0) add(`<rect x="${mx}" y="${by}" width="${150 * frac}" height="8" rx="4" fill="${L.color}"/>`);
  t(mx + 160, by + 8, `${n.toLocaleString("en-US")} / 1,925`, { size: 12.5, weight: 700, fill: frac === 0 ? "#B42318" : K.ink });
  if (note !== "all rows") t(mx, by - 6, note, { size: 11.5, fill: frac === 0 ? "#B42318" : K.muted, italic: true });
});

// mart header badge (sits on the panel's top edge)
add(`<rect x="${MART_X + 14}" y="${PANEL_TOP - 12}" width="246" height="24" rx="12" fill="${K.mart}"/>`);
t(MART_X + 137, PANEL_TOP + 5, "1,925 rows · province × month", { size: 12.5, weight: 600, fill: K.white, anchor: "middle" });

// ------------------------------------------------------------------ 7 query-time metrics
rect(MET_X, PANEL_TOP, MET_W, PANEL_H, { fill: K.white, stroke: K.app, sw: 2, rx: 8 });
arrow(`M${MART_X + MART_W},${PANEL_TOP + PANEL_H / 2} H${MET_X - 2}`, K.mart, 2.4);
let my = PANEL_TOP + 34;
const mtitle = (s) => { t(MET_X + 16, my, s, { size: 14.5, weight: 700, fill: K.ink }); my += 22; };
const mline = (s, o = {}) => { t(MET_X + 16, my, s, { size: 12.5, fill: K.muted, ...o }); my += 19; };
t(MET_X + 16, my, "15 metrics from one catalogue", { size: 13, fill: K.app, weight: 600 }); my += 32;
mtitle("Stocks · SUM within one month");
mline("credits · deposits · branches · gpp", { mono: true }); my += 10;
mtitle("Ratios · SUM ÷ SUM");
mline("credit_deposit_ratio", { mono: true });
mline("branches_per_100k", { mono: true });
mline("deposits_per_person", { mono: true });
mline("credits_per_person  ★", { mono: true, fill: K.app });
mline("credits_per_branch  ★", { mono: true, fill: K.app });
mline("★ computed only at query time");
my += 10;
mtitle("Context");
mline("policy_rate · MAX at month-end", { mono: true }); my += 10;
mtitle("YoY · same month, prior year");
mline("credits · deposits · branches", { mono: true });
mline("credits_per_person · credits_per_branch", { mono: true }); my += 14;
add(`<path d="M${MET_X + 16},${my - 8} H${MET_X + MET_W - 16}" stroke="#E1E6EA"/>`); my += 14;
mtitle("Rules");
mline("Never SUM stocks across months");
mline("Ratio of sums, not average of ratios");
mline("NULL or zero base → unavailable, not 0"); my += 14;
add(`<path d="M${MET_X + 16},${my - 8} H${MET_X + MET_W - 16}" stroke="#E1E6EA"/>`); my += 14;
mtitle("Consumed by");
[[si.SiNextdotjs, "#000000", "Dashboard via Analytics API"], [fa.FaComments, "#ED7100", "Assistant: QueryPlan → SQL"], [fa.FaListCheck, K.navy, "10 competency questions"], [si.SiGrafana, "#F46800", "Grafana · 13 panels"]].forEach(([I, c, s]) => {
  icon(I, MET_X + 16, my - 15, 20, c);
  t(MET_X + 46, my, s, { size: 13, fill: K.text }); my += 30;
});

// ------------------------------------------------------------------ lineage band
const BY = 1010;
rect(20, BY, 1590, 316, { fill: K.panel, stroke: "#D5DBDB", rx: 8 });
t(40, BY + 36, "Lineage: trace any number back to the file it came from", { size: 18, weight: 700, fill: K.ink });
t(40, BY + 60, "Each hop is a stored key, so the path can be followed in SQL without re-fetching a source.", { size: 13.5, fill: K.muted });
const hops = [
  [fa.FaChartColumn, "Value on screen", [["API row or chart point", true]]],
  [fa.FaTableCells, "mart row", ["province_code + period", "+ *_reference_year"]],
  [fa.FaLayerGroup, "fact row", ["source_sha256"]],
  [fa.FaListCheck, "source_manifest", ["url · raw_path · sha256", "fetched_at · reference"]],
  [fa.FaFileLines, "raw file", ["data/raw/<source>/", "<sha256>.<ext>"]],
];
hops.forEach(([I, h, l], i) => {
  const x = 40 + i * 312, y = BY + 92;
  rect(x, y, 270, 132, { fill: K.white });
  icon(I, x + 16, y + 18, 26, K.navy);
  t(x + 54, y + 38, h, { size: 15.5, weight: 700, fill: K.ink, mono: i > 0 && i < 4 });
  lines(x + 16, y + 74, l, { size: 12.5, gap: 20 });
  if (i < hops.length - 1) arrow(`M${x + 270},${y + 66} H${x + 310}`, K.navy, 2);
});
t(40, BY + 262, "etl_run records status, rows_loaded and a redacted detail for every source job and mart build.", { size: 13.5, fill: K.muted });
t(40, BY + 286, "Retrieval time, reference period and publication date are stored separately; a recent fetch does not prove upstream freshness.", { size: 13.5, fill: K.muted });

// ------------------------------------------------------------------ load guarantees
rect(1630, BY, 740, 316, { fill: K.panel, stroke: "#D5DBDB", rx: 8 });
t(1650, BY + 36, "Load guarantees", { size: 18, weight: 700, fill: K.ink });
[
  ["One transaction per source", "delete + insert facts + manifest; a failed parse rolls back and keeps the previous facts"],
  ["Explicit geography", "unknown province alias fails the load; no fuzzy matching"],
  ["Mart preconditions", "77 mapped provinces required; row count must equal fact_bank_month"],
  ["No invented values", "missing context stays NULL; nothing is filled with 0 or a later vintage"],
].forEach(([h, s], i) => {
  const y = BY + 76 + i * 58;
  icon(fa.FaShieldHalved, 1650, y - 15, 20, K.app);
  t(1680, y, h, { size: 14.5, weight: 700, fill: K.ink });
  t(1680, y + 21, s, { size: 13, fill: K.muted });
});

// ------------------------------------------------------------------ assemble
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>
<rect width="${W}" height="${H}" fill="${K.white}"/>
${parts.join("\n")}
</svg>`;

renderSvg(svg, W, H, OUT_SVG, OUT_PNG).catch((e) => { console.error(e); process.exit(1); });
