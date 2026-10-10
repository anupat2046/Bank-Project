"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { DataState, Footer, PageHeading, useWorkspace } from "@/components/shell";
import { DataTable } from "@/components/table";
import { Bars, TrendChart } from "@/components/charts";
import { Question, QuestionResult, Row, label, metricDefs, number, useApi } from "@/lib/data";

const business: Record<string, [string, string]> = {
  CQ01: ["ดูความสม่ำเสมอของการเติบโต ไม่ใช้ยอดเดือนเดียวเป็นตัวแทนทั้งตลาด", "ตรวจประเภทสินเชื่อและฐานเปรียบเทียบเพิ่มเติมก่อนอธิบายสาเหตุการเติบโต"],
  CQ02: ["เห็นพื้นที่ที่เงินฝากและสินเชื่อเปลี่ยนแปลงในอัตราต่างกัน", "ศึกษาการเคลื่อนย้ายเงินฝากและโครงสร้างธุรกิจ โดยไม่ตีความเป็นสภาพคล่องรายธนาคาร"],
  CQ03: ["เทียบเครือข่ายสาขาเมื่อคำนึงถึงขนาดประชากรตามทะเบียน", "ตรวจบริการดิจิทัล ระยะทาง และประชากรแฝงก่อนสรุปเรื่องการเข้าถึงบริการ"],
  CQ04: ["เปรียบเทียบตลาดสินเชื่อของจังหวัดที่มีขนาดเศรษฐกิจใกล้กัน", "ตรวจโครงสร้างอุตสาหกรรมและที่ตั้งการบันทึกสินเชื่อ; GPP ใกล้กันไม่แปลว่าความต้องการสินเชื่อเท่ากัน"],
  CQ05: ["ดูบริบทดอกเบี้ยพร้อมยอดสินเชื่อและเงินฝากบนแกนเวลาเดียวกัน", "ต้องมีการวิเคราะห์เพิ่มเติมก่อนสรุปว่าดอกเบี้ยทำให้ยอดสินเชื่อเปลี่ยน"],
  CQ06: ["ค้นหาพื้นที่ที่เครือข่ายสาขาและยอดสินเชื่อเคลื่อนไหวคนละทิศ", "ศึกษาช่องทางบริการและโครงสร้างผู้กู้; ไม่สรุปว่าการลดสาขาทำให้สินเชื่อเพิ่ม"],
  CQ07: ["สร้างรายชื่อพื้นที่สำหรับศึกษาต่อด้วยเกณฑ์ที่ตรวจสอบได้", "ตรวจการแข่งขัน ต้นทุน รายได้ และคุณภาพสินเชื่อก่อนตัดสินใจเชิงธุรกิจ"],
  CQ08: ["เปรียบเทียบโครงสร้างยอดสินเชื่อและเงินฝากระดับพื้นที่", "ตรวจ head-office booking และข้อจำกัดระดับจังหวัด ไม่ใช้แทน liquidity ratio รายธนาคาร"],
  CQ09: ["เทียบยอดเงินฝากกับขนาดประชากรตามทะเบียนของจังหวัด", "ตรวจประชากรแฝงและบัญชีนิติบุคคล; ตัวเลขนี้ไม่ใช่เงินออมเฉลี่ยของลูกค้า"],
  CQ10: ["เข้าใจการกระจุกตัวของยอดสินเชื่อที่บันทึกในแต่ละพื้นที่", "ศึกษาผลของการบันทึกสำนักงานใหญ่และโครงสร้างเศรษฐกิจ ก่อนสรุปตำแหน่งความต้องการสินเชื่อ"],
};
const defaultMetric: Record<string, string> = { CQ01: "positive_months", CQ02: "growth_gap_pp", CQ03: "branches_per_100k", CQ04: "credit_size_ratio", CQ05: "credits_million", CQ06: "credit_yoy_pct", CQ07: "gpp_million_baht", CQ08: "credit_deposit_ratio_pct", CQ09: "deposits_baht_per_person", CQ10: "bangkok_share_pct" };

export default function QuestionsPage() {
  const { period, href, setParams } = useWorkspace(), params = useSearchParams();
  const qid = params.get("qid") || "CQ01";
  const catalog = useApi<Question[]>("questions");
  const result = useApi<QuestionResult>(period ? `questions/${qid}?period=${period}` : null);
  const [selectedMetric, setSelectedMetric] = useState<{ qid: string; key: string } | null>(null);
  const groups = [["การเติบโตของตลาด", ["CQ01", "CQ02", "CQ06"]], ["เครือข่ายและขนาดเศรษฐกิจ", ["CQ03", "CQ04", "CQ07"]], ["บริบทและโครงสร้างตลาด", ["CQ05", "CQ08", "CQ09", "CQ10"]]] as [string, string[]][];
  const data = result.data;
  const numeric = data?.rows.length ? Object.keys(data.rows[0]).filter(k => typeof data.rows[0][k] === "number" && !/year|population$|observed_months/.test(k)) : [];
  const metric = selectedMetric?.qid === qid ? selectedMetric.key : defaultMetric[qid];
  const chartRows = data?.rows.map(r => ({ ...r, pair: `${r.province_a} / ${r.province_b}` })) || [];
  const shares: Row[] = data?.rows.length && qid === "CQ10" ? [{ name_th: "กรุงเทพฯ", value: data.rows[0].bangkok_share_pct }, { name_th: "5 จังหวัดแรก (รวมกรุงเทพฯ)", value: data.rows[0].top5_share_pct }] : [];
  return <>
    <PageHeading title="คำถามธุรกิจ" description="10 คำถาม พร้อมผลจริงและวิธีคำนวณ" />
    {catalog.data && <select className="question-mobile" aria-label="เลือกคำถามธุรกิจ" value={qid} onChange={e => setParams({ qid: e.target.value })}>{catalog.data.map(q => <option key={q.id} value={q.id}>{q.id} · {q.title}</option>)}</select>}
    <div className="questions-layout"><nav className="question-list" aria-label="รายการคำถามธุรกิจ">{catalog.data ? groups.map(([group, ids]) => <div key={group}><h3>{group}</h3>{ids.map(id => { const q = catalog.data!.find(q => q.id === id)!; return <button key={id} className={`question-item ${qid === id ? "active" : ""}`} aria-pressed={qid === id} onClick={() => setParams({ qid: id })}><span>{id}</span><span>{q.title}</span></button>; })}</div>) : <DataState error={catalog.error} retry={catalog.retry} />}</nav>
      <section className="question-answer">{!data ? <DataState error={result.error} retry={result.retry} /> : <>
        <h2>{data.title}</h2><p className="muted">{business[qid]?.[0]}</p><p className="muted">แหล่งข้อมูล: {data.sources} · ประเมินเฉพาะข้อมูลไม่เกินงวดที่เลือก</p>
        {qid === "CQ10" && data.rows.length > 0 && <div className="kpis">{[["bangkok_share_pct", "กรุงเทพฯ"], ["top5_share_pct", "5 จังหวัดแรก รวมกรุงเทพฯ"]].map(([key, name]) => <div className="kpi" key={key}><div className="kpi-label">{name}</div><div className="kpi-value" style={{ color: "var(--teal)" }}>{number(data.rows[0][key], 2)}<small>%</small></div><p className="muted">ของสินเชื่อที่บันทึกทั่วประเทศ</p></div>)}</div>}
        {!data.rows.length ? <div className="empty">ไม่มีข้อมูลที่ผ่านเงื่อนไขสำหรับงวดนี้ อาจยังไม่มีคู่ข้อมูล YoY ครบ หรือข้อมูล GPP ยังไม่ถึงวันเผยแพร่</div> : <>
          {qid !== "CQ10" && qid !== "CQ05" && <label className="toolbar"><span className="muted">ตัวชี้วัดในกราฟ</span><select aria-label="ตัวชี้วัดคำถาม" value={metric} onChange={e => setSelectedMetric({ qid, key: e.target.value })}>{numeric.map(k => <option key={k} value={k}>{label(k)}</option>)}</select></label>}
          {qid === "CQ10" ? <Bars rows={shares} valueKey="value" unit="%" /> : qid === "CQ05" ? <><TrendChart rows={data.rows} series={[{ key: "credits_million", name: "สินเชื่อรวม" }, { key: "deposits_million", name: "เงินฝากรวม" }]} unit="ล้านบาท" /><TrendChart rows={data.rows} series={[{ key: "policy_rate_pct", name: "ดอกเบี้ยนโยบาย", color: "#8a9ab0" }]} unit="%" height={145} policy /></> : <Bars rows={chartRows} valueKey={metric} nameKey={qid === "CQ04" ? "pair" : "name_th"} unit={metricDefs[metric]?.unit || ""} />}
          <section className="section"><h3>ตารางผลลัพธ์</h3><DataTable rows={data.rows} filename={`${qid}-${period}`} /></section>
        </>}
        <div className="split-explanation"><div><h3>ผลที่พบ</h3><p>{qid === "CQ10" && data.rows.length ? `กรุงเทพฯ มีสัดส่วน ${number(data.rows[0].bangkok_share_pct, 2)}% และ 5 จังหวัดแรกมี ${number(data.rows[0].top5_share_pct, 2)}% ของยอดรวม ณ งวดที่เลือก` : `พบ ${data.rows.length} แถวที่ผ่านเงื่อนไข query; อ่านค่าจากตารางและตรวจสูตรก่อนตีความ`}</p></div><div><h3>สิ่งที่ควรศึกษาต่อ</h3><p>{business[qid]?.[1]}</p></div></div>
        <p className="notice warning">{data.caveat}</p>
        <details className="sql"><summary>SQL ฟิลด์ และพารามิเตอร์ที่ใช้</summary><pre>{data.sql}</pre><p>พารามิเตอร์: {JSON.stringify(data.parameters)} · ตาราง cq_mart จำกัด period ≤ as_of</p><p>ฟิลด์: {data.fields}</p></details>
        <Link className="button subtle section" href={href("/provinces", { tab: qid === "CQ07" ? "screen" : "compare" })}>วิเคราะห์จังหวัดต่อ</Link>
      </>}</section>
    </div><Footer period={period} />
  </>;
}
