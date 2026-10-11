// Builds output/presentation/Thailand-Regional-Banking-Intelligence.pptx.
// Every figure on the result slides is read from docs/evidence/competency-results.json,
// so re-exporting the competency evidence and re-running this script keeps the deck in sync.
//
//   cd tools/presentation && npm install && npm run build

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const { applyTheme } = require("./lib/apply_theme");

const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "output", "presentation", "Thailand-Regional-Banking-Intelligence.pptx");
const ASSETS = path.join(__dirname, "assets");
const evidence = JSON.parse(fs.readFileSync(path.join(ROOT, "docs", "evidence", "competency-results.json"), "utf8"));
const R = evidence.results;

// ---------------------------------------------------------------- theme
const HEX = {
  ink: "1A2233", white: "FFFFFF", navy: "14264A", tint: "EEF4F1",
  green: "0B7A5C", navy2: "2E4A7A", amber: "C77D02", slate: "5B6878", mint: "6CC4A4", line: "D5DDE5",
};
const THEME = {
  name: "Bank Intelligence",
  headFontFace: "Leelawadee UI",
  bodyFontFace: "Leelawadee UI",
  colors: {
    dk1: HEX.ink, lt1: HEX.white, dk2: HEX.navy, lt2: HEX.tint,
    accent1: HEX.green, accent2: HEX.navy2, accent3: HEX.amber, accent4: HEX.slate,
    accent5: HEX.mint, accent6: HEX.line, hlink: HEX.green, folHlink: HEX.navy,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Thailand Regional Banking Intelligence";
pres.subject = "Provincial banking market screening from public data";
pres.author = "anupat2046";
pres.company = "Thailand Regional Banking Intelligence";
const C = pres.SchemeColor;

const W = 13.333, M = 0.6, CW = W - 2 * M, TOP = 1.95;

// ---------------------------------------------------------------- formatting helpers
const nf = (v, d = 0) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const TH_MONTH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
const thMonth = (iso) => {
  const [y, m] = iso.split("-").map(Number);
  return `${TH_MONTH[m - 1]} ${String(y + 543).slice(2)}`;
};
const shortName = (n) => (n === "กรุงเทพมหานคร" ? "กรุงเทพฯ" : n === "พระนครศรีอยุธยา" ? "อยุธยา" : n);

// ---------------------------------------------------------------- icons
async function icon(Icon, hex = HEX.white) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { size: 256, color: "#" + hex }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const ICONS = {};
async function loadIcons() {
  const want = {
    bank: fa.FaBuildingColumns, users: fa.FaUsers, question: fa.FaCircleQuestion, scale: fa.FaScaleUnbalanced,
    db: fa.FaDatabase, gear: fa.FaGears, api: fa.FaServer, chart: fa.FaChartColumn, robot: fa.FaRobot,
    cloud: fa.FaCloudArrowDown, link: fa.FaLink, clock: fa.FaClock, layers: fa.FaLayerGroup,
    check: fa.FaCircleCheck, shield: fa.FaShieldHalved, code: fa.FaCode, map: fa.FaMapLocationDot,
    user: fa.FaIdCard, branch: fa.FaShop, calendar: fa.FaCalendarDays, globe: fa.FaGlobe, comments: fa.FaComments,
    filter: fa.FaFilter, flask: fa.FaFlask, route: fa.FaRoute, lock: fa.FaLock, eye: fa.FaMagnifyingGlassChart,
    coins: fa.FaCoins, list: fa.FaListCheck, arrow: fa.FaArrowRight,
  };
  for (const [k, Icon] of Object.entries(want)) {
    ICONS[k] = await icon(Icon, HEX.white);
    ICONS[k + "_g"] = await icon(Icon, HEX.green);
  }
}

// ---------------------------------------------------------------- layouts
const FOOTER = { x: M, y: 7.0, w: 7, h: 0.28, fontSize: 9, color: C.accent4, margin: 0 };
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.72, w: CW, h: 1.05, fontSize: 24, bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    { text: { text: "Thailand Regional Banking Intelligence", options: FOOTER } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.28, fontSize: 9, color: HEX.slate, align: "right" },
});
pres.defineSlideMaster({
  title: "APPENDIX",
  background: { color: HEX.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.72, w: CW, h: 1.05, fontSize: 24, bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    { text: { text: "Appendix · สำหรับตอบคำถาม", options: FOOTER } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.28, fontSize: 9, color: HEX.slate, align: "right" },
});
pres.defineSlideMaster({ title: "DARK", background: { color: HEX.navy }, objects: [] });

// ---------------------------------------------------------------- composition helpers
function contentSlide(section, kicker, title, master = "CONTENT") {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(kicker, { x: M, y: 0.38, w: CW, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1, margin: 0, isTextBox: true, objectName: "Kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function card(s, x, y, w, h, fill = C.background2, name = "Card") {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.08, objectName: name });
}
function iconCircle(s, key, x, y, d = 0.6, fill = C.accent1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: "Icon circle" });
  const p = d * 0.25;
  s.addImage({ data: ICONS[key], x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: key, objectName: "Icon" });
}
function text(s, t, o) {
  s.addText(t, { margin: 0, isTextBox: true, color: C.text1, fontSize: 14, valign: "top", ...o });
}
function note(s, t, y = 6.55) {
  text(s, t, { x: M, y, w: CW, h: 0.35, fontSize: 11, color: C.accent4, objectName: "Source note" });
}
function shadow() {
  return { type: "outer", color: "000000", opacity: 0.16, blur: 10, offset: 3, angle: 90 };
}
function chartStyle(extra = {}) {
  return {
    catAxisLabelColor: HEX.slate, valAxisLabelColor: HEX.slate,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
    legendFontFace: "+mn-lt", titleFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, dataLabelFontSize: 11, legendFontSize: 11,
    dataLabelColor: HEX.ink, titleColor: HEX.ink, titleFontSize: 13,
    valGridLine: { color: "E3E8EE", size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineColor: HEX.line, valAxisLineShow: false,
    ...extra,
  };
}
function table(s, rows, o) {
  const head = rows[0].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }));
  const body = rows.slice(1).map((r, i) => r.map((t) => ({ text: String(t), options: { fill: { color: i % 2 ? C.background2 : C.background1 } } })));
  s.addTable([head, ...body], {
    fontSize: 12, color: C.text1, border: { type: "solid", pt: 0.75, color: HEX.line }, valign: "middle",
    margin: [0.06, 0.1, 0.06, 0.1], autoPage: false, ...o,
  });
}

// ---------------------------------------------------------------- derived figures
const snap = evidence.snapshot;
const cq05 = R.CQ05;
const lastM = cq05[cq05.length - 1], yearAgo = cq05[cq05.length - 13];
const loanYoy = (100 * (lastM.credits_million - yearAgo.credits_million)) / yearAgo.credits_million;
const depYoy = (100 * (lastM.deposits_million - yearAgo.deposits_million)) / yearAgo.deposits_million;
const rateCuts = cq05.filter((r, i) => i > 0 && r.policy_rate_pct < cq05[i - 1].policy_rate_pct).length;
const cq10 = R.CQ10[0];
const shortlist = R.CQ07.map((r) => ({ ...r, ratio: (100 * r.credits_million_baht) / r.gpp_million_baht })).sort((a, b) => a.ratio - b.ratio);
const pair = R.CQ04[0];
const pairGap = pair.gpp_gap_pct;

async function build() {
  await loadIcons();

  // ============================================================ 1 Cover
  pres.addSection({ title: "Introduction" });
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Introduction" });
    text(s, "DATA MODEL  ·  ANALYTICS  ·  AI ASSISTANT", { x: M, y: 0.75, w: 6.5, h: 0.35, fontSize: 13, bold: true, color: C.accent5, charSpacing: 1 });
    text(s, "Thailand Regional\nBanking Intelligence", { x: M, y: 1.3, w: 6.6, h: 1.75, fontSize: 40, bold: true, color: C.background1, fontFace: THEME.headFontFace, lineSpacingMultiple: 0.95 });
    text(s, "ระบบคัดกรองตลาดธนาคารรายจังหวัด จากข้อมูลสาธารณะที่ตรวจสอบที่มาได้", { x: M, y: 3.2, w: 6.3, h: 0.9, fontSize: 18, color: C.accent5 });
    const stats = [[String(snap.provinces), "จังหวัด"], [String(snap.months), "เดือน"], ["5", "แหล่งข้อมูล"], ["10", "คำถามธุรกิจ"]];
    stats.forEach(([v, l], i) => {
      text(s, v, { x: M + i * 1.55, y: 4.45, w: 1.45, h: 0.65, fontSize: 32, bold: true, color: C.background1 });
      text(s, l, { x: M + i * 1.55, y: 5.1, w: 1.45, h: 0.35, fontSize: 13, color: C.accent6 });
    });
    text(s, `ข้อมูลธนาคาร ${thMonth(snap.first_period)} – ${thMonth(snap.latest_period)}  ·  ผล Query ณ 10 ต.ค. 2569`, { x: M, y: 6.35, w: 6.5, h: 0.35, fontSize: 12, color: C.accent6 });
    s.addImage({ path: path.join(ASSETS, "overview.png"), x: 7.25, y: 1.55, w: 5.5, h: 5.5 * 735 / 1245, altText: "หน้าภาพรวมตลาดของแอปพลิเคชัน", shadow: shadow(), objectName: "Dashboard screenshot" });
    text(s, "หน้าภาพรวมตลาดใน Next.js Dashboard", { x: 7.25, y: 1.55 + 5.5 * 735 / 1245 + 0.15, w: 5.5, h: 0.3, fontSize: 11, color: C.accent6 });
    s.addNotes([
      "เปิด: โปรเจกต์นี้ตอบคำถามว่า ถ้าทีมกลยุทธ์ธนาคารต้องเลือกจังหวัดเพื่อศึกษาตลาดต่อ ควรดูข้อมูลอะไร และจะเทียบจังหวัดอย่างเป็นธรรมได้อย่างไร",
      `ข้อมูลครอบคลุม ${snap.provinces} จังหวัด ${snap.months} เดือน รวม ${nf(snap.rows)} แถวใน mart จาก 5 แหล่งทางการ`,
      "ผลลัพธ์มี 3 ส่วน: Data Model ที่ตอบ 10 คำถามธุรกิจด้วย SQL, Dashboard และ AI Assistant ภาษาไทย",
    ].join("\n"));
  }

  // ============================================================ 2 Executive summary
  {
    const s = contentSlide("Introduction", "EXECUTIVE SUMMARY", "ยอดรวมทำให้ภาพตลาดบิดเบือน ระบบนี้ช่วยเทียบจังหวัดด้วยตัวชี้วัดที่ปรับขนาดและตรวจสอบได้");
    const cols = [
      { k: "scale", v: `${Math.round(cq10.bangkok_share_pct)}%`, h: "ของสินเชื่อบันทึกในกรุงเทพฯ", b: `5 จังหวัดแรกรวม ${nf(cq10.top5_share_pct, 1)}% ยอดรวมจึงสะท้อนที่ตั้งการบันทึกบัญชี มากกว่าความต้องการในพื้นที่ ต้องเทียบด้วยตัวชี้วัดต่อประชากร ต่อเงินฝาก และต่อ GPP` },
      { k: "filter", v: String(R.CQ07.length), h: "จังหวัดผ่านเกณฑ์คัดกรอง", b: "ไม่รวมกรุงเทพฯ, GPP ≥ 1 แสนล้านบาท, สินเชื่อ ≥ 5 หมื่นล้านบาท และสาขา ≤ 15 แห่งต่อแสนคน ใช้เป็น long list สำหรับศึกษาเชิงลึก" },
      { k: "check", v: "10/10", h: "คำถามธุรกิจตอบได้ด้วย SQL", b: `5 แหล่งข้อมูลทางการรวมเป็น mart ${nf(snap.rows)} แถว ใช้งานผ่าน Dashboard และ AI Assistant ที่รัน Read-only SQL หลังผ่านการตรวจแผนเท่านั้น` },
    ];
    const cw = (CW - 2 * 0.35) / 3;
    cols.forEach((c, i) => {
      const x = M + i * (cw + 0.35);
      card(s, x, TOP, cw, 3.95);
      iconCircle(s, c.k, x + 0.35, TOP + 0.35, 0.62);
      text(s, c.v, { x: x + 0.35, y: TOP + 1.15, w: cw - 0.7, h: 0.9, fontSize: 44, bold: true, color: C.accent1 });
      text(s, c.h, { x: x + 0.35, y: TOP + 2.05, w: cw - 0.7, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
      text(s, c.b, { x: x + 0.35, y: TOP + 2.6, w: cw - 0.7, h: 1.25, fontSize: 14 });
    });
    note(s, "ขอบเขต: เครื่องมือคัดกรองตลาดระดับจังหวัด ไม่ใช่การอนุมัติสินเชื่อ การจัดอันดับการลงทุน หรือการตัดสินใจเปิด/ปิดสาขา", 6.5);
    s.addNotes("สรุป 3 ข้อก่อนลงรายละเอียด: (1) ยอดรวมถูกครอบงำโดยกรุงเทพฯ จึงต้องใช้ตัวชี้วัดปรับขนาด (2) เกณฑ์ตัวอย่างได้ 22 จังหวัดเป็นรายชื่อศึกษาต่อ (3) ทุกคำตอบตรวจย้อนไปถึง SQL และแหล่งข้อมูลได้");
  }

  // ============================================================ 3 Problem
  {
    const s = contentSlide("Introduction", "BUSINESS PROBLEM", "จังหวัดที่ขนาดเศรษฐกิจใกล้กัน อาจมียอดสินเชื่อต่างกันหลายเท่า");
    card(s, M, TOP, 6.2, 4.45, C.background1, "Chart frame");
    const toB = (v) => Math.round(v / 100) / 10; // million -> billion, 1 dp
    s.addChart(pres.charts.BAR, [
      { name: pair.province_a, labels: ["GPP ปี 2567", "สินเชื่อ ก.ค. 2569"], values: [toB(pair.gpp_a_million), toB(pair.credits_a_million)] },
      { name: pair.province_b, labels: ["GPP ปี 2567", "สินเชื่อ ก.ค. 2569"], values: [toB(pair.gpp_b_million), toB(pair.credits_b_million)] },
    ], chartStyle({
      x: M, y: TOP, w: 6.2, h: 4.45, barDir: "col", barGapWidthPct: 60,
      chartColors: [HEX.slate, HEX.green], showLegend: true, legendPos: "t",
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0.0",
      showTitle: true, title: "หน่วย: พันล้านบาท", valAxisHidden: true, valGridLine: { style: "none" },
      objectName: "GPP vs loans chart",
    }));
    const x2 = M + 6.6, w2 = CW - 6.6;
    text(s, [
      { text: `GPP ต่างกัน ${nf(pairGap, 1)}%`, options: { breakLine: true } },
      { text: `แต่สินเชื่อต่างกัน ${nf(pair.credit_size_ratio, 1)} เท่า` },
    ], { x: x2, y: TOP, w: w2, h: 0.95, fontSize: 22, bold: true, color: C.accent1 });
    const rows = [
      ["question", "ปัญหา", "ยอดสินเชื่อขึ้นกับขนาดประชากร โครงสร้างเศรษฐกิจ และที่ตั้งการบันทึกบัญชี การจัดอันดับด้วยยอดรวมจึงชี้ไปที่จังหวัดใหญ่เสมอ"],
      ["users", "ผู้ใช้เป้าหมาย", "นักวิเคราะห์ตลาดและทีมกลยุทธ์ธนาคาร ที่ต้องเลือกจังหวัดสำหรับศึกษาเชิงลึก"],
      ["map", "สิ่งที่ระบบช่วยตอบ", "จังหวัดใดเติบโต มีสาขาหนาแน่น หรือผ่านเกณฑ์ที่กำหนด โดยเห็นสูตร ปีอ้างอิง และแหล่งข้อมูลของทุกตัวเลข"],
    ];
    rows.forEach(([k, h, b], i) => {
      const y = TOP + 1.2 + i * 1.08;
      iconCircle(s, k, x2, y, 0.52);
      text(s, h, { x: x2 + 0.72, y, w: w2 - 0.72, h: 0.32, fontSize: 15, bold: true, color: C.text2 });
      text(s, b, { x: x2 + 0.72, y: y + 0.34, w: w2 - 0.72, h: 0.7, fontSize: 13 });
    });
    note(s, `ตัวอย่างจาก CQ04: ${pair.province_a} และ ${pair.province_b} · GPP 2567 (2024p) จาก สศช. · สินเชื่อ ก.ค. 2569 จาก ธปท.`);
    s.addNotes(`ยกตัวอย่างจริงจาก CQ04: ${pair.province_a} กับ ${pair.province_b} มี GPP ใกล้กัน (ต่าง ${nf(pairGap, 1)}%) แต่สินเชื่อต่างกัน ${nf(pair.credit_size_ratio, 2)} เท่า แสดงว่าขนาดเศรษฐกิจไม่ได้บอกขนาดตลาดสินเชื่อโดยตรง จึงต้องมีระบบที่เทียบหลายมิติพร้อมกัน`);
  }

  // ============================================================ 4 Competency questions
  pres.addSection({ title: "Data & Architecture" });
  {
    const s = contentSlide("Data & Architecture", "10 COMPETENCY QUESTIONS", "10 คำถามธุรกิจเป็นตัวกำหนดว่า Data Model ต้องเก็บข้อมูลอะไร และเชื่อมกันอย่างไร");
    const groups = [
      { k: "chart", h: "การเติบโตและบริบทตลาด", items: [["CQ01", "สินเชื่อ YoY เป็นบวกต่อเนื่อง 12 เดือน"], ["CQ02", "เงินฝากโตเร็วกว่าสินเชื่อมากที่สุด"], ["CQ05", "ยอดรวมเมื่อดอกเบี้ยนโยบายเปลี่ยน"], ["CQ06", "สาขาลดลง แต่สินเชื่อเพิ่มขึ้น YoY"]] },
      { k: "scale", h: "ตัวชี้วัดปรับขนาด", items: [["CQ03", "สาขาต่อประชากรแสนคน"], ["CQ08", "สินเชื่อต่อเงินฝากสูงสุด"], ["CQ09", "เงินฝากต่อประชากรทะเบียน"], ["CQ10", "การกระจุกตัวของสินเชื่อ"]] },
      { k: "filter", h: "เทียบและคัดกรองพื้นที่", items: [["CQ04", "GPP ใกล้กัน สินเชื่อต่างกันเท่าไร"], ["CQ07", "จังหวัดที่ผ่านเกณฑ์ GPP สินเชื่อ และสาขา"]] },
    ];
    const cw = (CW - 2 * 0.3) / 3;
    groups.forEach((g, i) => {
      const x = M + i * (cw + 0.3);
      card(s, x, TOP, cw, 4.45);
      iconCircle(s, g.k, x + 0.3, TOP + 0.3, 0.55);
      text(s, g.h, { x: x + 1.0, y: TOP + 0.38, w: cw - 1.2, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
      g.items.forEach(([id, q], j) => {
        const y = TOP + 1.15 + j * 0.8;
        text(s, id, { x: x + 0.3, y, w: 0.8, h: 0.35, fontSize: 14, bold: true, color: C.accent1 });
        text(s, q, { x: x + 1.05, y, w: cw - 1.3, h: 0.7, fontSize: 14 });
      });
    });
    note(s, "SQL แหล่งข้อมูล และผลของทุกคำถามอยู่ใน Appendix B–E · YoY = เทียบกับเดือนเดียวกันของปีก่อน");
    s.addNotes("คำถามถูกเขียนก่อนออกแบบตาราง แต่ละคำถามบังคับให้ต้องมีข้อมูลบางอย่าง เช่น CQ03 ต้องเชื่อมสาขาจาก ธปท. กับประชากรจากกรมการปกครอง ส่วน CQ05 ต้องจับคู่ดอกเบี้ยนโยบายแบบ as-of กับข้อมูลรายเดือน");
  }

  // ============================================================ 5 Data sources
  {
    const s = contentSlide("Data & Architecture", "DATA SOURCES & INTEGRATION", "รวม 5 แหล่งข้อมูลทางการที่ต่างกันทั้งรูปแบบไฟล์ ความถี่ และวันเผยแพร่");
    table(s, [
      ["แหล่งข้อมูล", "ข้อมูลที่ใช้", "ความถี่", "วิธีดึง", "การใช้งานใน mart"],
      ["ธปท. (FI_CB_011_S5)", "สินเชื่อ เงินฝาก จำนวนสาขา", "รายเดือน", "Web table / HTTP", `ครบ ${nf(snap.rows)} แถว`],
      ["กรมการปกครอง (DOPA)", "ประชากรตามทะเบียน", "รายปี", "ไฟล์ TXT", `ครบ ${nf(snap.rows)} แถว`],
      ["สศช. (NESDC)", "ผลิตภัณฑ์มวลรวมจังหวัด (GPP)", "รายปี", "XLSX workbook", "385 แถว ตามวันเผยแพร่"],
      ["ธปท. มติ กนง.", "อัตราดอกเบี้ยนโยบาย", "ตามมติ", "XLSX workbook", "ครบ ใช้มติล่าสุด ณ สิ้นเดือน"],
      ["World Bank", "เงินเฟ้อระดับประเทศ", "รายปี", "REST API / JSON", "ดึงได้ 66 ค่า ยังไม่ผ่านกฎวันเผยแพร่"],
    ], { x: M, y: TOP, w: CW, colW: [2.45, 3.05, 1.25, 2.1, 3.283], rowH: 0.48, fontSize: 13 });
    const chips = [
      ["link", "Province mapping", "แปลงชื่อจังหวัดจากทุกแหล่งเป็นรหัสเดียว และตรวจว่าครบ 77 จังหวัด"],
      ["clock", "As-of temporal join", "ใช้เฉพาะข้อมูลที่เผยแพร่แล้ว ณ สิ้นเดือนนั้น ไม่ใช้ข้อมูลจากอนาคต"],
      ["layers", "Source-grain facts", "เก็บแต่ละแหล่งตามความถี่เดิม แล้วจึงรวมเป็น mart รายเดือน"],
    ];
    const cw = (CW - 2 * 0.3) / 3;
    chips.forEach(([k, h, b], i) => {
      const x = M + i * (cw + 0.3), y = 5.15;
      card(s, x, y, cw, 1.3);
      iconCircle(s, k, x + 0.22, y + 0.25, 0.5);
      text(s, h, { x: x + 0.88, y: y + 0.2, w: cw - 1.05, h: 0.32, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: x + 0.88, y: y + 0.55, w: cw - 1.05, h: 0.7, fontSize: 12 });
    });
    note(s, "GPP ขาดในเดือนแรกๆ เพราะ GPP 2024p เผยแพร่หลังเดือนเหล่านั้น · ข้อมูลเงินเฟ้อพร้อม pipeline แต่ยังไม่มีค่าที่ใช้ได้ในช่วงข้อมูลนี้", 6.58);
    s.addNotes("ประเด็นสำคัญคือ 'วันอ้างอิง' กับ 'วันเผยแพร่' ต่างกัน ระบบจึงใช้กฎ as-of เพื่อไม่ให้ข้อมูลที่ยังไม่ประกาศ ณ เวลานั้นรั่วเข้าการวิเคราะห์ย้อนหลัง ผลคือ GPP ใช้ได้ 385 จาก 1,925 แถว และเงินเฟ้อ World Bank ยังไม่มีค่าที่ผ่านกฎ ซึ่งเป็นการตัดสินใจโดยเจตนาเพื่อความถูกต้อง");
  }

  // ============================================================ 6 Data model
  {
    const s = contentSlide("Data & Architecture", "DATA MODEL & ANALYTICAL GRAIN", "หนึ่งแถวใน mart = หนึ่งจังหวัดในหนึ่งเดือน พร้อมบริบทรายปีตามกฎ as-of");
    const bx = (x, y, w, h, title, sub, dark = false) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: dark ? C.text2 : C.background2 }, line: { color: dark ? C.text2 : C.accent6, width: 1 }, objectName: title });
      text(s, [{ text: title, options: { bold: true, breakLine: true, fontSize: 13, color: dark ? C.background1 : C.text2 } }, { text: sub, options: { fontSize: 11, color: dark ? C.accent6 : C.accent4 } }],
        { x: x + 0.12, y, w: w - 0.24, h, valign: "middle", align: "center" });
    };
    const lx = M, lw = 3.0;
    text(s, "Source-grain facts", { x: lx, y: TOP - 0.05, w: lw, h: 0.3, fontSize: 12, bold: true, color: C.accent4 });
    const facts = [["fact_bank_month", "จังหวัด + เดือน · ธปท."], ["fact_population_year", "จังหวัด + ปี · DOPA"], ["fact_gpp_year", "จังหวัด + ปี · สศช."], ["fact_macro_year", "ปี · World Bank"], ["fact_policy_event", "วันที่มีผล · กนง."]];
    facts.forEach(([t, d], i) => bx(lx, TOP + 0.35 + i * 0.82, lw, 0.68, t, d));
    text(s, "Dimensions", { x: lx + 3.45, y: TOP - 0.05, w: 2.6, h: 0.3, fontSize: 12, bold: true, color: C.accent4 });
    bx(lx + 3.45, TOP + 0.35, 2.6, 0.68, "dim_province", "77 จังหวัด");
    bx(lx + 3.45, TOP + 1.17, 2.6, 0.68, "dim_month", "25 เดือน");
    const mx = lx + 3.45, my = TOP + 2.35;
    bx(mx, my, 2.6, 1.35, "mart_province_month", "PK: province_code + period\nยอด · อัตราส่วน · ปีอ้างอิง", true);
    // connectors: facts -> mart, dims -> mart
    facts.forEach((_, i) => {
      s.addShape(pres.shapes.LINE, { x: lx + lw, y: TOP + 0.69 + i * 0.82, w: 0.22, h: 0, line: { color: HEX.slate, width: 1 } });
    });
    s.addShape(pres.shapes.LINE, { x: lx + lw + 0.22, y: TOP + 0.69, w: 0, h: 3.28, line: { color: HEX.slate, width: 1 } });
    s.addShape(pres.shapes.LINE, { x: lx + lw + 0.22, y: my + 0.67, w: 0.23, h: 0, line: { color: HEX.slate, width: 1.25, endArrowType: "triangle" } });
    s.addShape(pres.shapes.LINE, { x: mx + 1.3, y: TOP + 1.85, w: 0, h: 0.5, line: { color: HEX.slate, width: 1.25, endArrowType: "triangle" } });
    // consumers
    s.addShape(pres.shapes.LINE, { x: mx + 1.3, y: my + 1.35, w: 0, h: 0.4, line: { color: HEX.slate, width: 1.25, endArrowType: "triangle" } });
    text(s, "Dashboard  ·  FastAPI / Assistant  ·  Grafana", { x: mx - 0.4, y: my + 1.8, w: 3.4, h: 0.35, fontSize: 12, bold: true, color: C.accent1, align: "center" });
    // right column: grain stat + rationale
    const rx = M + 6.65, rw = CW - 6.65;
    card(s, rx, TOP, rw, 1.75);
    text(s, `${snap.provinces} × ${snap.months} = ${nf(snap.rows)}`, { x: rx + 0.35, y: TOP + 0.25, w: rw - 0.7, h: 0.75, fontSize: 36, bold: true, color: C.accent1 });
    text(s, "แถวใน mart (จังหวัด × เดือน)", { x: rx + 0.35, y: TOP + 1.05, w: rw - 0.7, h: 0.4, fontSize: 15, color: C.text2 });
    const why = [
      ["db", "ทำไมเป็น Relational", "PostgreSQL รองรับ Join, Aggregate และ Self-join เทียบ YoY ได้ตรงไปตรงมา"],
      ["layers", "ทำไมแยก fact ตามความถี่", "ข้อมูลรายปีคงความหมายเดิม และตรวจย้อนได้ว่ามาจากปีใด"],
    ];
    why.forEach(([k, h, b], i) => {
      const y = TOP + 2.15 + i * 1.12;
      iconCircle(s, k, rx, y, 0.5);
      text(s, h, { x: rx + 0.7, y, w: rw - 0.7, h: 0.32, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: rx + 0.7, y: y + 0.35, w: rw - 0.7, h: 0.7, fontSize: 13 });
    });
    s.addNotes("mart เป็นตารางกว้างที่ทุก query ใช้ร่วมกัน ข้อดีคือสูตรอยู่ที่เดียว ส่วน fact แยกตามความถี่ต้นทาง ทำให้ตรวจย้อนได้ว่าแต่ละค่ามาจากปีอ้างอิงใด รายละเอียดคีย์อยู่ใน Appendix A");
  }

  // ============================================================ 7 Architecture
  {
    const s = contentSlide("Data & Architecture", "SYSTEM ARCHITECTURE", "Pipeline อัตโนมัติจากแหล่งข้อมูลถึงผู้ใช้ ผ่าน API แบบอ่านอย่างเดียว");
    const steps = [
      ["cloud", "Public sources", "ธปท. · DOPA · สศช.\nWorld Bank · กนง."],
      ["gear", "ETL + Airflow", "Python ตรวจ schema\nรันทุกวัน 07:00 น."],
      ["db", "PostgreSQL", "Dimensions · Facts\nmart_province_month"],
      ["api", "FastAPI", "Analytics API\nRead-only transaction"],
      ["chart", "Next.js · Grafana", "Dashboard · Assistant\n13 Grafana panels"],
    ];
    const sw = 2.05, gap = (CW - 5 * sw) / 4;
    steps.forEach(([k, h, b], i) => {
      const x = M + i * (sw + gap);
      card(s, x, TOP, sw, 2.45);
      iconCircle(s, k, x + (sw - 0.7) / 2, TOP + 0.3, 0.7, i === 2 ? C.text2 : C.accent1);
      text(s, h, { x: x + 0.1, y: TOP + 1.12, w: sw - 0.2, h: 0.35, fontSize: 14, bold: true, color: C.text2, align: "center" });
      text(s, b, { x: x + 0.1, y: TOP + 1.5, w: sw - 0.2, h: 0.8, fontSize: 12, align: "center", color: C.accent4 });
      if (i < 4) s.addImage({ data: ICONS.arrow_g, x: x + sw + (gap - 0.24) / 2, y: TOP + 1.1, w: 0.24, h: 0.24, altText: "ถัดไป" });
    });
    const pr = [
      ["eye", "Provenance", "ทุกค่ามีปีอ้างอิง วันเผยแพร่ และเวลาดึงข้อมูลกำกับ"],
      ["lock", "Read-only access", "ผู้ใช้และ Assistant อ่านข้อมูลผ่าน SQL ที่ตรวจแล้วเท่านั้น"],
      ["code", "Reproducible", "SQL ของ 10 คำถามและผลลัพธ์เก็บไว้ใน repository"],
    ];
    const cw = (CW - 2 * 0.3) / 3;
    text(s, "หลักการออกแบบ", { x: M, y: 4.7, w: 4, h: 0.32, fontSize: 14, bold: true, color: C.accent4 });
    pr.forEach(([k, h, b], i) => {
      const x = M + i * (cw + 0.3), y = 5.1;
      iconCircle(s, k + "", x, y, 0.5, C.text2);
      text(s, h, { x: x + 0.7, y, w: cw - 0.7, h: 0.32, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: x + 0.7, y: y + 0.35, w: cw - 0.75, h: 0.75, fontSize: 13 });
    });
    s.addNotes("ไล่จากซ้ายไปขวา: ETL ใน Python ตรวจ schema และหน่วยก่อนเขียนลง PostgreSQL, Airflow ตั้งเวลา 07:00 ทุกวัน, FastAPI เป็นชั้นเดียวที่แตะฐานข้อมูลแบบอ่านอย่างเดียว ส่วน Next.js เรียกผ่าน server proxy และ Grafana ใช้สำหรับรายงาน");
  }

  // ============================================================ 8 Finding 1: concentration
  pres.addSection({ title: "Findings" });
  {
    const s = contentSlide("Findings", "FINDING 1 · การกระจุกตัวของสินเชื่อ", `สินเชื่อ ${nf(cq10.bangkok_share_pct, 0)}% บันทึกในกรุงเทพฯ จึงต้องเทียบจังหวัดด้วยตัวชี้วัดที่ปรับขนาดแล้ว`);
    // Top-5 provinces by loans come from the overview mart; shares are recomputed against the national total.
    const top5 = [["กรุงเทพฯ", 13825081], ["ชลบุรี", 450683], ["สมุทรปราการ", 296751], ["นนทบุรี", 267194], ["เชียงใหม่", 203282]];
    const tot = cq10.national_credits_million;
    const shares = top5.map(([n, v]) => [n, Math.round((10000 * v) / tot) / 100]);
    const top5Sum = top5.reduce((a, [, v]) => a + v, 0);
    shares.push([`อีก ${snap.provinces - 5} จังหวัด`, Math.round((10000 * (tot - top5Sum)) / tot) / 100]);
    s.addChart(pres.charts.BAR, [{ name: "สัดส่วนสินเชื่อ", labels: shares.map((r) => r[0]), values: shares.map((r) => r[1]) }], chartStyle({
      x: M, y: TOP, w: 6.5, h: 4.45, barDir: "bar", barGapWidthPct: 45, catAxisOrientation: "maxMin",
      chartColors: [HEX.green], showLegend: false, valAxisHidden: true, valGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.00"%"', catAxisLabelFontSize: 13, dataLabelFontSize: 12,
      showTitle: true, title: `สัดส่วนของสินเชื่อรวม ${nf(tot / 1e6, 2)} ล้านล้านบาท (ก.ค. 2569)`, valAxisMaxVal: 90,
      objectName: "Loan share chart",
    }));
    const rx = M + 6.9, rw = CW - 6.9;
    text(s, `${nf(cq10.top5_share_pct, 2)}%`, { x: rx, y: TOP, w: rw, h: 0.85, fontSize: 40, bold: true, color: C.accent1 });
    text(s, "ของสินเชื่ออยู่ใน 5 จังหวัดแรก", { x: rx, y: TOP + 0.85, w: rw, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
    text(s, [
      { text: "ยอดบันทึกตามที่ตั้งสาขาและสำนักงานใหญ่ ไม่ใช่ที่อยู่ของผู้กู้", options: { bullet: true, breakLine: true } },
      { text: "การจัดอันดับด้วยยอดรวมจะได้กรุงเทพฯ และจังหวัดใหญ่ทุกครั้ง", options: { bullet: true, breakLine: true } },
      { text: "ระบบจึงเพิ่มตัวชี้วัดต่อประชากร ต่อสาขา ต่อเงินฝาก ต่อ GPP และตัวเลือก ‘ไม่รวมกรุงเทพฯ’", options: { bullet: true } },
    ], { x: rx, y: TOP + 1.45, w: rw, h: 2.6, fontSize: 14, paraSpaceAfter: 8 });
    note(s, "CQ10 · ยอดคงค้าง ณ สิ้นเดือน ก.ค. 2569 จาก ธปท. · ผลรวมรายจังหวัดอาจต่างจากยอดประเทศเล็กน้อยจากการปัดเศษ");
    s.addNotes(`กรุงเทพฯ ${nf(cq10.bangkok_share_pct, 2)}% และ 5 จังหวัดแรก ${nf(cq10.top5_share_pct, 2)}% ของยอดสินเชื่อ ${nf(tot)} ล้านบาท ข้อสรุปคือยอดรวมใช้บอกขนาดตลาดที่บันทึกได้ แต่ใช้เลือกพื้นที่ไม่ได้ จึงเป็นเหตุผลของตัวชี้วัดปรับขนาดในสไลด์ถัดไป`);
  }

  // ============================================================ 9 Finding 2: normalized measures
  {
    const s = contentSlide("Findings", "FINDING 2 · ตัวชี้วัดปรับขนาด", "เมื่อปรับด้วยประชากรและเงินฝาก ภาพของจังหวัดเปลี่ยนไปจากการดูยอดรวม");
    const top = R.CQ03.slice(0, 10);
    s.addChart(pres.charts.BAR, [{ name: "สาขาต่อแสนคน", labels: top.map((r) => shortName(r.name_th)), values: top.map((r) => r.branches_per_100k) }], chartStyle({
      x: M, y: TOP, w: 6.6, h: 4.45, barDir: "bar", barGapWidthPct: 40, catAxisOrientation: "maxMin",
      chartColors: [HEX.navy2], showLegend: false, valAxisHidden: true, valGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", catAxisLabelFontSize: 12,
      showTitle: true, title: "สาขาต่อประชากรแสนคน 10 อันดับแรก (CQ03)", valAxisMaxVal: 27,
      objectName: "Branch density chart",
    }));
    const rx = M + 7.0, rw = CW - 7.0;
    const roiEt = R.CQ08[0], bkk = R.CQ08.find((r) => r.name_th === "กรุงเทพมหานคร");
    const pt1 = R.CQ01[0], pt6 = R.CQ06.find((r) => r.name_th === pt1.name_th);
    const cards = [
      [`${nf(roiEt.credit_deposit_ratio_pct, 0)}%`, `${roiEt.name_th}: สินเชื่อต่อเงินฝากสูงสุด`, `สูงกว่ากรุงเทพฯ (${nf(bkk.credit_deposit_ratio_pct, 0)}%) แม้ยอดสินเชื่อเล็กกว่าหลายร้อยเท่า ควรตรวจแหล่งเงินทุนและประเภทสินเชื่อ (CQ08)`],
      [`${pt1.positive_months}/${pt1.observed_months}`, `${pt1.name_th}: สินเชื่อ YoY บวกทุกเดือน`, `ขณะที่สาขาลดลง ${Math.abs(pt6.branch_change)} แห่ง (สินเชื่อ YoY ${pt6.credit_yoy_pct >= 0 ? "+" : ""}${nf(pt6.credit_yoy_pct, 2)}%) สะท้อนการเปลี่ยนช่องทาง ไม่ได้แปลว่าไม่ต้องมีสาขา (CQ01, CQ06)`],
    ];
    cards.forEach(([v, h, b], i) => {
      const y = TOP + i * 2.3;
      card(s, rx, y, rw, 2.1);
      text(s, v, { x: rx + 0.3, y: y + 0.2, w: rw - 0.6, h: 0.7, fontSize: 32, bold: true, color: C.accent1 });
      text(s, h, { x: rx + 0.3, y: y + 0.9, w: rw - 0.6, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: rx + 0.3, y: y + 1.27, w: rw - 0.6, h: 0.75, fontSize: 12 });
    });
    note(s, "สาขา ก.ค. 2569 ÷ ประชากรทะเบียนปี 2568 × 100,000 · ไม่รวมช่องทางดิจิทัล · อัตราส่วนระดับพื้นที่ ไม่ใช่ของธนาคารรายใด");
    s.addNotes("กรุงเทพฯ ยังนำในสาขาต่อประชากร แต่จังหวัดท่องเที่ยวอย่างภูเก็ตตามมาใกล้ๆ เพราะประชากรทะเบียนน้อยกว่าผู้ใช้บริการจริง ส่วนการ์ดด้านขวาแสดงว่าตัวชี้วัดปรับขนาดเผยจังหวัดที่ยอดรวมมองไม่เห็น เช่น ร้อยเอ็ด และปทุมธานี");
  }

  // ============================================================ 10 Finding 3: market trend
  {
    const s = contentSlide("Findings", "FINDING 3 · ภาพรวมตลาดและดอกเบี้ย", `ดอกเบี้ยนโยบายลดจาก ${nf(cq05[0].policy_rate_pct, 2)}% เหลือ ${nf(lastM.policy_rate_pct, 2)}% แต่สินเชื่อรวมทรงตัว ขณะที่เงินฝากขึ้นมาแซงสินเชื่อ`);
    const labels = cq05.map((r) => thMonth(r.period));
    s.addChart(pres.charts.LINE, [
      { name: "สินเชื่อ", labels, values: cq05.map((r) => Math.round(r.credits_million / 1e4) / 100) },
      { name: "เงินฝาก", labels, values: cq05.map((r) => Math.round(r.deposits_million / 1e4) / 100) },
    ], chartStyle({
      x: M, y: TOP, w: 8.3, h: 3.2, chartColors: [HEX.navy, HEX.green], lineSize: 2.5, lineDataSymbol: "none",
      showLegend: true, legendPos: "t", valAxisMinVal: 16.8, valAxisMaxVal: 18.4, valAxisMajorUnit: 0.4, valAxisLabelFormatCode: "0.0",
      catAxisLabelFontSize: 9, catAxisLabelFrequency: 3, showTitle: true, title: "ยอดคงค้างรวม 77 จังหวัด (ล้านล้านบาท)",
      objectName: "Loans and deposits trend",
    }));
    s.addChart(pres.charts.LINE, [{ name: "ดอกเบี้ยนโยบาย (%)", labels, values: cq05.map((r) => r.policy_rate_pct) }], chartStyle({
      x: M, y: TOP + 3.25, w: 8.3, h: 1.3, chartColors: [HEX.amber], lineSize: 2, lineDataSymbol: "none", showLegend: false,
      valAxisMinVal: 0.5, valAxisMaxVal: 3.0, valAxisMajorUnit: 1, valAxisLabelFormatCode: "0.0", catAxisHidden: true,
      showTitle: true, title: "ดอกเบี้ยนโยบาย ณ สิ้นเดือน (%)", titleFontSize: 11,
      objectName: "Policy rate trend",
    }));
    const rx = M + 8.7, rw = CW - 8.7;
    const kpis = [
      [`${loanYoy >= 0 ? "+" : ""}${nf(loanYoy, 2)}%`, "สินเชื่อ YoY"],
      [`+${nf(depYoy, 2)}%`, "เงินฝาก YoY"],
      ["−5.72%", "สาขา YoY (4,790 → 4,516)"],
      [`${rateCuts} ครั้ง`, "กนง. ลดดอกเบี้ยในช่วงข้อมูล"],
    ];
    kpis.forEach(([v, l], i) => {
      const y = TOP + i * 1.12;
      card(s, rx, y, rw, 0.98);
      text(s, v, { x: rx + 0.25, y: y + 0.1, w: rw - 0.5, h: 0.5, fontSize: 24, bold: true, color: i === 3 ? C.accent3 : C.accent1 });
      text(s, l, { x: rx + 0.25, y: y + 0.6, w: rw - 0.5, h: 0.3, fontSize: 12, color: C.text2 });
    });
    note(s, "CQ05 · YoY = ก.ค. 2569 เทียบ ก.ค. 2568 · แสดงการเคลื่อนไหวร่วมกันเท่านั้น ไม่ได้พิสูจน์ผลเชิงเหตุของดอกเบี้ยต่อสินเชื่อ");
    s.addNotes(`ในช่วง ${snap.months} เดือน กนง. ลดดอกเบี้ย ${rateCuts} ครั้ง แต่สินเชื่อรวมเกือบไม่เปลี่ยน (${nf(loanYoy, 2)}% YoY) ขณะที่เงินฝากโต ${nf(depYoy, 2)}% และเริ่มสูงกว่าสินเชื่อตั้งแต่ต้นปี 2569 สาขาลดลง 274 แห่ง ข้อมูลชุดนี้บอกได้แค่ว่าเกิดพร้อมกัน ไม่ได้บอกว่าดอกเบี้ยเป็นสาเหตุ`);
  }

  // ============================================================ 11 Finding 4: shortlist
  {
    const low = shortlist.slice(0, 2).map((r) => shortName(r.name_th)).join(" และ ");
    const s = contentSlide("Findings", "FINDING 4 · การคัดกรองพื้นที่", `${R.CQ07.length} จังหวัดผ่านเกณฑ์ตัวอย่าง โดย${low}มีสินเชื่อต่ำที่สุดเมื่อเทียบกับขนาดเศรษฐกิจ`);
    const crit = ["ไม่รวมกรุงเทพฯ", "GPP ≥ 100,000 ล้านบาท", "สินเชื่อ ≥ 50,000 ล้านบาท", "สาขา ≤ 15 ต่อแสนคน"];
    text(s, "เกณฑ์ CQ07 (ปรับได้ใน Dashboard)", { x: M, y: TOP, w: 3.4, h: 0.32, fontSize: 13, bold: true, color: C.accent4 });
    crit.forEach((c, i) => {
      const y = TOP + 0.45 + i * 0.62;
      card(s, M, y, 3.4, 0.5);
      s.addImage({ data: ICONS.check_g, x: M + 0.15, y: y + 0.13, w: 0.24, h: 0.24, altText: "เกณฑ์" });
      text(s, c, { x: M + 0.5, y, w: 2.85, h: 0.5, fontSize: 13, valign: "middle" });
    });
    text(s, [
      { text: "อ่านอย่างไร: ", options: { bold: true, color: C.text2 } },
      { text: "อัตราต่ำอาจเกิดจากบริษัทใหญ่ในนิคมฯ บันทึกสินเชื่อที่สำนักงานใหญ่ในกรุงเทพฯ หรือเป็นช่องว่างการให้บริการจริง ต้องตรวจเพิ่มก่อนสรุป" },
    ], { x: M, y: TOP + 3.1, w: 3.4, h: 1.4, fontSize: 12 });
    s.addChart(pres.charts.BAR, [{ name: "สินเชื่อต่อ GPP", labels: shortlist.map((r) => shortName(r.name_th)), values: shortlist.map((r) => Math.round(r.ratio * 10) / 10) }], chartStyle({
      x: M + 3.75, y: TOP - 0.05, w: CW - 3.75, h: 4.6, barDir: "bar", barGapWidthPct: 30, catAxisOrientation: "maxMin",
      chartColors: [HEX.green], showLegend: false, valAxisHidden: true, valGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', catAxisLabelFontSize: 9, dataLabelFontSize: 9,
      showTitle: true, title: `สินเชื่อ ÷ GPP ของ ${R.CQ07.length} จังหวัดที่ผ่านเกณฑ์ (ต่ำ → สูง)`,
      objectName: "Loans to GPP chart",
    }));
    note(s, "สินเชื่อ ก.ค. 2569 ÷ GPP 2567 (2024p) คำนวณจากผล CQ07 · ช่วงเวลาอ้างอิงต่างกัน ใช้เทียบระหว่างจังหวัด ไม่ใช่อัตราส่วนทางเศรษฐศาสตร์ที่สมบูรณ์");
    s.addNotes(`เกณฑ์เป็นสมมติฐานที่ปรับได้ ไม่ใช่การจัดอันดับการลงทุน เมื่อเรียงสินเชื่อต่อ GPP พบว่า ${shortlist.slice(0, 4).map((r) => `${r.name_th} ${nf(r.ratio, 1)}%`).join(", ")} ต่ำสุด เป็นกลุ่มอุตสาหกรรมภาคตะวันออกและภาคกลาง ซึ่งอาจอธิบายได้ด้วยการบันทึกบัญชีที่สำนักงานใหญ่ จึงเป็นคำถามสำหรับการศึกษาเชิงลึก ไม่ใช่ข้อสรุป`);
  }

  // ============================================================ 12 Dashboard
  pres.addSection({ title: "Application" });
  {
    const s = contentSlide("Application", "DASHBOARD", "Dashboard ให้ผู้ใช้สำรวจตลาด ปรับเกณฑ์ และตรวจที่มาของตัวเลขได้เอง");
    const iw = (CW - 0.4) / 2;
    const shots = [["overview.png", 1245, 735, "ภาพรวมตลาด", "KPI, แนวโน้มสินเชื่อ/เงินฝาก, ดอกเบี้ยนโยบาย และการกระจุกตัว"], ["screening.png", 1245, 620, "คัดกรองพื้นที่", "ปรับเกณฑ์ เห็นปีอ้างอิงของ GPP/ประชากร และดาวน์โหลด CSV"]];
    shots.forEach(([f, pw, ph, h, b], i) => {
      const x = M + i * (iw + 0.4), ih = Math.min(3.25, iw * ph / pw), w = ih * pw / ph;
      s.addImage({ path: path.join(ASSETS, f), x: x + (iw - w) / 2, y: TOP, w, h: ih, altText: h, shadow: shadow(), objectName: h });
      text(s, h, { x, y: TOP + 3.45, w: iw, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
      text(s, b, { x, y: TOP + 3.82, w: iw, h: 0.35, fontSize: 13, color: C.accent4 });
    });
    const pages = ["ภาพรวมตลาด", "วิเคราะห์จังหวัด (เทียบได้ 4 จังหวัด)", "ผู้ช่วยวิเคราะห์", "คำถามธุรกิจ + SQL", "แหล่งข้อมูลและคุณภาพ"];
    text(s, [{ text: "5 หน้าหลัก:  ", options: { bold: true, color: C.text2 } }, { text: pages.join("  ·  ") }], { x: M, y: 6.45, w: CW, h: 0.35, fontSize: 12 });
    s.addNotes("Demo ที่แนะนำ: เปิดภาพรวมตลาด → เทียบ 2 จังหวัด → ปรับเกณฑ์คัดกรองแล้วอธิบายว่าทำไมแต่ละจังหวัดผ่าน → เปิดคำถามธุรกิจเพื่อดู SQL → ถาม Assistant");
  }

  // ============================================================ 13 Assistant
  {
    const s = contentSlide("Application", "AI ASSISTANT", "AI Assistant ตอบคำถามภาษาไทย โดย LLM เลือกเจตนาและวางแผน แต่ไม่ได้เขียน SQL เอง");
    const flow = [
      ["comments", "คำถาม + บริบทที่ยืนยันแล้ว", "จำ metric, ตัวกรอง และงวดของคำตอบก่อนหน้า"],
      ["route", "Gemini router", "เลือก: วิเคราะห์ / อธิบาย / ถามกลับ / เปลี่ยนการแสดงผล / ปฏิเสธ"],
      ["list", "Hybrid planner", "Semantic rules ก่อน แล้วใช้ LLM structured output เมื่อ rules ไม่เข้าใจ"],
      ["shield", "Validation", "QueryPlan (Pydantic) → SQL compiler → SQLGlot → read-only"],
      ["chart", "คำตอบ", "ตัวเลข กราฟ ตาราง SQL และแหล่งข้อมูล"],
    ];
    flow.forEach(([k, h, b], i) => {
      const y = TOP + i * 0.92;
      iconCircle(s, k, M, y, 0.55, i === 1 || i === 2 ? C.accent2 : C.accent1);
      text(s, h, { x: M + 0.75, y: y - 0.02, w: 5.3, h: 0.32, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: M + 0.75, y: y + 0.3, w: 5.3, h: 0.5, fontSize: 12, color: C.accent4 });
      if (i < flow.length - 1) s.addShape(pres.shapes.LINE, { x: M + 0.275, y: y + 0.6, w: 0, h: 0.28, line: { color: HEX.slate, width: 1, endArrowType: "triangle" } });
    });
    const x2 = M + 6.4, iw = CW - 6.4, ih = iw * 555 / 1175;
    s.addImage({ path: path.join(ASSETS, "assistant.png"), x: x2, y: TOP, w: iw, h: ih, altText: "Assistant ถามกลับเมื่อคำถามกำกวม", shadow: shadow(), objectName: "Assistant screenshot" });
    text(s, "ถามกลับเมื่อตัวหารกำกวม แทนการเดา", { x: x2, y: TOP + ih + 0.2, w: iw, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
    text(s, "เช่น ‘สินเชื่อเทียบกับสาขาและประชากร’ ระบบให้เลือกว่าจะจัดอันดับด้วยสินเชื่อต่อประชากรหรือต่อสาขา", { x: x2, y: TOP + ih + 0.58, w: iw, h: 0.65, fontSize: 12 });
    note(s, "คำถามนอกขอบเขต เช่น NPL หรือข้อมูลรายธนาคาร ถูกปฏิเสธก่อนเรียก LLM · ไม่มี API key ก็ยังใช้ rules-based analytics ได้");
    s.addNotes("จุดออกแบบสำคัญ: LLM ไม่ได้สร้าง SQL โดยตรง แต่สร้าง QueryPlan ที่มีโครงสร้าง แล้ว compiler แบบ allowlist แปลงเป็น SQL และตรวจด้วย SQLGlot ก่อนรันใน transaction แบบอ่านอย่างเดียว ภาพตัวอย่างบันทึกจากหน้า analytical view ซึ่งเป็นเส้นทางเดียวกับที่ router ส่งต่อมา (ภาพถ่าย 11 ต.ค. 2569)");
  }

  // ============================================================ 14 Validation
  pres.addSection({ title: "Validation & Next steps" });
  {
    const s = contentSlide("Validation & Next steps", "VALIDATION", "ตรวจสอบทั้งข้อมูล ตัวเลข และพฤติกรรมของ Assistant โดยรายงานผลแยกตามประเภทหลักฐาน");
    const tiles = [
      ["170", "Regression tests ผ่าน", "ทดสอบกับฐานข้อมูลจริงในเครื่อง"],
      ["80/80", "คำถามไทยแบบ offline", "ตรวจ status, แผน และตัวเลขด้วยการคำนวณอิสระ"],
      ["14/14", "Held-out planner: hybrid", "เทียบกับ LLM-only ที่ผ่าน 6/14 จึงเลือกใช้ hybrid"],
      ["7/7", "Live conversation smoke", "Gemini router + บริบทข้ามรอบ ผ่าน HTTP จริง"],
    ];
    const tw = (CW - 3 * 0.3) / 4;
    tiles.forEach(([v, h, b], i) => {
      const x = M + i * (tw + 0.3);
      card(s, x, TOP, tw, 2.35);
      text(s, v, { x: x + 0.25, y: TOP + 0.25, w: tw - 0.5, h: 0.8, fontSize: 36, bold: true, color: C.accent1 });
      text(s, h, { x: x + 0.25, y: TOP + 1.08, w: tw - 0.5, h: 0.4, fontSize: 14, bold: true, color: C.text2 });
      text(s, b, { x: x + 0.25, y: TOP + 1.5, w: tw - 0.5, h: 0.75, fontSize: 12 });
    });
    text(s, "การตรวจข้อมูลใน pipeline", { x: M, y: 4.6, w: 6, h: 0.32, fontSize: 14, bold: true, color: C.accent4 });
    const checks = ["Province mapping ครบ 77 จังหวัด", "Key ไม่ซ้ำ และจำนวนแถวหลัง Join ถูกต้อง", "หน่วยและการแปลงหน่วย", "ผลคำนวณเทียบกับการคำนวณอิสระ"];
    checks.forEach((c, i) => {
      const x = M + (i % 2) * 6.2, y = 5.05 + Math.floor(i / 2) * 0.55;
      s.addImage({ data: ICONS.check_g, x, y: y + 0.05, w: 0.26, h: 0.26, altText: "ผ่าน" });
      text(s, c, { x: x + 0.4, y, w: 5.6, h: 0.36, fontSize: 14 });
    });
    note(s, "ตัวเลขแต่ละชุดมีตัวหารต่างกัน จึงไม่รวมเป็น ‘ความแม่นยำ’ ตัวเดียว · รายละเอียดใน Appendix F");
    s.addNotes("เน้นว่าหลักฐานแยกประเภท: regression tests ทดสอบระบบ, 80 คำถามทดสอบ planner แบบ deterministic, benchmark 24 turns เทียบสามกลยุทธ์ และ smoke test ทดสอบ router จริง ผล LLM-only 6/14 เป็นเหตุผลเชิงข้อมูลที่เลือก hybrid planner");
  }

  // ============================================================ 15 Limitations
  {
    const s = contentSlide("Validation & Next steps", "LIMITATIONS", "ข้อจำกัดที่ต้องรู้ก่อนนำผลไปใช้ตัดสินใจ");
    const lim = [
      ["bank", "ที่ตั้งบันทึก ≠ ที่อยู่ผู้กู้", "ยอดของกรุงเทพฯ รวมสินเชื่อที่บันทึกที่สำนักงานใหญ่ จึงควรดูผลแบบไม่รวมกรุงเทพฯ ประกอบ"],
      ["user", "ประชากรทะเบียน ≠ ลูกค้า", "ไม่สะท้อนประชากรแฝงหรือนักท่องเที่ยว และจำนวนสาขาไม่รวมช่องทางดิจิทัล"],
      ["calendar", "บริบทรายปีล่าช้า", "ใช้ GPP 2024p กับยอดปี 2569 และ GPP ขาดใน 1,540 แถวช่วงต้นตามกฎวันเผยแพร่"],
      ["globe", "เงินเฟ้อยังไม่มีค่าใช้ได้", "ดึงจาก World Bank ได้ 66 ค่า แต่ไม่มีค่าที่เผยแพร่ทันช่วงข้อมูลนี้"],
      ["robot", "Assistant ยังเป็น prototype", "Router ผ่าน smoke test แต่ยังไม่ประเมินกับคำถามหลากหลาย ยังไม่มีระบบสิทธิ์ผู้ใช้"],
      ["coins", "ไม่มีข้อมูลระดับลูกค้า", "ไม่มีต้นทุน คุณภาพสินเชื่อ ส่วนแบ่งตลาดรายธนาคาร จึงใช้คัดกรองเท่านั้น"],
    ];
    const cw = (CW - 2 * 0.3) / 3, ch = 2.1;
    lim.forEach(([k, h, b], i) => {
      const x = M + (i % 3) * (cw + 0.3), y = TOP + Math.floor(i / 3) * (ch + 0.25);
      card(s, x, y, cw, ch);
      iconCircle(s, k, x + 0.25, y + 0.25, 0.5, C.accent4);
      text(s, h, { x: x + 0.9, y: y + 0.3, w: cw - 1.1, h: 0.45, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
      text(s, b, { x: x + 0.25, y: y + 0.92, w: cw - 0.5, h: 1.05, fontSize: 13 });
    });
    s.addNotes("รวมข้อจำกัดไว้ในสไลด์เดียวเพื่อให้ชัดว่าระบบตอบอะไรได้และไม่ได้ ทุกข้อมีเอกสารใน docs/data-sources.md และ docs/verification.md");
  }

  // ============================================================ 16 Recommendations
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Validation & Next steps" });
    text(s, "RECOMMENDATIONS & NEXT STEPS", { x: M, y: 0.55, w: CW, h: 0.3, fontSize: 12, bold: true, color: C.accent5, charSpacing: 1 });
    text(s, "ใช้ระบบเป็นจุดเริ่มของการเลือกพื้นที่ แล้วเติมข้อมูลที่ยังขาดก่อนตัดสินใจ", { x: M, y: 0.92, w: CW, h: 0.95, fontSize: 26, bold: true, color: C.background1 });
    const low3 = shortlist.slice(0, 3).map((r) => shortName(r.name_th)).join(" ");
    const lowBranch = R.CQ07.slice().sort((a, b) => a.branches_per_100k - b.branches_per_100k).slice(0, 2).map((r) => shortName(r.name_th)).join(" ");
    const colsData = [
      ["map", "ด้านธุรกิจ", [
        `ใช้ ${R.CQ07.length} จังหวัดเป็น long list แล้วเลือก 3–5 จังหวัดศึกษาเชิงลึก`,
        `เริ่มจากกลุ่มสินเชื่อต่ำเทียบ GPP (${low3}) และกลุ่มสาขาต่อประชากรต่ำ (${lowBranch})`,
        "เติมข้อมูลคู่แข่ง การใช้ช่องทางดิจิทัล ต้นทุน และคุณภาพสินเชื่อ",
      ]],
      ["gear", "ด้านระบบ", [
        "ประเมิน conversation router ด้วยชุดคำถามที่ใหญ่และหลากหลายขึ้น",
        "เพิ่ม authentication สิทธิ์ผู้ใช้ และนโยบายเก็บประวัติแชต",
        "ประกาศ Foreign Key และติดตาม scheduled runs ต่อเนื่อง 1 เดือน",
      ]],
    ];
    const cw = (CW - 0.4) / 2;
    colsData.forEach(([k, h, items], i) => {
      const x = M + i * (cw + 0.4), y = 2.15;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: 3.55, rectRadius: 0.08, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: h });
      iconCircle(s, k, x + 0.35, y + 0.3, 0.6, C.accent1);
      text(s, h, { x: x + 1.15, y: y + 0.38, w: cw - 1.4, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
      text(s, items.map((t, j) => ({ text: t, options: { bullet: { type: "number" }, breakLine: j < items.length - 1 } })),
        { x: x + 0.35, y: y + 1.15, w: cw - 0.7, h: 2.25, fontSize: 15, color: C.background1, paraSpaceAfter: 10 });
    });
    text(s, "Questions & Discussion", { x: M, y: 6.1, w: CW, h: 0.5, fontSize: 22, bold: true, color: C.accent5 });
    s.addNotes("ปิดด้วยข้อเสนอที่ทำได้จริง: shortlist คือคำถามสำหรับการศึกษาต่อ ไม่ใช่คำตอบสุดท้าย ด้านระบบต้องประเมิน router และเพิ่มความปลอดภัยก่อนใช้งานจริง จากนั้นเปิดรับคำถาม (ใช้ Appendix ตอบเรื่อง schema, SQL, การประเมิน AI และ data contract)");
  }

  // ============================================================ Appendix divider
  pres.addSection({ title: "Appendix" });
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Appendix" });
    text(s, "Appendix", { x: M, y: 1.0, w: CW, h: 0.9, fontSize: 40, bold: true, color: C.background1 });
    text(s, "รายละเอียดสำหรับตอบคำถาม", { x: M, y: 1.9, w: CW, h: 0.5, fontSize: 18, color: C.accent5 });
    const items = ["A  Logical schema", "B  CQ mapping (CQ01–CQ05)", "C  CQ mapping (CQ06–CQ10)", "D  SQL: CQ01", "E  SQL: CQ03 และ CQ07", "F  AI evaluation", "G  Data contract และแหล่งข้อมูล"];
    items.forEach((t, i) => text(s, t, { x: M + (i % 2) * 6.0, y: 3.0 + Math.floor(i / 2) * 0.62, w: 5.8, h: 0.45, fontSize: 18, color: C.background1 }));
  }

  // ============================================================ A Schema
  {
    const s = contentSlide("Appendix", "APPENDIX A", "Logical schema: ตารางหลักและ Primary Keys", "APPENDIX");
    const box = (x, y, w, h, t, d, dark) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.05, fill: { color: dark ? C.text2 : C.background2 }, line: { color: dark ? C.text2 : C.accent6, width: 1 }, objectName: t });
      text(s, [{ text: t, options: { bold: true, breakLine: true, fontSize: 13, color: dark ? C.background1 : C.text2 } }, { text: d, options: { fontSize: 11, color: dark ? C.accent6 : C.accent4 } }], { x: x + 0.1, y, w: w - 0.2, h, align: "center", valign: "middle" });
    };
    const bw = 3.5, gx = (CW - 3 * bw) / 2;
    const col = (i) => M + i * (bw + gx);
    box(col(0), TOP, bw, 0.9, "dim_province", "province_code PK · name_th");
    box(col(1), TOP, bw, 0.9, "dim_month", "period PK · year · month");
    box(col(0), TOP + 1.4, bw, 1.0, "fact_bank_month", "PK province_code + period\ncredits · deposits · branches");
    box(col(1), TOP + 1.4, bw, 1.0, "fact_population_year", "PK province_code + year\npopulation");
    box(col(2), TOP + 1.4, bw, 1.0, "fact_gpp_year", "PK province_code + year\ngpp · last_modified");
    box(col(0), TOP + 2.9, bw, 1.0, "fact_macro_year", "PK reference_year\ninflation · last_updated");
    box(col(1), TOP + 2.9, bw, 1.0, "mart_province_month", "PK province_code + period\nratios · context reference years", true);
    box(col(2), TOP + 2.9, bw, 1.0, "fact_policy_event", "PK event_date\npolicy_rate · decision");
    const L = (x, y, w, h, arrow) => s.addShape(pres.shapes.LINE, { x, y, w, h, line: { color: HEX.slate, width: 1, endArrowType: arrow ? "triangle" : undefined } });
    L(col(0) + bw / 2, TOP + 0.9, 0, 0.5, true);
    L(col(1) + bw / 2, TOP + 2.4, 0, 0.5, true);
    L(col(0) + bw, TOP + 3.4, gx, 0, true);
    s.addShape(pres.shapes.LINE, { x: col(1) + bw, y: TOP + 3.4, w: gx, h: 0, line: { color: HEX.slate, width: 1, beginArrowType: "triangle" } });
    L(col(0) + bw / 2, TOP + 2.4, 0, 0.25, false);
    L(col(0) + bw / 2, TOP + 2.65, bw / 2 + gx + 0.6, 0, false);
    L(col(1) + 0.6, TOP + 2.65, 0, 0.25, true);
    L(col(2) + bw / 2, TOP + 2.4, 0, 0.25, false);
    L(col(1) + bw - 0.6, TOP + 2.65, col(2) + bw / 2 - (col(1) + bw - 0.6), 0, false);
    L(col(1) + bw - 0.6, TOP + 2.65, 0, 0.25, true);
    note(s, "เส้นแสดง logical joins ด้วย province_code และ period ตาม grain ของตาราง · บริบทรายปีและรายมติใช้กฎ as-of · ระบบมี Primary Keys แต่ยังไม่ได้ประกาศ Foreign Key constraints", 6.3);
    s.addNotes("แหล่งอ้างอิง: docs/architecture.md");
  }

  // ============================================================ B, C CQ mapping
  const mapRows = [
    ["CQ01", "BOT", "Self-join เดือนเดียวกันปีก่อน + COUNT / AVG", `${R.CQ01[0].name_th} ${R.CQ01[0].positive_months}/12 เดือน; เฉลี่ย +${nf(R.CQ01[0].average_yoy_pct, 2)}%`],
    ["CQ02", "BOT", "Self-join + ผลต่าง YoY (จุดเปอร์เซ็นต์)", `${R.CQ02[0].name_th} ต่างกัน ${nf(R.CQ02[0].growth_gap_pp, 2)} จุด`],
    ["CQ03", "BOT + DOPA", "สาขา ÷ ประชากร × 100,000 + ranking", `กรุงเทพฯ ${nf(R.CQ03[0].branches_per_100k, 2)} สาขาต่อแสนคน`],
    ["CQ04", "BOT + NESDC", "จับคู่จังหวัด GPP ต่าง ≤ 15% ของค่าที่มากกว่า", `${pair.province_a}–${pair.province_b}: สินเชื่อต่าง ${nf(pair.credit_size_ratio, 2)} เท่า`],
    ["CQ05", "BOT + MPC", "SUM รายเดือน + ดอกเบี้ย as-of", `${snap.months} เดือน; ดอกเบี้ย ${nf(cq05[0].policy_rate_pct, 2)}% → ${nf(lastM.policy_rate_pct, 2)}%`],
    ["CQ06", "BOT", "Self-join: สาขาลด และสินเชื่อเพิ่ม YoY", `${R.CQ06.length} จังหวัด; ปทุมธานี −14 สาขา`],
    ["CQ07", "BOT + DOPA + NESDC", "AND เงื่อนไข GPP / สาขา / สินเชื่อ", `${R.CQ07.length} จังหวัด (ไม่รวมกรุงเทพฯ)`],
    ["CQ08", "BOT", "สินเชื่อ ÷ เงินฝาก × 100 + ranking", `${R.CQ08[0].name_th} ${nf(R.CQ08[0].credit_deposit_ratio_pct, 2)}%`],
    ["CQ09", "BOT + DOPA", "เงินฝาก × 1,000,000 ÷ ประชากร", `กรุงเทพฯ ${nf(R.CQ09[0].deposits_baht_per_person / 1e6, 2)} ล้านบาท/คน`],
    ["CQ10", "BOT", "ROW_NUMBER + SUM / share", `กรุงเทพฯ ${nf(cq10.bangkok_share_pct, 2)}%; Top 5 ${nf(cq10.top5_share_pct, 2)}%`],
  ];
  [["APPENDIX B", "CQ mapping (1/2): แหล่งข้อมูล วิธี Query และผลที่บันทึก", mapRows.slice(0, 5), "CQ01 ต้องมีคู่ข้อมูลครบ 12 เดือน · CQ04 ใช้ GPP 2024p กับสินเชื่อ ก.ค. 2569 · CQ05 อธิบายการเคลื่อนไหวร่วมกันเท่านั้น"],
   ["APPENDIX C", "CQ mapping (2/2): แหล่งข้อมูล วิธี Query และผลที่บันทึก", mapRows.slice(5), "CQ07 เป็นเกณฑ์ตัวอย่าง · CQ08 เป็นอัตราส่วนระดับพื้นที่ · CQ09 ใช้ประชากรทะเบียน ไม่ใช่เงินออมรายบุคคล"]].forEach(([k, t, rows, foot]) => {
    const s = contentSlide("Appendix", k, t, "APPENDIX");
    table(s, [["CQ", "แหล่งข้อมูล", "Query logic", "ผลที่บันทึก (ก.ค. 2569)"], ...rows], { x: M, y: TOP, w: CW, colW: [0.9, 2.2, 4.4, 4.633], rowH: 0.62, fontSize: 13 });
    note(s, foot, 6.0);
    s.addNotes("ทุก query อ่าน mart_province_month · แหล่งอ้างอิง: docs/competency-questions.md, sql/competency_questions.sql, docs/evidence/competency-results.json");
  });

  // ============================================================ D, E SQL
  const code = (s, src, x, y, w, h) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: C.text2 }, line: { color: C.text2, width: 0 }, objectName: "Code block" });
    text(s, src, { x: x + 0.25, y: y + 0.2, w: w - 0.5, h: h - 0.4, fontFace: "Courier New", fontSize: 12, color: C.background1, lineSpacingMultiple: 1.05 });
  };
  {
    const s = contentSlide("Appendix", "APPENDIX D", "SQL CQ01: เทียบจังหวัดเดียวกันกับเดือนเดียวกันของปีก่อน", "APPENDIX");
    code(s, [
      "WITH yoy AS (",
      "  SELECT n.province_code, n.name_th, n.period,",
      "    100.0 * (n.credits_million_baht - p.credits_million_baht)",
      "      / NULLIF(p.credits_million_baht, 0) AS yoy_pct",
      "  FROM mart_province_month n",
      "  JOIN mart_province_month p",
      "    ON p.province_code = n.province_code",
      "   AND p.period = (n.period - INTERVAL '1 year')::date",
      "  WHERE n.period >= (SELECT MAX(period) - INTERVAL '11 months' FROM mart_province_month)",
      ")",
      "SELECT name_th,",
      "       COUNT(*) FILTER (WHERE yoy_pct > 0) AS positive_months,",
      "       COUNT(*) AS observed_months,",
      "       ROUND(AVG(yoy_pct)::numeric, 2) AS average_yoy_pct",
      "FROM yoy GROUP BY province_code, name_th HAVING COUNT(*) = 12",
      "ORDER BY positive_months DESC, average_yoy_pct DESC, name_th LIMIT 10;",
    ].join("\n"), M, TOP, CW, 4.2);
    note(s, `นับเดือนที่ YoY เป็นบวก โดยต้องมีคู่ข้อมูลครบ 12 เดือน · อันดับแรก: ${R.CQ01[0].name_th} ${R.CQ01[0].positive_months}/12 เดือน เฉลี่ย +${nf(R.CQ01[0].average_yoy_pct, 2)}%`, 6.3);
    s.addNotes("แหล่งอ้างอิง: sql/competency_questions.sql");
  }
  {
    const s = contentSlide("Appendix", "APPENDIX E", "SQL CQ03 และ CQ07: ranking และการคัดกรองจาก mart", "APPENDIX");
    const hw = (CW - 0.3) / 2;
    text(s, "CQ03 · ความหนาแน่นสาขา", { x: M, y: TOP, w: hw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    code(s, [
      "SELECT name_th, branches, population,",
      "       population_reference_year,",
      "       ROUND(branches_per_100k::numeric, 2)",
      "         AS branches_per_100k",
      "FROM mart_province_month",
      "WHERE period = (SELECT MAX(period)",
      "                FROM mart_province_month)",
      "  AND branches_per_100k IS NOT NULL",
      "ORDER BY branches_per_100k DESC,",
      "         province_code",
      "LIMIT 10;",
    ].join("\n"), M, TOP + 0.45, hw, 3.9);
    text(s, "CQ07 · คัดกรองหลายเงื่อนไข", { x: M + hw + 0.3, y: TOP, w: hw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    code(s, [
      "SELECT name_th, gpp_million_baht,",
      "       credits_million_baht,",
      "       ROUND(branches_per_100k::numeric, 2)",
      "         AS branches_per_100k",
      "FROM mart_province_month",
      "WHERE period = (SELECT MAX(period)",
      "                FROM mart_province_month)",
      "  AND province_code <> 10",
      "  AND gpp_million_baht >= 100000",
      "  AND branches_per_100k <= 15",
      "  AND credits_million_baht >= 50000",
      "ORDER BY gpp_million_baht DESC, province_code;",
    ].join("\n"), M + hw + 0.3, TOP + 0.45, hw, 3.9);
    note(s, "province_code 10 = กรุงเทพมหานคร · เกณฑ์ CQ07 ปรับได้ในหน้า ‘คัดกรองพื้นที่’ ของ Dashboard", 6.5);
    s.addNotes("แหล่งอ้างอิง: sql/competency_questions.sql");
  }

  // ============================================================ F AI evaluation
  {
    const s = contentSlide("Appendix", "APPENDIX F", "AI evaluation: แยก regression, planner benchmark และ conversation routing", "APPENDIX");
    table(s, [
      ["หลักฐาน", "ผลที่บันทึก", "สิ่งที่ยังไม่ได้พิสูจน์"],
      ["Python regression", "170 tests ผ่าน", "ความแม่นยำภาษาธรรมชาติทั่วไป / production readiness"],
      ["Offline Thai analytics", "80/80 ผ่าน status, plan, ตัวเลข", "ความแม่นยำของ LLM แบบ live"],
      ["Held-out planner: rules / hybrid", "14/14 ทั้งสองแบบ; 0 model calls", "ความแม่นยำของ Gemini"],
      ["Held-out planner: LLM-only", "6/14 all-checks; 8/10 numeric", "ตัวหารต่างกัน ไม่ควรรวมเป็น % เดียว"],
      ["Live conversation smoke", "7 turns ผ่าน", "การประเมิน router แบบครอบคลุม"],
    ], { x: M, y: TOP, w: CW, colW: [3.4, 3.9, 4.833], rowH: 0.6, fontSize: 13 });
    note(s, "Planner benchmark ใช้ 24 turns (dev 10 / held-out 14) ก่อนเพิ่ม conversation router จึงต้องประเมิน router แยกต่างหาก", 6.0);
    s.addNotes("แหล่งอ้างอิง: docs/verification.md, docs/evidence/llm/results.md, docs/conversation-routing.md");
  }

  // ============================================================ G Data contract
  {
    const s = contentSlide("Appendix", "APPENDIX G", "Data contract: วันอ้างอิง วันเผยแพร่ และเวลาดึงข้อมูลมีความหมายต่างกัน", "APPENDIX");
    table(s, [
      ["บริบท", "กฎที่ใช้", "แถวที่ขาดใน mart"],
      ["Population", "ใช้ปีทะเบียนล่าสุดตั้งแต่ ม.ค. ของปีถัดไป", `0 / ${nf(snap.rows)}`],
      ["GPP", "Last-Modified ต้องไม่เกินสิ้นเดือนของข้อมูลธนาคาร", `1,540 / ${nf(snap.rows)}`],
      ["Inflation", "ปีก่อนหน้า และ lastupdated ไม่เกินสิ้นเดือน", `${nf(snap.rows)} / ${nf(snap.rows)}`],
      ["Policy rate", "มติล่าสุดที่มีผลไม่เกินสิ้นเดือน", "เลือกตาม event_date"],
    ], { x: M, y: TOP, w: CW, colW: [2.3, 6.6, 3.233], rowH: 0.58, fontSize: 13 });
    text(s, [
      { text: "ยอดสินเชื่อและเงินฝากเป็นยอดคงค้าง ณ สิ้นงวด: ", options: { bold: true, color: C.text2 } },
      { text: "รวมข้ามจังหวัดในเดือนเดียวกันได้ แต่ห้ามรวมข้ามเดือน เพราะไม่ใช่ยอดธุรกรรมรายเดือน", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 6 } },
      { text: "แหล่งทางการ: ", options: { bold: true, color: C.text2 } },
      { text: "app.bot.or.th (FI_CB_011_S5) · stat.bora.dopa.go.th · nesdc.go.th (GPP 2024p) · api.worldbank.org (FP.CPI.TOTL.ZG) · bot.or.th (MPC)" },
    ], { x: M, y: 5.2, w: CW, h: 1.2, fontSize: 12 });
    s.addNotes("แหล่งอ้างอิง: docs/data-sources.md");
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  await useThaiFont(OUT, THEME.bodyFontFace);
  console.log("wrote", OUT);
}

// PowerPoint renders Thai with the theme's complex-script (cs) font, which pptxgenjs leaves
// empty, so Thai would otherwise fall back to Angsana/Cordia New. Point every slot at one font.
async function useThaiFont(file, face) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const name = "ppt/theme/theme1.xml";
  let xml = await zip.file(name).async("string");
  xml = xml.replace(/<a:cs typeface="[^"]*"\/>/g, `<a:cs typeface="${face}"/>`)
    .replace(/<a:font script="Thai" typeface="[^"]*"\/>/g, `<a:font script="Thai" typeface="${face}"/>`);
  zip.file(name, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

build().catch((e) => { console.error(e); process.exit(1); });
