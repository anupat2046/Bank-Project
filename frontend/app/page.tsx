"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { DataState, Footer, PageHeading, useWorkspace } from "@/components/shell";
import { DataTable } from "@/components/table";
import { TrendChart } from "@/components/charts";
import { Overview, Row, calendarDate, month, number, useApi } from "@/lib/data";

export default function OverviewPage() {
  const { period, href } = useWorkspace(), router = useRouter();
  const { data, error, retry } = useApi<Overview>(period ? `overview?period=${period}` : null);
  const [range, setRange] = useState("12"), [metric, setMetric] = useState("credits_million_baht");
  if (!data) return <DataState error={error} retry={retry} />;
  const trend = (range === "12" ? data.trend.slice(-12) : data.trend).map(r => ({ ...r, credits: Number(r.credits) / 1e6, deposits: Number(r.deposits) / 1e6 }));
  const openProvince = (row: Row) => router.push(href("/provinces", { province: String(row.province_code) }));
  const yoy = (key: string) => data.changes[key] == null ? "ไม่มีงวดเปรียบเทียบปีก่อน" : `${Number(data.changes[key]) >= 0 ? "+" : ""}${number(data.changes[key], 2)}% YoY`;
  return <>
    <PageHeading title="ภาพรวมตลาดธนาคาร" description="สินเชื่อ เงินฝาก และเครือข่ายสาขาระดับประเทศ" />
    <p className="data-context">ข้อมูลล่าสุดในคลัง: {month(data.latest_period)} · กำลังแสดง: {month(period)} · YoY เทียบเดือนเดียวกันปีก่อน</p>
    <section className="kpis" aria-label="ตัวเลขหลัก">
      {[{ key: "credits", name: "สินเชื่อรวม", value: Number(data.totals.credits) / 1e6, unit: "ล้านล้านบาท", decimals: 2 }, { key: "deposits", name: "เงินฝากรวม", value: Number(data.totals.deposits) / 1e6, unit: "ล้านล้านบาท", decimals: 2 }, { key: "branches", name: "จำนวนสาขา", value: data.totals.branches, unit: "แห่ง", decimals: 0 }].map(k => <div key={k.key} className="kpi"><div className="kpi-label">{k.name}</div><div className="kpi-value">{number(k.value, k.decimals)}<small>{k.unit}</small></div><div className="kpi-delta"><b>{yoy(k.key)}</b>{k.key === "branches" && data.changes.branch_change != null ? ` · ${number(data.changes.branch_change)} แห่ง` : ""}</div></div>)}
    </section>
    <section className="panel"><div className="panel-heading"><div><h2>แนวโน้มสินเชื่อและเงินฝาก</h2><p className="muted">หน่วย: ล้านล้านบาท · ยอดคงค้าง ณ สิ้นงวด</p></div><div className="segment" aria-label="ช่วงเวลาของกราฟ"><button className={range === "12" ? "active" : ""} aria-pressed={range === "12"} onClick={() => setRange("12")}>12 เดือน</button><button className={range === "all" ? "active" : ""} aria-pressed={range === "all"} onClick={() => setRange("all")}>ทั้งหมด</button></div></div>
      <TrendChart rows={trend} series={[{ key: "credits", name: "สินเชื่อรวม" }, { key: "deposits", name: "เงินฝากรวม" }]} unit="ล้านล้านบาท" height={215} />
      <div className="policy-heading"><h3>ดอกเบี้ยนโยบาย ณ สิ้นงวด</h3><span>{number(data.totals.policy_rate_pct, 2)}% · มติ {calendarDate(data.totals.policy_event_date)}</span></div>
      <TrendChart rows={trend} series={[{ key: "policy_rate_pct", name: "ดอกเบี้ยนโยบาย", color: "#62718a" }]} unit="%" height={150} policy />
      <p className="muted">ดอกเบี้ยใช้เป็นบริบท การเคลื่อนไหวร่วมกันไม่พิสูจน์เหตุและผล</p>
    </section>
    <div className="two-column section"><section className="panel"><div className="panel-heading"><h2>ตลาดรายจังหวัด</h2><select aria-label="จัดอันดับตาม" value={metric} onChange={e => setMetric(e.target.value)}><option value="credits_million_baht">สินเชื่อ</option><option value="deposits_million_baht">เงินฝาก</option><option value="credit_deposit_ratio_pct">สินเชื่อ/เงินฝาก</option></select></div><DataTable key={metric + period} rows={data.provinces} columns={["name_th", "credits_million_baht", "deposits_million_baht", "branches", ...(metric === "credit_deposit_ratio_pct" ? [metric] : [])]} initialSort={metric} search filename={`province-market-${period}`} onProvince={openProvince} /></section>
      <aside className="panel insights"><h2>ข้อสังเกตจากข้อมูล</h2><div className="insight"><p>กรุงเทพฯ มีสัดส่วนสินเชื่อที่บันทึก</p><strong>{number(data.concentration.bangkok_share_pct, 2)}%</strong><p>ของยอดรวมทั้งประเทศ</p></div><div className="insight"><p>5 จังหวัดแรก รวมกรุงเทพฯ</p><strong>{number(data.concentration.top5_share_pct, 2)}%</strong><p>ของยอดสินเชื่อรวม</p></div><Link href={href("/questions", { qid: "CQ10" })}>ดูวิธีคำนวณ <ArrowRight size={14} /></Link><p className="notice">ที่ตั้งการบันทึกรายการไม่ใช่ที่อยู่ผู้กู้ และไม่ใช่ส่วนแบ่งธนาคารรายแห่ง</p></aside>
    </div>
    <details className="sql"><summary>วิธีคำนวณตัวเลขหลักและ YoY</summary><p>ยอดรวมคือผลรวม 77 จังหวัดในเดือนเดียวกัน · YoY คือการเปลี่ยนแปลงเทียบเดือนเดียวกันปีก่อน = (ยอดงวดปัจจุบัน − ยอดเดือนเดียวกันปีก่อน) ÷ ยอดปีก่อน × 100 · สาขาเปลี่ยนแปลง = จำนวนงวดปัจจุบัน − จำนวนปีก่อน · งวดที่ใช้: {month(period)}</p><DataTable rows={data.trend} columns={["period", "credits", "deposits", "branches", "policy_rate_pct"]} filename={`national-trend-${period}`} /></details>
    <Footer period={period} />
  </>;
}
