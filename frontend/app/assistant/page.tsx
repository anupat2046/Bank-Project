"use client";

import { useEffect, useRef, useState } from "react";
import { Download, MessageSquare, Send, Plus } from "lucide-react";
import { Footer, PageHeading } from "@/components/shell";
import { DataTable } from "@/components/table";
import { Bars, TrendChart } from "@/components/charts";
import { useConversation } from "@/components/conversation-state";
import { ChatReply, Row, downloadCsv, month, readableText } from "@/lib/data";

const examples = ["สินเชื่อต่อประชากรสูงสุด 10 จังหวัด พร้อมสินเชื่อต่อสาขาและ YoY", "เปรียบเทียบสินเชื่อต่อประชากรเชียงใหม่และชลบุรี", "แนวโน้มเงินฝากย้อนหลัง"];
function replyHeading(reply: ChatReply) {
  if (reply.mode === "clarification") return "ขอรายละเอียดเพิ่มเติม";
  if (reply.error) return "ยังไม่สามารถตอบคำถามนี้ได้";
  if (reply.mode === "capabilities" || reply.mode === "greeting") return "ผู้ช่วยทำอะไรได้บ้าง";
  if (reply.conversation_route === "explanation" || reply.mode === "explanation") return "คำอธิบายผลล่าสุด";
  return "คำตอบจากผู้ช่วย";
}
function modeLabel(reply: ChatReply) {
  if (reply.provider_status?.circuit_open) return "ผู้ให้บริการ AI ไม่พร้อม · ใช้โหมดสำรองเมื่อรองรับ";
  return /fallback|offline/.test(reply.routing_mode || "") ? "ใช้โหมดสำรองสำหรับวิเคราะห์ข้อมูล" : /rules/i.test(reply.mode) ? "AI จัดเส้นทาง · คำนวณด้วยแผนที่ตรวจสอบได้" : "ผู้ช่วยวิเคราะห์ข้อมูล";
}

function ProviderNotice({ reply }: { reply: ChatReply }) {
  const health = reply.provider_status;
  if (!health?.circuit_open) return null;
  const reason = health.last_failure === "quota_exhausted"
    ? "ผู้ให้บริการ AI แจ้งว่าถึงข้อจำกัดทรัพยากรหรือ quota ผู้ดูแลควรตรวจ usage และข้อจำกัดในบัญชีผู้ให้บริการ"
    : health.last_failure === "authentication_failed"
      ? "การยืนยันตัวตนกับผู้ให้บริการ AI ไม่สำเร็จ ผู้ดูแลควรตรวจ API key และสิทธิ์การใช้งาน"
      : "ผู้ให้บริการ AI ไม่พร้อมใช้งานชั่วคราว ระบบพักการเรียกซ้ำและจะลองใหม่เมื่อมีคำขอหลังพ้นช่วงพัก";
  return <p className="notice warning" role="status">{reason} · คำถามที่รองรับยังคำนวณจากคลังข้อมูลด้วยโหมดสำรองได้ การได้คำตอบไม่ได้หมายความว่า AI ทำงานสำเร็จในรอบนี้</p>;
}

function Analysis({ reply, index }: { reply: ChatReply; index: number }) {
  const result = reply.result!;
  const metrics = result.metrics || [{ key: "value", label: result.metric_label, unit: result.unit, formula: "" }];
  const [metricKey, setMetricKey] = useState(metrics[0].key);
  const [view, setView] = useState(result.chart?.kind === "table" ? "table" : "chart");
  const metric = metrics.find(m => m.key === metricKey) || metrics[0];
  const columns = [...(result.plan.group_by === "period" ? ["period"] : []), ...(result.rows.some(r => r.name_th) ? ["name_th"] : []), ...metrics.map(m => m.key), ...["population_reference_year", "gpp_reference_year"].filter(key => result.rows.some(row => row[key] != null))];
  const labels = Object.fromEntries(metrics.map(m => [m.key, `${m.label} (${m.unit})`]));
  const comparison = result.rows.some(r => r.name_th) && result.plan.group_by === "period";
  const names = [...new Set(result.rows.map(r => String(r.name_th)))];
  const trendRows: Row[] = comparison ? [...new Set(result.rows.map(r => r.period))].map(period => Object.fromEntries([["period", period], ...names.map(name => [name, result.rows.find(r => r.period === period && r.name_th === name)?.[metric.key] ?? null])]) as Row) : result.rows;
  const kind = result.chart?.kind || (result.plan.group_by === "period" ? "line" : "bar");
  const barRows = result.rows.map(r => ({ ...r, chart_name: comparison ? `${r.name_th} · ${month(r.period)}` : r.name_th || month(r.period) }));
  const periods = [...new Set(result.rows.map(row => String(row.period || result.period || "")))].filter(Boolean).sort();
  const periodLabel = result.plan.group_by === "period" && periods.length ? `${month(periods[0], true)} – ${month(periods[periods.length - 1], true)} · ${periods.length} เดือน` : month(result.period);
  return <>
    <div className="panel-heading"><div><h2>{result.metric_label}</h2><p className="muted">{result.rows.length} รายการ · {periodLabel} · {result.scope}</p></div><button className="button subtle" disabled={!result.rows.length} onClick={() => downloadCsv(result.rows, `chat-${result.plan.metric}-${index + 1}`, columns, labels)}><Download size={15} />ดาวน์โหลด CSV</button></div>
    <p className="findings-summary">{readableText(reply.answer)}</p>
    <details className="sql"><summary>ระบบเข้าใจคำถามและสูตรว่าอย่างไร</summary><p>ตัวจัดอันดับ: {result.metric_label} · ขอบเขต: {result.scope} · จังหวัดที่คำนวณได้ก่อน Top N: {result.plan.group_by === "province" ? result.eligible_count : "เป็นแนวโน้มรายเดือน"}</p><p>จังหวัด: {result.plan.province || result.plan.provinces?.join(" / ") || "ทุกจังหวัดในขอบเขต"}</p><pre>{JSON.stringify({ min_population: result.plan.min_population, min_credits_million: result.plan.min_credits, min_gpp_million: result.plan.min_gpp, max_branches_per_100k: result.plan.max_branch_density, start: result.plan.start_period, end: result.plan.end_period }, null, 2)}</pre>{metrics.map(m => <p key={m.key}>{m.label} ({m.unit}): <code>{m.formula}</code></p>)}</details>
    <div className="tabs" aria-label="รูปแบบผลวิเคราะห์"><button aria-pressed={view === "chart"} className={view === "chart" ? "active" : ""} onClick={() => setView("chart")}>กราฟ</button><button aria-pressed={view === "table"} className={view === "table" ? "active" : ""} onClick={() => setView("table")}>ตาราง</button></div>
    {view === "chart" && metrics.length > 1 && <label className="toolbar"><span>ตัวชี้วัดในกราฟ</span><select aria-label="ตัวชี้วัดแชต" value={metric.key} onChange={e => setMetricKey(e.target.value)}>{metrics.map(m => <option key={m.key} value={m.key}>{m.label} ({m.unit})</option>)}</select></label>}
    {result.chart?.notice && <p className="notice">{result.chart.notice}</p>}
    {!result.rows.length ? <div className="empty">ไม่มีข้อมูลที่คำนวณได้ตามเงื่อนไข</div> : view === "table" ? <DataTable rows={result.rows} columns={columns} columnLabels={labels} filename={`chat-${index + 1}`} /> : kind === "line" || kind === "table" && result.plan.group_by === "period" ? <TrendChart key={metric.key} rows={trendRows} series={comparison ? names.map(name => ({ key: name, name })) : [{ key: metric.key, name: metric.label }]} unit={metric.unit} height={330} /> : <Bars rows={barRows} valueKey={metric.key} nameKey="chart_name" unit={metric.unit} />}
    <p className="muted section">แหล่งข้อมูล: {result.sources.join(" · ")}</p><p className="notice warning">{result.caveat}</p><details className="sql"><summary>SQL และรายละเอียดระบบของคำตอบนี้</summary><p>Router: {reply.routing_mode || "ไม่ระบุ"} · Planner: {reply.mode}</p><pre>{result.sql}</pre><pre>{JSON.stringify(result.parameters, null, 2)}</pre></details>
  </>;
}

export default function AssistantPage() {
  const { question, setQuestion, messages, selected, setSelected, pending, failure, mobileView, setMobileView, send, reset } = useConversation();
  const form = useRef<HTMLFormElement>(null), messageList = useRef<HTMLDivElement>(null), resultHeading = useRef<HTMLElement>(null);
  const active = messages[selected], result = active?.reply.result;
  useEffect(() => { const node = messageList.current; if (node) node.scrollTop = node.scrollHeight; }, [messages.length, pending]);
  useEffect(() => { if (active && mobileView === "result" && window.matchMedia("(max-width:850px)").matches) resultHeading.current?.focus({ preventScroll: true }); }, [selected, mobileView, active]);
  return <>
    <PageHeading title="ผู้ช่วยวิเคราะห์" description="ถามเพื่อจัดอันดับ เปรียบเทียบจังหวัด และดูแนวโน้ม พร้อมตรวจสอบข้อมูลประกอบ" />
    <p className="notice assistant-intro">ระบุเดือนในคำถามได้ คำถามใหม่ที่ไม่ระบุเดือนจะใช้ข้อมูลล่าสุดในคลัง ส่วนคำถามต่อเนื่องอาจใช้ช่วงเวลาเดิม · วิเคราะห์ได้เฉพาะข้อมูลตลาด ไม่มีข้อมูลลูกค้ารายบุคคล รายธนาคาร หรือสินเชื่อด้อยคุณภาพ (NPL)</p>
    <p className="muted session-hint">สลับหน้าแล้วกลับมาสนทนาต่อได้ · การรีโหลดหน้าเว็บจะเริ่มบทสนทนาใหม่ · YoY คือการเปลี่ยนแปลงเทียบเดือนเดียวกันปีก่อน</p>
    {active && <ProviderNotice reply={active.reply} />}
    <div className="tabs chat-mobile-tabs"><button className={mobileView === "conversation" ? "active" : ""} onClick={() => setMobileView("conversation")}>บทสนทนา</button><button className={mobileView === "result" ? "active" : ""} onClick={() => setMobileView("result")}>ผลวิเคราะห์</button></div>
    <div className="chat-layout"><section className={`chat-thread ${mobileView !== "conversation" ? "chat-hidden-mobile" : ""}`} aria-label="บทสนทนา"><div className="chat-toolbar"><span>{active ? modeLabel(active.reply) : "พร้อมรับคำถาม"}</span><button className="text-button" disabled={pending} onClick={reset}><Plus size={16} /> เริ่มบทสนทนาใหม่</button></div>
      <div className="chat-messages" ref={messageList}>{messages.length === 0 && <><h3>ต้องการวิเคราะห์เรื่องใด?</h3><p className="muted">เลือกคำถามแนะนำหรือพิมพ์ประเด็นที่ต้องการวิเคราะห์</p><div className="chat-examples">{examples.map(example => <button key={example} disabled={pending} onClick={() => { setQuestion(example); form.current?.querySelector("textarea")?.focus(); }}>{example}</button>)}</div></>}
        {messages.map((m, i) => <div key={i}><div className="message user"><small>คุณ</small>{m.question}</div><button className={`message ${selected === i ? "selected" : ""}`} aria-pressed={selected === i} onClick={() => { setSelected(i); setMobileView("result"); }}><small>{m.reply.error ? "ยังตอบไม่ได้" : "ผู้ช่วยวิเคราะห์"} · เปิดดูคำตอบ</small>{m.reply.result ? `${m.reply.result.metric_label} · ${m.reply.result.rows.length} รายการ · ${month(m.reply.result.period, true)}` : readableText(m.reply.answer)}</button></div>)}
        <span className="sr-only" role="status">{!pending && active ? "ได้รับคำตอบแล้ว เปิดดูได้ในส่วนผลวิเคราะห์" : ""}</span>
        {pending && <p className="notice" role="status">กำลังตีความคำถามและตรวจผลจากคลังข้อมูล…</p>}
        {failure && <div className="notice warning" role="alert">{failure} · คำถามยังอยู่ในช่องพิมพ์ คุณสามารถลองส่งใหม่ได้</div>}
      </div>
      <form className="chat-form" ref={form} onSubmit={e => { e.preventDefault(); void send(); }}><label><span>คำถาม</span><textarea aria-label="คำถาม" placeholder="เช่น แนวโน้มสินเชื่อจังหวัดเชียงใหม่" maxLength={1000} value={question} onChange={e => setQuestion(e.target.value)} disabled={pending} onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); form.current?.requestSubmit(); } }} /></label><div className="chat-form-bottom"><span>{question.length}/1,000 · Ctrl+Enter เพื่อส่ง</span><button className="button primary" type="submit" disabled={pending || !question.trim()}><Send size={15} />{pending ? "กำลังถาม…" : "ส่งคำถาม"}</button></div></form>
    </section>
    <section ref={resultHeading} tabIndex={-1} className={`chat-result ${mobileView !== "result" ? "chat-hidden-mobile" : ""}`} aria-label="ผลวิเคราะห์">{pending ? <div className="chat-result-empty" role="status"><MessageSquare size={30} /><h2>กำลังเตรียมผลวิเคราะห์</h2><p>กำลังตรวจคำถามและคำนวณจากข้อมูลในคลัง</p></div> : !active ? <div className="chat-result-empty"><MessageSquare size={32} strokeWidth={1.5} /><h2>ผลวิเคราะห์ที่ตรวจสอบได้</h2><p>ดูคำตอบพร้อมกราฟ ตาราง หน่วย และแหล่งข้อมูล แล้วเปิดสูตรและ SQL เมื่อต้องการตรวจรายละเอียด</p></div> : active.reply.error || !result ? <div className="state" role={active.reply.error ? "alert" : "status"}><h2>{replyHeading(active.reply)}</h2><p style={{ whiteSpace: "pre-line" }}>{readableText(active.reply.answer)}</p><div className="chat-examples">{active.reply.choices?.map(choice => <button key={choice} onClick={() => { setQuestion(choice); setMobileView("conversation"); }}>{choice}</button>)}</div>{active.reply.choices?.length ? <p className="muted">เลือกคำถามแนะนำ จากนั้นตรวจข้อความและกดส่ง</p> : <button className="button" onClick={() => { setQuestion(active.question); setMobileView("conversation"); form.current?.querySelector("textarea")?.focus(); }}>แก้ไขหรือส่งคำถามอีกครั้ง</button>}</div> : <Analysis key={selected} reply={active.reply} index={selected} />}</section></div><Footer />
  </>;
}
