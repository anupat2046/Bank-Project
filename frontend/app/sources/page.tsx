"use client";

import { useState } from "react";
import { DataState, Footer, PageHeading } from "@/components/shell";
import { Row, month, number, useApi } from "@/lib/data";

type Source = { source: string; title: string; method: string; frequency: string; url: string; sha256: string; reference: string; fetched_at: string; freshness: string };
type Sources = { sources: Source[]; runs: Row[]; coverage: Row };
const time = (v: unknown) => v ? new Date(String(v)).toLocaleString("th-TH", { timeZone: "Asia/Bangkok", dateStyle: "short", timeStyle: "short" }) : "ไม่มีข้อมูล";

export default function SourcesPage() {
  const { data, error, retry } = useApi<Sources>("sources"), [selected, setSelected] = useState("bot");
  if (!data) return <DataState error={error} retry={retry} />;
  const source = data.sources.find(s => s.source === selected) || data.sources[0];
  return <>
    <PageHeading title="แหล่งข้อมูลและคุณภาพ" description="ตรวจที่มา ช่วงเวลา และกติกาการเชื่อมข้อมูล" />
    <section className="coverage-strip"><div><strong>{number(data.coverage.provinces)}</strong><span>จังหวัด</span></div><div><strong>{number(data.coverage.months)}</strong><span>เดือนของข้อมูลธนาคาร</span></div><div><strong>{month(data.coverage.first_period)} – {month(data.coverage.latest_period)}</strong><span>ช่วงข้อมูลในคลัง · {number(data.coverage.rows)} แถวจังหวัด-เดือน</span></div></section>
    <section><h2>รายการแหล่งข้อมูล</h2><p className="muted">คลิกแหล่งข้อมูลเพื่อดู URL ต้นทางและหลักฐานไฟล์</p><div className="table-scroll section source-table"><table><thead><tr><th>แหล่งข้อมูล</th><th>วิธีรับข้อมูล</th><th>งวด / ชุดอ้างอิง</th><th>ดึงล่าสุด (เวลาไทย)</th></tr></thead><tbody>{data.sources.map(s => <tr key={s.source}><td><button className="text-button" aria-pressed={selected === s.source} onClick={() => setSelected(s.source)}>{s.title}</button></td><td>{s.method}</td><td>{s.reference || s.frequency}</td><td>{time(s.fetched_at)}</td></tr>)}</tbody></table></div><p className="notice">วันที่ดึงข้อมูลไม่ใช่งวดข้อมูล และยังไม่ได้ตรวจว่างวดล่าสุดของต้นทางตรงกับในคลังหรือไม่ จึงไม่อ้างว่าแหล่งข้อมูลสดทั้งหมด</p></section>
    <div className="source-grid section"><section><h2>รายละเอียดแหล่งข้อมูลที่เลือก</h2>{source && <div className="source-detail"><h3>{source.title}</h3><p>วิธีรับ: {source.method} · ความถี่: {source.frequency}</p><p>อ้างอิง: {source.reference || "ดูต้นทาง"}</p><p><a href={source.url} target="_blank" rel="noreferrer">เปิดแหล่งข้อมูลต้นทาง</a></p><p>ดึงข้อมูล: {time(source.fetched_at)}</p><p>SHA-256 ของไฟล์ที่ใช้</p><code>{source.sha256}</code></div>}<p className="notice warning">World Bank เป็น REST API จริง ส่วน BOT banking เป็น web table และดอกเบี้ยนโยบายมาจาก workbook ไม่ใช่ BOT API ที่ต้องใช้คีย์</p></section>
      <section><h2>กติกาการเชื่อมข้อมูลตามเวลา</h2><ol className="join-list"><li>Map ชื่อจังหวัดเป็นรหัส DOPA 77 จังหวัด; ชื่อที่ไม่รู้จักต้องไม่ผ่าน validation</li><li>ข้อมูลประชากรใช้ snapshot เดือนธันวาคมล่าสุดที่มีให้ใช้ในงวดนั้น ไม่ใช่จำนวนลูกค้า</li><li>GPP และเงินเฟ้อต้องผ่านเงื่อนไขวันเผยแพร่/ปรับปรุงต้นทางก่อนเชื่อม หากใช้ไม่ได้จะเป็น NULL</li><li>ดอกเบี้ยนโยบายใช้มติล่าสุดที่มีผลไม่เกินสิ้นเดือนของงวดธนาคาร</li><li>ยอดคงค้างรวมได้ข้ามจังหวัดในเดือนเดียวกัน ไม่รวมยอดหลายเดือนเข้าด้วยกัน</li></ol></section></div>
    <section className="panel section"><h2>ความครบถ้วนตามกติกา Join</h2><p className="muted">ทั้งช่วงข้อมูล: GPP ที่ใช้ไม่ได้ {number(data.coverage.missing_gpp_rows)} แถว · ประชากรที่ใช้ไม่ได้ {number(data.coverage.missing_population_rows)} แถว · เงินเฟ้อที่ใช้ไม่ได้ {number(data.coverage.missing_inflation_rows)} แถว</p><p className="muted">World Bank vintage ปัจจุบัน: {String(data.coverage.macro_vintage_date || "ไม่มีข้อมูล")} · หากวันที่ปรับปรุงชุดข้อมูลอยู่หลังงวดธนาคาร ระบบจะไม่ใส่ค่าของ vintage ใหม่ในงวดเก่าเพื่อป้องกัน lookahead; NULL ไม่ใช่ศูนย์</p></section>
    <section className="section"><h2>ประวัติการนำเข้าและสร้างคลังข้อมูล</h2><p className="muted">แสดง 30 งาน ETL ล่าสุด ไม่ใช่หลักฐาน scheduled DAG ต่อเนื่องครบเดือน</p><div className="table-scroll section"><table><thead><tr><th>แหล่ง / งาน</th><th>สถานะ</th><th>จำนวนแถว</th><th>เวลาเริ่ม (ไทย)</th></tr></thead><tbody>{data.runs.map((r, i) => <tr key={i}><td>{r.source}</td><td><span className={`status ${r.status}`}>{r.status === "success" ? "สำเร็จ" : r.status === "failed" ? "ล้มเหลว" : r.status}</span></td><td className="numeric">{number(r.rows_loaded)}</td><td>{time(r.started_at)}</td></tr>)}</tbody></table></div></section><Footer />
  </>;
}
