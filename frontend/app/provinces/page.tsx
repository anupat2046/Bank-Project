"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { X } from "lucide-react";
import { DataState, Footer, PageHeading, useWorkspace } from "@/components/shell";
import { ComparisonTable, DataTable } from "@/components/table";
import { GppScatter, TrendChart } from "@/components/charts";
import { Row, metricDefs, number, useApi } from "@/lib/data";

const columns = ["name_th", "credits_million_baht", "deposits_million_baht", "branches", "credit_deposit_ratio_pct", "branches_per_100k", "gpp_million_baht", "gpp_reference_year", "population_reference_year"];
const defaults = { gpp: 100000, credit: 50000, density: 15, exclude: true };
const threshold = (value: string | null, fallback: number) => value !== null && Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : fallback;

export default function ProvincesPage() {
  const { period, meta, href, setParams } = useWorkspace(), params = useSearchParams(), router = useRouter();
  const tab = ["detail", "compare", "screen"].includes(params.get("tab") || "") ? params.get("tab")! : "detail";
  const code = Number(params.get("province") || 50);
  const chosen = (params.get("compare") || "").split(",").filter(Boolean).map(Number).filter((c, i, a) => a.indexOf(c) === i).slice(0, 4);
  const { data, error, retry } = useApi<{ rows: Row[] }>(period ? `provinces?period=${period}` : null);
  const history = useApi<{ rows: Row[] }>(period && tab === "detail" ? `provinces/${code}/history?period=${period}` : null);
  const compare = useApi<{ rows: Row[] }>(period && chosen.length && tab === "compare" ? `comparison?period=${period}&codes=${chosen.join(",")}` : null);
  const [metric, setMetric] = useState("credits_million_baht"), [index, setIndex] = useState(false), [hideBangkok, setHideBangkok] = useState(true), [scatterScope, setScatterScope] = useState("selected"), [selectionMessage, setSelectionMessage] = useState("");
  const applied = { gpp: threshold(params.get("gpp"), defaults.gpp), credit: threshold(params.get("credit"), defaults.credit), density: threshold(params.get("density"), defaults.density), exclude: params.get("exclude") !== "false" };
  const [draft, setDraft] = useState(applied);
  const filterKey = [applied.gpp, applied.credit, applied.density, applied.exclude].join("|");
  useEffect(() => { setDraft({ gpp: applied.gpp, credit: applied.credit, density: applied.density, exclude: applied.exclude }); }, [filterKey]); // URL is the applied filter source of truth.
  if (!data) return <DataState error={error} retry={retry} />;
  const current = data.rows.find(r => r.province_code === code);
  const openProvince = (row: Row) => router.push(href("/provinces", { province: String(row.province_code), tab: "detail" }));
  const select = (row: Row) => {
    const c = Number(row.province_code);
    if (!chosen.includes(c) && chosen.length === 4) { setSelectionMessage("เปรียบเทียบได้สูงสุด 4 จังหวัด กรุณานำจังหวัดเดิมออกก่อน"); return; }
    setSelectionMessage(""); setParams({ compare: (chosen.includes(c) ? chosen.filter(v => v !== c) : [...chosen, c]).join(",") });
  };
  const comparisonRows = chosen.flatMap(c => data.rows.filter(r => r.province_code === c));
  const candidates = data.rows.filter(r => r.gpp_million_baht != null && r.branches_per_100k != null && (!applied.exclude || r.province_code !== 10) && Number(r.gpp_million_baht) >= applied.gpp && Number(r.credits_million_baht) >= applied.credit && Number(r.branches_per_100k) <= applied.density);
  const missing = data.rows.filter(r => r.gpp_million_baht == null || r.branches_per_100k == null).length;
  const scatterBase = scatterScope === "selected" ? comparisonRows : data.rows;
  const paired = scatterBase.filter(r => r.gpp_million_baht != null && (scatterScope === "selected" || !hideBangkok || r.province_code !== 10));
  const comparisonTrend: Row[] = [];
  if (compare.data) {
    const bases: Record<number, number | null> = {};
    chosen.forEach(c => { const first = compare.data!.rows.find(r => r.province_code === c); bases[c] = first?.[metric] != null && Number(first[metric]) !== 0 ? Number(first[metric]) : null; });
    for (const row of compare.data.rows) {
      let target = comparisonTrend.find(r => r.period === row.period);
      if (!target) { target = { period: row.period }; comparisonTrend.push(target); }
      const c = Number(row.province_code), raw = row[metric];
      target["p" + c] = raw == null ? null : index ? bases[c] ? Number(raw) / bases[c]! * 100 : null : Number(raw);
    }
  }
  return <>
    <PageHeading title="วิเคราะห์จังหวัด" description="เปรียบเทียบตลาดและคัดเลือกพื้นที่สำหรับศึกษาต่อ" />
    <div className="province-controls"><label><span>จังหวัด</span><select aria-label="จังหวัด" value={code} onChange={e => setParams({ province: e.target.value })}>{meta?.provinces.map(p => <option key={String(p.province_code)} value={String(p.province_code)}>{p.name_th}</option>)}</select></label><button className="button primary" disabled={!current || chosen.includes(code)} onClick={() => current && select(current)}>เพิ่มจังหวัดเพื่อเปรียบเทียบ</button>{chosen.length > 0 && <button className="button" onClick={() => setParams({ tab: "compare" })}>ดูการเปรียบเทียบ ({chosen.length})</button>}</div>
    <p className="muted control-hint">เลือกได้สูงสุด 4 จังหวัด · GPP คือผลิตภัณฑ์มวลรวมจังหวัด · YoY คือการเปลี่ยนแปลงเทียบเดือนเดียวกันปีก่อน</p>
    <div className="tabs" aria-label="มุมมองจังหวัด">{[["detail", "รายละเอียดจังหวัด"], ["compare", "เปรียบเทียบ"], ["screen", "คัดกรองพื้นที่"]].map(([key, title]) => <button key={key} className={tab === key ? "active" : ""} aria-pressed={tab === key} onClick={() => setParams({ tab: key })}>{title}</button>)}</div>
    {selectionMessage && <p className="notice" role="status">{selectionMessage}</p>}
    {tab === "detail" && (!current ? <div className="empty">ไม่พบจังหวัดที่เลือก กรุณาเลือกจังหวัดจากรายการ</div> : <>
      <section className="kpis four">{["credits_million_baht", "deposits_million_baht", "credit_deposit_ratio_pct", "branches_per_100k"].map(k => <div className="kpi" key={k}><div className="kpi-label">{metricDefs[k].label}</div><div className="kpi-value">{number(current[k], /pct|per_100k/.test(k) ? 2 : 0)}<small>{metricDefs[k].unit}</small></div></div>)}</section>
      <div className="two-column balanced"><section className="panel"><div className="panel-heading"><h2>แนวโน้ม {current.name_th}</h2><select aria-label="ตัวชี้วัดจังหวัด" value={metric} onChange={e => setMetric(e.target.value)}>{["credits_million_baht", "deposits_million_baht", "branches"].map(k => <option key={k} value={k}>{metricDefs[k].label}</option>)}</select></div>{history.data ? <TrendChart rows={history.data.rows} series={[{ key: metric, name: metricDefs[metric].label, color: "#087d65" }]} unit={metricDefs[metric].unit} /> : <DataState error={history.error} retry={history.retry} />}</section><aside className="panel"><h2>บริบทจังหวัด</h2><dl className="definition-list"><dt>GPP (ล้านบาท)</dt><dd>{number(current.gpp_million_baht)}</dd><dt>ปี GPP (ค.ศ.)</dt><dd>{current.gpp_reference_year ?? "ยังไม่มีข้อมูลที่ใช้ได้"}</dd><dt>ประชากรตามทะเบียน</dt><dd>{number(current.population)} คน</dd><dt>ปีประชากร (ค.ศ.)</dt><dd>{current.population_reference_year ?? "ไม่มีข้อมูล"}</dd><dt>สาขา</dt><dd>{number(current.branches)} แห่ง</dd><dt>สินเชื่อ YoY</dt><dd>{number(current.credit_yoy_pct, 2)}{current.credit_yoy_pct != null ? "%" : ""}</dd></dl><p className="notice">ปีอ้างอิง GPP และประชากรต่างจากงวดธนาคาร ประชากรไม่ใช่จำนวนลูกค้า</p></aside></div>
      <section className="panel section"><h2>ประวัติรายเดือน</h2>{history.data && <DataTable rows={history.data.rows} columns={["period", "credits_million_baht", "deposits_million_baht", "branches"]} filename={`province-${code}-${period}`} />}</section>
    </>)}
    {tab === "compare" && <>
      <div className="chip-list">{comparisonRows.map(r => <span className="selection" key={String(r.province_code)}>{r.name_th}<button aria-label={`นำ ${r.name_th} ออกจากการเปรียบเทียบ`} onClick={() => select(r)}><X size={14} /></button></span>)}</div>
      {!chosen.length ? <div className="empty">เลือกจังหวัดด้านบนแล้วกด “เพิ่มจังหวัดเพื่อเปรียบเทียบ” ได้สูงสุด 4 จังหวัด</div> : <>
        <section className="panel"><h2>เปรียบเทียบตัวชี้วัด ณ งวดที่เลือก</h2><ComparisonTable rows={comparisonRows} columns={columns.filter(c => c !== "name_th")} filename={`comparison-${chosen.join("-")}-${period}`} /></section>
        <section className="panel section"><div className="panel-heading"><h2>แนวโน้มเปรียบเทียบ</h2><div className="toolbar"><select aria-label="ตัวชี้วัดเปรียบเทียบ" value={metric} onChange={e => setMetric(e.target.value)}>{["credits_million_baht", "deposits_million_baht", "branches"].map(k => <option key={k} value={k}>{metricDefs[k].label}</option>)}</select><label><input type="checkbox" checked={index} onChange={e => setIndex(e.target.checked)} /> ดัชนีเริ่มต้น 100</label></div></div>{compare.data ? <TrendChart rows={comparisonTrend} series={comparisonRows.map(r => ({ key: "p" + r.province_code, name: String(r.name_th) }))} unit={index ? "จุดดัชนี" : metricDefs[metric].unit} /> : <DataState error={compare.error} retry={compare.retry} />}<p className="muted">{index ? "ดัชนีเทียบงวดแรกที่แสดง = 100 ใช้ดูการเปลี่ยนแปลง ไม่ใช่ยอดเงินจริง; ถ้าค่าเริ่มต้นเป็นศูนย์จะไม่คำนวณดัชนี" : `หน่วย: ${metricDefs[metric].unit}`}</p></section>
      </>}
      <section className="panel section"><div className="panel-heading"><div><h2>GPP เทียบสินเชื่อ</h2><p className="muted">GPP คือผลิตภัณฑ์มวลรวมจังหวัด · หน่วยทั้งสองแกน: ล้านบาท</p></div><label><span>ขอบเขตของกราฟ</span><select aria-label="ขอบเขตกราฟ GPP" value={scatterScope} onChange={e => setScatterScope(e.target.value)}><option value="selected">เฉพาะจังหวัดที่เลือก</option><option value="all">ทุกจังหวัด</option></select></label></div>
        {scatterScope === "all" && <label className="checkbox-line"><input type="checkbox" checked={hideBangkok} onChange={e => setHideBangkok(e.target.checked)} /> ไม่รวมกรุงเทพมหานครในกราฟ</label>}
        <p className="muted" role="status">แสดง {paired.length} จังหวัด · {scatterScope === "selected" ? "เฉพาะจังหวัดที่เลือก" : hideBangkok ? "ภาพรวมทุกจังหวัด ยกเว้นกรุงเทพมหานคร" : "ภาพรวมทุกจังหวัด"}</p>
        {paired.length ? <GppScatter rows={paired} selected={chosen} onProvince={openProvince} /> : <div className="empty">{!chosen.length && scatterScope === "selected" ? "เลือกจังหวัดเพื่อเปรียบเทียบ หรือเปลี่ยนขอบเขตเป็นทุกจังหวัด" : "ไม่มี GPP ที่ผ่านเงื่อนไขวันเผยแพร่ในขอบเขตที่เลือก"}</div>}
        <p className="muted">GPP รายปีเทียบยอดสินเชื่อรายเดือน การเคลื่อนไหวร่วมกันไม่ได้ยืนยันเหตุและผล · เลือกจุดเพื่อเปิดรายละเอียดจังหวัด</p>
        {paired.length > 0 && <details className="sql"><summary>ดูข้อมูลจังหวัดในกราฟ</summary><DataTable rows={paired} columns={["name_th", "gpp_million_baht", "gpp_reference_year", "credits_million_baht"]} filename={`gpp-${scatterScope}-${period}`} onProvince={openProvince} /></details>}
      </section>
    </>}
    {tab === "screen" && <><div className="screen-layout"><form className="filter-rail" onSubmit={e => { e.preventDefault(); setParams({ gpp: String(draft.gpp), credit: String(draft.credit), density: String(draft.density), exclude: String(draft.exclude) }); }}><h2>ตั้งค่าเกณฑ์คัดกรอง</h2>
      <label>GPP ขั้นต่ำ (ล้านบาท)<input aria-label="GPP ขั้นต่ำ" type="number" min="0" step="1000" required value={draft.gpp} onChange={e => setDraft({ ...draft, gpp: Number(e.target.value) })} /></label>
      <label>สินเชื่อขั้นต่ำ (ล้านบาท)<input aria-label="สินเชื่อขั้นต่ำ" type="number" min="0" step="1000" required value={draft.credit} onChange={e => setDraft({ ...draft, credit: Number(e.target.value) })} /></label>
      <label>สาขาต่อแสนคนสูงสุด<input aria-label="สาขาต่อแสนคนสูงสุด" type="number" min="0" step="0.1" required value={draft.density} onChange={e => setDraft({ ...draft, density: Number(e.target.value) })} /><input aria-label="ปรับความหนาแน่นสาขา" type="range" min="0" max="50" step="0.1" value={Math.min(50, draft.density)} onChange={e => setDraft({ ...draft, density: Number(e.target.value) })} /></label>
      <label className="checkbox"><input type="checkbox" checked={draft.exclude} onChange={e => setDraft({ ...draft, exclude: e.target.checked })} /> ไม่รวมกรุงเทพมหานคร</label><button className="button primary" type="submit">ใช้เกณฑ์</button><button className="button" type="button" onClick={() => { setDraft(defaults); setParams({ gpp: null, credit: null, density: null, exclude: null }); }}>คืนค่าเริ่มต้น</button><p className="muted section">กรุงเทพฯ อาจได้รับผลจากการบันทึกสำนักงานใหญ่</p></form>
      <div><section className="panel"><div className="panel-heading"><h2>{number(candidates.length)} จังหวัดผ่านเกณฑ์</h2><button className="button" disabled={!chosen.length} onClick={() => setParams({ tab: "compare" })}>เปรียบเทียบที่เลือก ({chosen.length})</button></div><p className="muted">เกณฑ์ที่ใช้: GPP ≥ {number(applied.gpp)} ล้านบาท · สินเชื่อ ≥ {number(applied.credit)} ล้านบาท · สาขาต่อแสนคน ≤ {number(applied.density, 1)}</p><p className="muted">{missing ? `${missing} จังหวัดมีข้อมูล GPP หรือประชากรไม่ครบ จึงไม่รวมในการประเมิน` : "ทุกจังหวัดมีข้อมูล GPP และประชากรที่ใช้ประเมินเกณฑ์ได้"}</p><DataTable rows={candidates} columns={["name_th", "gpp_million_baht", "credits_million_baht", "branches_per_100k", "gpp_reference_year", "population_reference_year"]} filename={`shortlist-gpp${applied.gpp}-credit${applied.credit}-density${applied.density}-exclude${applied.exclude}-${period}`} initialSort="gpp_million_baht" search onProvince={openProvince} selected={chosen} onSelect={select} /></section>
      <section className="panel section"><h2>GPP เทียบสินเชื่อ — จังหวัดผ่านเกณฑ์</h2>{candidates.length ? <GppScatter rows={candidates} onProvince={openProvince} /> : <div className="empty">ไม่มีจังหวัดผ่านเกณฑ์ ลองลดเกณฑ์หรือเปลี่ยนงวด</div>}</section></div></div><p className="notice">รายชื่อพื้นที่นี้ใช้เป็นจุดเริ่มต้นสำหรับศึกษาต่อ การตัดสินใจเปิดสาขาหรือปล่อยสินเชื่อต้องพิจารณาการแข่งขัน รายได้ คุณภาพสินเชื่อ และต้นทุนเพิ่มเติม</p></>}
    <Footer period={period} />
  </>;
}
