// Renders the high-level system architecture diagram (reference-architecture style).
//   node architecture.js  ->  docs/design/system-architecture.svg and .png (3840x2160)
// Product logos come from Simple Icons via react-icons; rendering uses Playwright's Chromium.

const path = require("path");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const si = require("react-icons/si");
const fa = require("react-icons/fa6");

const { ROOT, renderSvg } = require("./lib/render");
const OUT_SVG = path.join(ROOT, "docs", "design", "system-architecture.svg");
const OUT_PNG = path.join(ROOT, "docs", "design", "system-architecture.png");

const K = {
  ink: "#16191F", text: "#232F3E", muted: "#545B64", line: "#879196", white: "#FFFFFF",
  host: "#01A88D", web: "#14264A", app: "#0B7A5C", chat: "#ED7100", data: "#336791",
  etl: "#7D8998", ext: "#8C4FFF", badge: "#232F3E", tierFill: "#F2F8FC",
};
const BRAND = {
  postgres: [si.SiPostgresql, "#4169E1"], airflow: [si.SiApacheairflow, "#017CEE"], fastapi: [si.SiFastapi, "#009688"],
  next: [si.SiNextdotjs, "#000000"], grafana: [si.SiGrafana, "#F46800"], python: [si.SiPython, "#3776AB"],
  docker: [si.SiDocker, "#2496ED"], gemini: [si.SiGooglegemini, "#8E75B2"], langchain: [si.SiLangchain, "#1C3C3C"],
  pydantic: [si.SiPydantic, "#E92063"], sqlalchemy: [si.SiSqlalchemy, "#D71F00"],
};
const FONT = "'Segoe UI', Arial, sans-serif";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const parts = [];
const add = (s) => parts.push(s);

// Place a react-icon as a nested <svg> at (x, y) with the given size and color.
function icon(Icon, x, y, size, color) {
  const svg = renderToStaticMarkup(React.createElement(Icon, { size, color }));
  add(svg.replace("<svg ", `<svg x="${x}" y="${y}" `));
}
function t(x, y, s, { size = 14, weight = 400, fill = K.text, anchor = "start", italic = false } = {}) {
  add(`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"${italic ? ' font-style="italic"' : ""}>${esc(s)}</text>`);
}
// Boundary group with a solid corner badge, like cloud reference diagrams.
function group(x, y, w, h, color, Icon, title, sub, { dash = "", fill = "none" } = {}) {
  add(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${color}" stroke-width="1.8"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`);
  add(`<rect x="${x}" y="${y}" width="40" height="40" fill="${color}"/>`);
  icon(Icon, x + 9, y + 9, 22, K.white);
  t(x + 52, y + 27, title, { size: 19, weight: 600, fill: K.ink });
  if (sub) t(x + 52 + title.length * 10 + 12, y + 27, sub, { size: 16, fill: K.muted, italic: true });
}
// Service: icon centred above a bold label and grey detail lines.
function service(cx, y, Icon, color, label, lines = [], size = 50) {
  icon(Icon, cx - size / 2, y, size, color);
  t(cx, y + size + 24, label, { size: 16, weight: 600, fill: K.ink, anchor: "middle" });
  lines.forEach((l, i) => t(cx, y + size + 45 + i * 19, l, { size: 14, fill: K.muted, anchor: "middle" }));
}
function brand(cx, y, key, label, lines, size) {
  const [Icon, color] = BRAND[key];
  service(cx, y, Icon, color, label, lines, size);
}
function arrow(d, { both = false, dash = "", color = K.ink } = {}) {
  add(`<path d="${d}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linejoin="round"${dash ? ` stroke-dasharray="${dash}"` : ""} marker-end="url(#ah)"${both ? ' marker-start="url(#ah)"' : ""}/>`);
}
// Two sequences: lettered (teal) for the scheduled pipeline, numbered (blue) for a user request.
const PIPE = "#01A88D", REQ = "#336791";
function step(n, x, y) {
  add(`<rect x="${x - 15}" y="${y - 15}" width="30" height="30" rx="4" fill="${/[A-Z]/.test(n) ? PIPE : REQ}"/>`);
  t(x, y + 6, String(n), { size: 16, weight: 700, fill: K.white, anchor: "middle" });
}
function tag(x, y, s) {
  const w = s.length * 7.4 + 14;
  add(`<rect x="${x - w / 2}" y="${y - 13}" width="${w}" height="20" rx="3" fill="${K.white}"/>`);
  t(x, y + 2, s, { size: 13, fill: K.muted, anchor: "middle" });
}

// ------------------------------------------------------------------ external actors (left)
service(150, 110, fa.FaUsers, K.text, "Market analysts", ["strategy & channel teams"], 60);

group(30, 560, 270, 470, K.etl, fa.FaBuildingColumns, "Public data sources", "", { dash: "7 5" });
const src = [
  [fa.FaBuildingColumns, "BOT · FI_CB_011_S5", "loans · deposits · branches"],
  [fa.FaIdCard, "DOPA", "registered population"],
  [fa.FaChartLine, "NESDC", "provincial GPP"],
  [fa.FaGlobe, "World Bank API", "national inflation"],
  [fa.FaPercent, "BOT · MPC", "policy-rate decisions"],
];
src.forEach(([I, a, b], i) => {
  const y = 628 + i * 78;
  add(`<rect x="48" y="${y - 6}" width="44" height="44" rx="6" fill="#EEF1F4"/>`);
  icon(I, 58, y + 4, 24, K.text);
  t(104, y + 13, a, { size: 15, weight: 600, fill: K.ink });
  t(104, y + 33, b, { size: 13.5, fill: K.muted });
});

// ------------------------------------------------------------------ host boundary
group(330, 30, 1280, 1020, K.host, BRAND.docker[0], "Docker Compose host", "ports bound to 127.0.0.1", { dash: "8 6" });

// Web tier
group(360, 100, 280, 380, K.web, fa.FaDesktop, "Web tier", "", { fill: K.tierFill });
brand(500, 158, "next", "Next.js application", ["5 pages · charts · CSV"], 54);
arrow("M500,280 V318");
service(500, 324, fa.FaShieldHalved, K.web, "/api/* proxy", ["same-origin, allowlisted", "server-side API URL"], 46);
arrow("M212,192 H470", { both: true });
step("1", 300, 164);

// Reporting
group(360, 600, 280, 150, "#F46800", fa.FaChartColumn, "Reporting", "");
brand(500, 648, "grafana", "Grafana 11", ["13 provisioned panels"], 38);

// Application tier
group(680, 100, 900, 380, K.app, fa.FaServer, "Application tier", "FastAPI", { fill: K.tierFill });
brand(800, 165, "fastapi", "Analytics API", ["dashboard pages", "business questions"], 54);
group(920, 150, 640, 240, K.chat, fa.FaComments, "Chat workflow", "LangGraph", { dash: "7 5", fill: K.white });
const chat = [
  [fa.FaRoute, K.chat, "Router", ["safety gate", "intent"]],
  [BRAND.langchain[0], BRAND.langchain[1], "Planner", ["Thai rules →", "LLM fallback"]],
  [BRAND.pydantic[0], BRAND.pydantic[1], "Validate", ["QueryPlan", "Pydantic"]],
  [fa.FaCode, K.text, "Compile", ["allowlisted SQL", "SQLGlot"]],
  [BRAND.sqlalchemy[0], BRAND.sqlalchemy[1], "Execute", ["read-only", "with provenance"]],
];
chat.forEach(([I, c, a, l], i) => {
  const cx = 1000 + i * 122;
  service(cx, 222, I, c, a, l, 44);
  if (i < chat.length - 1) arrow(`M${cx + 28},244 H${cx + 92}`);
});
step("4", 952, 244);

// External LLM (called by router and planner)
group(1650, 150, 250, 270, K.ext, fa.FaCloud, "External service", "");
brand(1775, 218, "gemini", "Google Gemini API", ["intent routing", "structured QueryPlan", "never writes SQL"], 54);
arrow("M1560,262 H1648", { both: true, dash: "6 4", color: K.ext });

// Proxy -> application tier
arrow("M548,348 H678", { both: true });
step("2", 613, 320);

// Data tier: facts and dimensions feed the mart; operational tables sit to the right.
group(680, 520, 900, 230, K.data, BRAND.postgres[0], "Data tier", "PostgreSQL 17", { fill: K.tierFill });
const data = [
  [770, fa.FaTableCells, K.data, "Dimensions", ["province (77)", "month (25)"]],
  [975, fa.FaCubes, BRAND.postgres[1], "Province–month mart", ["1,925 rows", "ratios + ref. years"]],
  [1180, fa.FaLayerGroup, K.data, "Source facts", ["bank · population", "GPP · macro · policy"]],
  [1372, fa.FaClockRotateLeft, K.chat, "Checkpoints", ["chat session state"]],
  [1500, fa.FaListCheck, K.etl, "ETL metadata", ["manifest · runs"]],
];
data.forEach(([cx, I, c, a, l]) => service(cx, 574, I, c, a, l, 44));
arrow("M796,596 H945");
arrow("M1154,596 H1005");
add(`<path d="M1280,580 V720" stroke="#C5CED6" stroke-width="1.4" stroke-dasharray="4 4"/>`);

// Application <-> data
arrow("M800,340 V470 H955 V572", { both: true });
step("3", 800, 410);
arrow("M1035,390 V572", { both: true });
tag(1035, 460, "SELECT");
step("5", 1084, 460);
arrow("M1372,390 V572", { both: true });
tag(1372, 460, "state");

// Reporting <-> data
arrow("M640,675 H678", { both: true });
step("6", 659, 640);

// Ingestion pipeline
group(360, 790, 1220, 240, K.etl, BRAND.airflow[0], "Ingestion pipeline", "daily 07:00 Asia/Bangkok", { dash: "7 5" });
const etl = [
  ["airflow", "Apache Airflow", ["5 load tasks", "2 retries"]],
  ["fastapi", "ETL endpoints", ["protected, not proxied"]],
  [fa.FaBoxArchive, "Raw snapshots", ["SHA-256 named", "immutable"]],
  ["python", "Source adapters", ["mapping · units", "coverage · as-of"]],
  [fa.FaDatabase, "Transactional load", ["replace facts", "rebuild mart"]],
];
etl.forEach(([k, a, l], i) => {
  const cx = 480 + i * 245;
  if (typeof k === "string") brand(cx, 848, k, a, l, 46);
  else service(cx, 848, k, i === 2 ? K.text : BRAND.postgres[1], a, l, 46);
  if (i < etl.length - 1) arrow(`M${cx + 34},871 H${cx + 211}`, { dash: i === 0 ? "6 4" : "" });
});
step("A", 602, 846);
arrow("M300,1008 H970 V990");
tag(640, 1008, "HTTPS · files · REST API");
step("B", 330, 982);
step("C", 1092, 846);
arrow("M1460,848 V772 H1180 V752");
tag(1330, 772, "load facts");
step("D", 1488, 808);

// ------------------------------------------------------------------ flow key (right)
add(`<rect x="1650" y="460" width="250" height="570" fill="#F7F8F9" stroke="#D5DBDB"/>`);
const sections = [
  ["Data pipeline (daily)", PIPE, [["A", "Airflow starts the run"], ["B", "Fetch 5 public sources"], ["C", "Snapshot, then validate"], ["D", "Load facts, rebuild mart"]]],
  ["User request", REQ, [["1", "Analyst opens the app"], ["2", "Proxy forwards /api/*"], ["3", "Dashboard reads the mart"], ["4", "Router + planner (Gemini)"], ["5", "Read-only SQL, checkpoint"], ["6", "Grafana reads the mart"]]],
];
let ky = 498;
sections.forEach(([h, c, rows]) => {
  t(1668, ky, h, { size: 16, weight: 700, fill: c });
  ky += 34;
  rows.forEach(([n, s]) => { step(n, 1684, ky); t(1710, ky + 5, s, { size: 14, fill: K.text }); ky += 44; });
  ky += 16;
});

// ------------------------------------------------------------------ assemble
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" font-family="${FONT}">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${K.ink}"/></marker></defs>
<rect width="1920" height="1080" fill="${K.white}"/>
${parts.join("\n")}
</svg>`;

renderSvg(svg, 1920, 1080, OUT_SVG, OUT_PNG).catch((e) => { console.error(e); process.exit(1); });
