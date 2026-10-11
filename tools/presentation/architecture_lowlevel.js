// Renders the low-level system architecture diagram (containers, endpoints, modules, tables, roles).
//   node architecture_lowlevel.js  ->  docs/design/system-architecture-low-level.svg and .png (4800x3000)
// Names, routes, limits and roles are taken from compose.yaml, bank/*.py, airflow/dags and frontend/app.

const fs = require("fs");
const path = require("path");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const si = require("react-icons/si");
const fa = require("react-icons/fa6");

const ROOT = path.resolve(__dirname, "..", "..");
const OUT_SVG = path.join(ROOT, "docs", "design", "system-architecture-low-level.svg");
const OUT_PNG = path.join(ROOT, "docs", "design", "system-architecture-low-level.png");
const W = 2400, H = 1500;

const K = {
  ink: "#16191F", text: "#232F3E", muted: "#545B64", white: "#FFFFFF", soft: "#F2F8FC", panel: "#F7F8F9",
  host: "#01A88D", web: "#14264A", app: "#0B7A5C", chat: "#ED7100", data: "#336791", etl: "#7D8998",
  ext: "#8C4FFF", grafana: "#F46800", reader: "#336791", owner: "#C2410C", get: "#0B7A5C", post: "#ED7100",
};
const FONT = "'Segoe UI', Arial, sans-serif";
const MONO = "'Cascadia Mono', Consolas, 'Courier New', monospace";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const parts = [];
const add = (s) => parts.push(s);

function icon(Icon, x, y, size, color) {
  add(renderToStaticMarkup(React.createElement(Icon, { size, color })).replace("<svg ", `<svg x="${x}" y="${y}" `));
}
function t(x, y, s, { size = 14, weight = 400, fill = K.text, anchor = "start", italic = false, mono = false } = {}) {
  add(`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"${italic ? ' font-style="italic"' : ""}${mono ? ` font-family="${MONO}"` : ""}>${esc(s)}</text>`);
}
function group(x, y, w, h, color, Icon, title, sub, { dash = "", fill = "none", logo = false } = {}) {
  add(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${color}" stroke-width="1.8"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`);
  add(`<rect x="${x}" y="${y}" width="40" height="40" fill="${color}"/>`);
  icon(Icon, x + 9, y + 9, 22, K.white);
  t(x + 52, y + 27, title, { size: 19, weight: 600, fill: K.ink });
  if (sub) t(x + 52 + title.length * 10 + 12, y + 27, sub, { size: 15, fill: K.muted, italic: true });
  if (logo) icon(logo[0], x + w - 40, y + 10, 26, logo[1]);
}
function box(x, y, w, h, { fill = K.white, stroke = "#C5CED6", dash = "", rx = 6 } = {}) {
  add(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="1.3"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`);
}
// Titled box with mono code lines (functions, files, tables).
function codeBox(x, y, w, h, title, lines, o = {}) {
  box(x, y, w, h, o);
  t(x + 12, y + 24, title, { size: 15, weight: 700, fill: o.titleFill || K.ink });
  lines.forEach((l, i) => {
    const [s, plain] = Array.isArray(l) ? l : [l, false];
    t(x + 12, y + 46 + i * 19, s, { size: o.lineSize || 13, fill: o.lineFill || K.muted, mono: !plain });
  });
}
function method(x, y, m) {
  add(`<rect x="${x}" y="${y - 14}" width="46" height="20" rx="3" fill="${m === "GET" ? K.get : K.post}"/>`);
  t(x + 23, y + 1, m, { size: 11.5, weight: 700, fill: K.white, anchor: "middle" });
}
const MARK = { [K.ink]: "ah", [K.reader]: "ar", [K.owner]: "ao", [K.ext]: "ae", [K.app]: "ag" };
function arrow(d, { both = false, dash = "", color = K.ink, width = 1.8 } = {}) {
  const m = MARK[color];
  add(`<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round"${dash ? ` stroke-dasharray="${dash}"` : ""} marker-end="url(#${m})"${both ? ` marker-start="url(#${m})"` : ""}/>`);
}
function tag(x, y, s, color = K.muted, anchor = "middle") {
  const w = s.length * 7 + 14;
  const left = anchor === "middle" ? x - w / 2 : anchor === "end" ? x - w : x;
  add(`<rect x="${left}" y="${y - 13}" width="${w}" height="20" rx="3" fill="${K.white}" stroke="#E1E6EA"/>`);
  t(left + w / 2, y + 2, s, { size: 12.5, fill: color, anchor: "middle" });
}

// ================================================================== left: external actors
group(30, 90, 300, 470, K.etl, fa.FaBuildingColumns, "Public sources", "", { dash: "7 5" });
const srcs = [
  ["BOT", "app.bot.or.th", "BOTWEBSTAT report 1008 · HTML form"],
  ["DOPA", "stat.bora.dopa.go.th", "stat_c{yy}.txt"],
  ["NESDC", "nesdc.go.th", "GPP workbook · XLSX"],
  ["World Bank", "api.worldbank.org", "FP.CPI.TOTL.ZG · JSON"],
  ["BOT · MPC", "bot.or.th", "policy-rate workbook · XLSX"],
];
srcs.forEach(([n, host, what], i) => {
  const y = 150 + i * 82;
  t(48, y + 16, n, { size: 15, weight: 700, fill: K.ink });
  t(48, y + 36, host, { size: 13, fill: K.data, mono: true });
  t(48, y + 55, what, { size: 12.5, fill: K.muted });
});

group(30, 600, 300, 410, K.web, fa.FaUsers, "Clients", "", { dash: "7 5" });
icon(fa.FaUsers, 60, 660, 44, K.text);
t(118, 682, "Analyst browser", { size: 15, weight: 700, fill: K.ink });
t(118, 702, "http://localhost:3000", { size: 13, fill: K.data, mono: true });
icon(fa.FaUserGear, 60, 760, 40, K.text);
t(118, 778, "Operator", { size: 15, weight: 700, fill: K.ink });
t(118, 798, "Grafana   :3001", { size: 13, fill: K.data, mono: true });
t(118, 817, "Airflow UI :8081", { size: 13, fill: K.data, mono: true });
t(48, 880, "Browser only calls same-origin", { size: 13, fill: K.muted });
t(48, 899, "/api/*; API_BASE_URL stays", { size: 13, fill: K.muted });
t(48, 918, "server-side.", { size: 13, fill: K.muted });

// ================================================================== host
group(355, 30, 1680, 1450, K.host, si.SiDocker, "Docker Compose host", "ports bound to 127.0.0.1 → container", { dash: "8 6" });

// ---------------------------------------------------------------- airflow container
group(385, 90, 390, 400, K.etl, si.SiApacheairflow, "airflow", "2.10.5 · :8081", { fill: K.soft, logo: [si.SiApacheairflow, "#017CEE"] });
t(403, 158, "DAG bank_regional_daily", { size: 15, weight: 700, fill: K.ink, mono: true });
const tasks = ["load_bot", "load_dopa", "load_nesdc", "load_worldbank_api", "load_bot_policy_workbook"];
tasks.forEach((n, i) => {
  const y = 176 + i * 38;
  box(403, y, 236, 28, { fill: K.white, rx: 14 });
  t(418, y + 19, n, { size: 12.5, fill: K.text, mono: true });
  arrow(`M639,${y + 14} H660 V${290} H676`, { width: 1.2 });
});
box(678, 276, 86, 28, { fill: K.white, stroke: K.app, rx: 14 });
t(721, 295, "build_mart", { size: 12, fill: K.app, mono: true, anchor: "middle" });
t(403, 386, "cron 0 7 * * *  Asia/Bangkok", { size: 13, fill: K.text, mono: true });
t(403, 406, "catchup=False · max_active_runs=1", { size: 13, fill: K.muted, mono: true });
t(403, 426, "retries=2 · retry_delay=5 min", { size: 13, fill: K.muted, mono: true });
t(403, 452, "PythonOperator → urllib POST, 240 s", { size: 13, fill: K.muted });
t(403, 472, "metadata DB: postgres / airflow", { size: 13, fill: K.muted });

// ---------------------------------------------------------------- web container
group(385, 520, 390, 490, K.web, fa.FaDesktop, "web", "Next.js · :3000", { fill: K.soft, logo: [si.SiNextdotjs, "#000000"] });
t(403, 590, "App Router pages (TypeScript, Recharts)", { size: 13.5, weight: 600, fill: K.ink });
["/", "/provinces", "/assistant", "/questions", "/sources"].forEach((p, i) => {
  const x = 403 + (i % 3) * 120, y = 604 + Math.floor(i / 3) * 36;
  box(x, y, 110, 28, { fill: K.white, rx: 4 });
  t(x + 55, y + 19, p, { size: 13, fill: K.web, mono: true, anchor: "middle" });
});
t(403, 698, "lib/data.ts → fetch('/api/…', no-store)", { size: 13, fill: K.muted, mono: true });
arrow("M580,708 V734", { width: 1.4 });
codeBox(403, 738, 354, 254, "app/api/[...path]/route.ts", [
  ["Backend-for-frontend proxy", true],
  "GET  metadata|overview|",
  "     provinces[/{n}/history]|",
  "     comparison|sources|",
  "     questions[/CQnn]",
  "POST chat  ≤6 KB body",
  "     question ≤1000, session ≤100",
  "timeout 15 s · chat 90 s",
  ["anything else → 404 (ETL never proxied)", true],
], { stroke: K.web });

// ---------------------------------------------------------------- api container
group(805, 90, 1200, 920, K.app, fa.FaServer, "api", "uvicorn bank.api:app · :8000", { fill: K.soft, logo: [si.SiFastapi, "#009688"] });

// ETL handlers
group(830, 145, 1150, 330, K.etl, fa.FaGears, "ETL handlers", "bank/etl.py · bank/sources.py", { dash: "6 4", fill: K.white });
const etl = [
  ["POST /etl/{job}", ["X-ETL-Token header", "== ETL_API_TOKEN", "job ∈ bot|dopa|nesdc|", "  worldbank|policy|mart", ["else 403 / 404", true]]],
  ["sources.fetch_*()", ["requests · HTTPS", "fetch_bot / fetch_dopa", "fetch_nesdc", "fetch_world_bank", "fetch_policy_events"]],
  ["_save_raw()", ["data/raw/<source>/", "  <sha256>.<ext>", ["volume ./data:/app/data", true], ["content-addressed", true]]],
  ["provinces.py", ["BOT_TO_CODE", "NESDC_ALIASES", ["unknown alias → fail", true], ["(no fuzzy match)", true]]],
  ["etl.run_source()", ["one transaction:", "replace source facts", "+ source_manifest", "+ etl_run"]],
];
etl.forEach(([title, lines], i) => {
  const x = 848 + i * 226;
  codeBox(x, 190, 206, 170, title, lines);
  if (i < etl.length - 1) arrow(`M${x + 206},270 H${x + 224}`, { width: 1.4 });
});
codeBox(1300, 372, 662, 92, "job = mart → etl.build_mart() · as-of joins into mart_province_month", [
  ["population: latest registry year, from Jan of the next year · GPP: Last-Modified ≤ month-end", true],
  ["inflation: prior year, lastupdated ≤ month-end · policy: latest decision ≤ month-end", true],
], { stroke: K.app });

// Read endpoints
group(830, 495, 420, 495, K.app, fa.FaListUl, "Read endpoints", "bank/api.py", { dash: "6 4", fill: K.white });
const routes = [
  ["GET", "/overview  /metadata", "analytics.overview_data()"],
  ["GET", "/provinces", "analytics.snapshot()"],
  ["GET", "/provinces/{code}/history", "analytics.province_history()"],
  ["GET", "/comparison?codes=", "≤4 provinces, mart rows"],
  ["GET", "/sources", "analytics.source_data()"],
  ["GET", "/questions[/{qid}]", "competency.run_question()"],
  ["GET", "/health", "months loaded, latest period"],
  ["POST", "/chat", "chat.ask(question, session_id)"],
];
routes.forEach(([m, p, h], i) => {
  const y = 560 + i * 44;
  method(848, y, m);
  t(904, y, p, { size: 13.5, fill: K.ink, mono: true });
  t(904, y + 18, h, { size: 12.5, fill: K.muted, mono: true });
});
box(848, 916, 384, 60, { fill: K.panel, stroke: "#E1E6EA" });
t(862, 940, "analytics.read() / run_question():", { size: 12.5, fill: K.ink, mono: true });
t(862, 962, "SET TRANSACTION READ ONLY · 10 s", { size: 12.5, fill: K.muted, mono: true });

// Chat graph
group(1270, 495, 710, 495, K.chat, fa.FaDiagramProject, "Chat graph", "LangGraph StateGraph · bank/chat.py", { dash: "6 4", fill: K.white, logo: [si.SiLangchain, "#1C3C3C"] });
arrow("M1150,868 H1268");
const nodes = [
  ["conversation", ["route_conversation", "ConversationDecision", "fallback_route", ["no key: narrow rules", true]]],
  ["plan", ["safety_check", "rules_plan (v3)", "_llm_decision", "PlannerDecision"]],
  ["execute", ["compile_query", "_validate_query", "SQLGlot: mart only", "execute_plan"]],
  ["answer", [["deterministic text", true], ["rows · units · SQL", true], ["provenance · chart", true], ["clarify choices", true]]],
];
t(1288, 568, "START", { size: 12.5, weight: 700, fill: K.muted, mono: true });
arrow("M1308,576 V604", { width: 1.4 });
nodes.forEach(([n, lines], i) => {
  const x = 1288 + i * 172;
  codeBox(x, 608, 156, 140, n, lines, { stroke: K.chat, titleFill: K.chat, lineSize: 12 });
  if (i < nodes.length - 1) arrow(`M${x + 156},680 H${x + 170}`, { width: 1.4 });
});
t(1876, 778, "END", { size: 12.5, weight: 700, fill: K.muted, mono: true, anchor: "middle" });
arrow("M1876,748 V764", { width: 1.4 });
// conditional edges that skip ahead to answer
arrow("M1366,608 V590 H1890 V606", { width: 1.3, dash: "5 4" });
tag(1560, 590, "guide · explain · present · refuse → answer", K.chat);
arrow("M1538,748 V770 H1830 V750", { width: 1.3, dash: "5 4" });
tag(1700, 770, "clarify · unsupported · error", K.chat);
box(1288, 800, 674, 172, { fill: K.panel, stroke: "#E1E6EA" });
t(1302, 826, "Guards and state", { size: 14, weight: 700, fill: K.ink });
[
  "QueryPlan (Pydantic) is the only LLM output that reaches SQL; SQL comes from an allowlisted compiler",
  "SQLGlot: one SELECT, only table mart_province_month (CTEs allowed) · READ ONLY · 10 s",
  "PostgresSaver checkpointer, thread = session_id: confirmed context, last result, pending choices",
  "observability.record(): latency and token telemetry, no keys, questions or session IDs",
  "Provider errors map to bounded public codes; exception strings are never returned",
].forEach((s, i) => t(1302, 850 + i * 24, "• " + s, { size: 12.5, fill: K.muted }));

// ---------------------------------------------------------------- data row
group(385, 1050, 210, 410, K.grafana, si.SiGrafana, "grafana", "11.6.3", { fill: K.soft });
icon(si.SiGrafana, 455, 1112, 66, "#F46800");
t(490, 1212, "13 provisioned panels", { size: 13.5, weight: 600, fill: K.ink, anchor: "middle" });
t(490, 1236, "regional-banking.json", { size: 12.5, fill: K.muted, mono: true, anchor: "middle" });
t(490, 1272, "datasource", { size: 12.5, fill: K.muted, anchor: "middle" });
t(490, 1292, "bank-postgres", { size: 12.5, fill: K.muted, mono: true, anchor: "middle" });
t(490, 1312, "user bank_reader", { size: 12.5, fill: K.reader, mono: true, anchor: "middle" });

group(625, 1050, 1380, 410, K.data, si.SiPostgresql, "postgres", "17-alpine · :5433 → 5432", { fill: K.soft, logo: [si.SiPostgresql, "#4169E1"] });
codeBox(645, 1110, 170, 330, "DB airflow", ["dag / task runs", "scheduler state", "", ["owner: airflow", true], ["written only by the", true], ["airflow container", true]], { fill: K.white });
box(835, 1110, 1150, 330, { fill: K.white, stroke: "#9FB4CC" });
add(`<rect x="835" y="1110" width="1150" height="36" rx="6" fill="#E6EEF6"/>`);
t(851, 1134, "DB bank", { size: 15, weight: 700, fill: K.ink });
t(930, 1134, "SQLAlchemy Core tables (bank/db.py) · primary keys, no FK constraints", { size: 13, fill: K.muted });
const tables = [
  ["mart", ["mart_province_month", "PK province_code+period", "18 columns: balances,", "ratios, reference years,", "policy rate"], K.web],
  ["dimensions", ["dim_province", "dim_month"], K.data],
  ["source facts", ["fact_bank_month", "fact_population_year", "fact_gpp_year", "fact_macro_year", "fact_policy_event", "+ source_sha256"], K.data],
  ["ETL metadata", ["source_manifest", "etl_run"], K.etl],
  ["LangGraph", ["checkpoints", "checkpoint_blobs", "checkpoint_writes"], K.chat],
];
tables.forEach(([h, rows, c], i) => {
  const x = 851 + i * 226;
  codeBox(x, 1160, 210, 200, h, rows, { titleFill: c, stroke: c === K.web ? K.web : "#C5CED6", fill: c === K.web ? "#EEF2F8" : K.white });
});
add(`<rect x="851" y="1376" width="1118" height="52" rx="6" fill="${K.panel}"/>`);
add(`<rect x="866" y="1390" width="22" height="6" fill="${K.owner}"/>`);
t(898, 1398, "role bank (owner): ETL writes, mart rebuild, LangGraph checkpoints", { size: 13, fill: K.ink });
add(`<rect x="866" y="1410" width="22" height="6" fill="${K.reader}"/>`);
t(898, 1418, "role bank_reader: SELECT only (db/bootstrap.sql) — API reads, chat SQL, Grafana", { size: 13, fill: K.ink });

// ================================================================== connections
// clients
arrow("M330,690 H383", { both: true });
tag(357, 668, "HTTP");
// web proxy -> api
arrow("M757,868 H828", { both: true });
tag(792, 846, "API_BASE_URL");
tag(792, 892, "http://api:8000");
// airflow -> etl
arrow("M775,230 H846");
tag(838, 206, "POST /etl/{job}", K.muted, "end");
tag(838, 256, "X-ETL-Token", K.muted, "end");
// sources -> fetch (outbound HTTPS from the api container), via the corridors between groups
arrow("M330,505 H818 V484 H1177 V362", { color: K.app });
tag(565, 505, "HTTPS · requests.get / form POST", K.app);
// read endpoints -> DB bank (bank_reader)
arrow("M1040,990 V1108", { color: K.reader, both: true });
tag(1040, 1028, "bank_reader · SELECT mart", K.reader);
// etl -> DB bank (owner)
arrow("M1260,475 V485 H1255 V1108", { color: K.owner });
tag(1255, 1028, "bank · INSERT / replace", K.owner);
// chat -> DB bank
arrow("M1620,990 V1108", { color: K.reader, both: true });
tag(1620, 1028, "bank_reader · SELECT", K.reader);
arrow("M1900,990 V1108", { color: K.owner, both: true });
tag(1900, 1028, "bank · checkpoints", K.owner);
// grafana -> DB bank
arrow("M595,1250 H623", { color: K.reader, both: true });

// ================================================================== right column
group(2065, 90, 315, 400, K.ext, fa.FaCloud, "External LLM", "", { dash: "7 5" });
icon(si.SiGooglegemini, 2090, 150, 46, "#8E75B2");
t(2148, 170, "Google Gemini API", { size: 15, weight: 700, fill: K.ink });
t(2148, 190, "langchain-google-genai", { size: 12.5, fill: K.muted, mono: true });
[
  "model gemini-2.5-flash",
  "temperature 0 · timeout 20 s",
  "max_retries ≤ 1 (default 0)",
  "with_structured_output(",
  "  ConversationDecision |",
  "  PlannerDecision)",
].forEach((s, i) => t(2090, 232 + i * 20, s, { size: 12.5, fill: K.text, mono: true }));
box(2085, 372, 275, 100, { fill: K.panel, stroke: "#E1E6EA", dash: "4 3" });
icon(si.SiOpenai, 2097, 386, 26, "#000000");
t(2132, 404, "OpenAI (optional)", { size: 14, weight: 700, fill: K.ink });
t(2097, 430, "OPENAI_MODEL gpt-4.1-mini", { size: 12.5, fill: K.muted, mono: true });
t(2097, 452, "configured but untested live", { size: 12.5, fill: K.muted });
arrow("M1980,680 H2040 V300 H2063", { color: K.ext, dash: "6 4", both: true });
tag(2022, 640, "HTTPS", K.ext);

add(`<rect x="2065" y="520" width="315" height="490" fill="${K.panel}" stroke="#D5DBDB"/>`);
t(2083, 552, "Legend", { size: 16, weight: 700, fill: K.ink });
const legend = [
  [K.ink, "", "HTTP request / response"],
  [K.app, "", "Outbound fetch of public data"],
  [K.reader, "", "PostgreSQL as bank_reader (SELECT)"],
  [K.owner, "", "PostgreSQL as bank (owner)"],
  [K.ext, "6 4", "External LLM call (HTTPS)"],
  [K.ink, "5 4", "Conditional graph edge"],
];
legend.forEach(([c, d, s], i) => {
  const y = 586 + i * 34;
  add(`<path d="M2083,${y} H2123" stroke="${c}" stroke-width="2.4"${d ? ` stroke-dasharray="${d}"` : ""}/>`);
  t(2133, y + 5, s, { size: 13, fill: K.text });
});
method(2083, 806, "GET");
t(2139, 806, "read route", { size: 13, fill: K.text });
method(2083, 838, "POST");
t(2139, 838, "write / chat route", { size: 13, fill: K.text });
t(2083, 880, "Monospace = real file, function,", { size: 13, fill: K.muted });
t(2083, 899, "route or table name in the repo.", { size: 13, fill: K.muted });
t(2083, 930, "Credentials shown in compose.yaml", { size: 13, fill: K.muted });
t(2083, 949, "are local development defaults.", { size: 13, fill: K.muted });

add(`<rect x="2065" y="1050" width="315" height="410" fill="${K.panel}" stroke="#D5DBDB"/>`);
t(2083, 1082, "Guardrails", { size: 16, weight: 700, fill: K.ink });
[
  ["Network", "all ports on 127.0.0.1"],
  ["Proxy", "regex allowlist, ETL never proxied"],
  ["ETL", "shared token header"],
  ["Database", "separate read-only role"],
  ["SQL", "SQLGlot, single table, READ ONLY"],
  ["Time", "10 s SQL · 20 s LLM · 90 s chat"],
  ["Lineage", "SHA-256 on raw files and facts"],
].forEach(([h, s], i) => {
  const y = 1118 + i * 46;
  icon(fa.FaShieldHalved, 2083, y - 14, 18, K.app);
  t(2110, y, h, { size: 13.5, weight: 700, fill: K.ink });
  t(2110, y + 19, s, { size: 12.5, fill: K.muted });
});

// ================================================================== assemble + render
const mk = (id, c) => `<marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
<defs>${mk("ah", K.ink)}${mk("ar", K.reader)}${mk("ao", K.owner)}${mk("ae", K.ext)}${mk("ag", K.app)}</defs>
<rect width="${W}" height="${H}" fill="${K.white}"/>
${parts.join("\n")}
</svg>`;

function findChromium() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = path.join(process.env.LOCALAPPDATA || "", "ms-playwright");
  if (!fs.existsSync(base)) return undefined;
  for (const d of fs.readdirSync(base).filter((n) => /^chromium-\d+$/.test(n)).sort().reverse()) {
    const exe = path.join(base, d, "chrome-win64", "chrome.exe");
    if (fs.existsSync(exe)) return exe;
  }
  return undefined;
}

async function main() {
  fs.writeFileSync(OUT_SVG, svg);
  const { chromium } = require(path.join(ROOT, "frontend", "node_modules", "playwright-core"));
  const browser = await chromium.launch({ executablePath: findChromium() });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await page.screenshot({ path: OUT_PNG, clip: { x: 0, y: 0, width: W, height: H } });
  await browser.close();
  console.log("wrote", OUT_SVG, "and", OUT_PNG);
}
main().catch((e) => { console.error(e); process.exit(1); });
