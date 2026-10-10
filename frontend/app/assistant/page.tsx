"use client";

import { useRef, useState } from "react";
import { Download, MessageSquare, Send, Plus } from "lucide-react";
import { Footer, PageHeading } from "@/components/shell";
import { DataTable } from "@/components/table";
import { Bars, TrendChart } from "@/components/charts";
import { ChatReply, Row, downloadCsv, month } from "@/lib/data";

type Message = { question: string; reply: ChatReply };
const examples = ["สินเชื่อต่อประชากรสูงสุด 10 จังหวัด พร้อมสินเชื่อต่อสาขาและ YoY", "เปรียบเทียบสินเชื่อต่อประชากรเชียงใหม่และชลบุรี", "แนวโน้มเงินฝากย้อนหลัง"];
function replyHeading(reply: ChatReply) {
  if (reply.mode === "clarification") return "ขอรายละเอียดเพิ่มเติม";
  if (reply.error) return "ยังไม่สามารถตอบคำถามนี้ได้";
  if (reply.mode === "capabilities" || reply.mode === "greeting") return "ผู้ช่วยทำอะไรได้บ้าง";
  if (reply.mode === "explanation") return "คำอธิบายผลล่าสุด";
  return "คำตอบจากผู้ช่วย";
}
function modeLabel(reply: ChatReply) {
  const planner = reply.mode.includes("semantic rules") ? "Rules planner" : reply.mode;
  return reply.routing_mode ? `${reply.routing_mode} router · ${planner}` : planner;
}

function Analysis({ reply, index }: { reply: ChatReply; index: number }) {
  const result = reply.result!;
  const metrics = result.metrics || [{ key: "value", label: result.metric_label, unit: result.unit, formula: "" }];
  const [metricKey, setMetricKey] = useState(metrics[0].key);
  const [view, setView] = useState(result.chart?.kind === "table" ? "table" : "chart");
  const metric = metrics.find(m => m.key === metricKey) || metrics[0];
  const columns = [...(result.plan.group_by === "period" ? ["period"] : []), ...(result.rows.some(r => r.name_th) ? ["name_th"] : []), ...metrics.map(m => m.key), "population_reference_year", "gpp_reference_year"];
  const labels = Object.fromEntries(metrics.map(m => [m.key, `${m.label} (${m.unit})`]));
  const comparison = result.rows.some(r => r.name_th) && result.plan.group_by === "period";
  const names = [...new Set(result.rows.map(r => String(r.name_th)))];
  const trendRows: Row[] = comparison ? [...new Set(result.rows.map(r => r.period))].map(period => Object.fromEntries([["period", period], ...names.map(name => [name, result.rows.find(r => r.period === period && r.name_th === name)?.[metric.key] ?? null])]) as Row) : result.rows;
  const kind = result.chart?.kind || (result.plan.group_by === "period" ? "line" : "bar");
  const barRows = result.rows.map(r => ({ ...r, chart_name: comparison ? `${r.name_th} · ${month(r.period)}` : r.name_th || month(r.period) }));
  return <>
    <div className="panel-heading"><div><h2>{result.metric_label}</h2><p className="muted">{result.rows.length} แถว · งวด {month(result.period)} · {result.scope}</p></div><button className="button subtle" disabled={!result.rows.length} onClick={() => downloadCsv(result.rows, `chat-${result.plan.metric}-${index + 1}`, columns, labels)}><Download size={15} />CSV</button></div>
    <p className="notice">{reply.answer}</p>
    <details className="sql"><summary>ระบบเข้าใจคำถามและสูตรว่าอย่างไร</summary><p>ตัวจัดอันดับ: {result.metric_label} · ขอบเขต: {result.scope} · จังหวัดที่คำนวณได้ก่อน Top N: {result.plan.group_by === "province" ? result.eligible_count : "เป็นแนวโน้มรายเดือน"}</p><p>จังหวัด: {result.plan.province || result.plan.provinces?.join(" / ") || "ทุกจังหวัดในขอบเขต"}</p><pre>{JSON.stringify({ min_population: result.plan.min_population, min_credits_million: result.plan.min_credits, min_gpp_million: result.plan.min_gpp, max_branches_per_100k: result.plan.max_branch_density, start: result.plan.start_period, end: result.plan.end_period }, null, 2)}</pre>{metrics.map(m => <p key={m.key}>{m.label} ({m.unit}): <code>{m.formula}</code></p>)}</details>
    <div className="tabs"><button className={view === "chart" ? "active" : ""} onClick={() => setView("chart")}>กราฟ</button><button className={view === "table" ? "active" : ""} onClick={() => setView("table")}>ตาราง</button></div>
    {view === "chart" && metrics.length > 1 && <label className="toolbar"><span>ตัวชี้วัดในกราฟ (แยกหน่วย ไม่รวมคนละหน่วยบนแกนเดียว)</span><select aria-label="ตัวชี้วัดแชต" value={metric.key} onChange={e => setMetricKey(e.target.value)}>{metrics.map(m => <option key={m.key} value={m.key}>{m.label} ({m.unit})</option>)}</select></label>}
    {result.chart?.notice && <p className="notice">{result.chart.notice}</p>}
    {!result.rows.length ? <div className="empty">ไม่มีข้อมูลที่คำนวณได้ตามเงื่อนไข</div> : view === "table" ? <DataTable rows={result.rows} columns={columns} columnLabels={labels} filename={`chat-${index + 1}`} /> : kind === "line" || kind === "table" && result.plan.group_by === "period" ? <TrendChart key={metric.key} rows={trendRows} series={comparison ? names.map(name => ({ key: name, name })) : [{ key: metric.key, name: metric.label }]} unit={metric.unit} height={330} /> : <Bars rows={barRows} valueKey={metric.key} nameKey="chart_name" unit={metric.unit} />}
    <p className="muted section">แหล่งข้อมูล: {result.sources.join(" · ")}</p><p className="notice warning">{result.caveat}</p><details className="sql"><summary>SQL และพารามิเตอร์ของคำตอบรอบนี้</summary><pre>{result.sql}</pre><pre>{JSON.stringify(result.parameters, null, 2)}</pre></details>
  </>;
}

export default function AssistantPage() {
  const [question, setQuestion] = useState(""), [messages, setMessages] = useState<Message[]>([]), [selected, setSelected] = useState(-1), [pending, setPending] = useState(false), [failure, setFailure] = useState<string | null>(null), [mobileView, setMobileView] = useState("conversation");
  const session = useRef(""), form = useRef<HTMLFormElement>(null);
  const active = messages[selected], result = active?.reply.result;
  const send = async () => {
    if (!question.trim() || pending) return;
    if (!session.current) session.current = crypto.randomUUID();
    const input = question.trim();
    setPending(true); setFailure(null); setSelected(-1);
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: input, session_id: session.current }), signal: AbortSignal.timeout(95000) });
      const reply = await response.json();
      if (!response.ok) throw new Error(typeof reply.detail === "string" ? reply.detail : "ไม่สามารถถามข้อมูลได้");
      const message = { question: input, reply: reply as ChatReply };
      setMessages(m => [...m, message]); setSelected(messages.length); setQuestion(""); setMobileView("result");
    } catch (error) { setFailure(error instanceof Error ? error.message : "บริการไม่พร้อมใช้งาน"); }
    finally { setPending(false); }
  };
  return <>
    <PageHeading title="ผู้ช่วยวิเคราะห์" description="ถามภาษาไทย แล้วตรวจผล กราฟ SQL และแหล่งที่มาได้" />
    <p className="notice" style={{ marginTop: -12, marginBottom: 24 }}>ข้อมูลสาธารณะระดับตลาด ไม่มีข้อมูลลูกค้า รายธนาคาร หรือ NPL · งวดของคำตอบกำหนดจาก query ไม่ใช่ตัวกรองหน้าอื่น</p>
    <div className="tabs chat-mobile-tabs"><button className={mobileView === "conversation" ? "active" : ""} onClick={() => setMobileView("conversation")}>บทสนทนา</button><button className={mobileView === "result" ? "active" : ""} onClick={() => setMobileView("result")}>ผลวิเคราะห์</button></div>
    <div className="chat-layout"><section className={`chat-thread ${mobileView !== "conversation" ? "chat-hidden-mobile" : ""}`} aria-label="บทสนทนา"><div className="chat-toolbar"><span>{active ? modeLabel(active.reply) : "โหมดจะแสดงเมื่อได้รับคำตอบ"}</span><button className="text-button" disabled={pending} onClick={() => { session.current = crypto.randomUUID(); setMessages([]); setSelected(-1); setFailure(null); }}><Plus size={14} /> เริ่มใหม่</button></div>
      <div className="chat-messages">{messages.length === 0 && <><h3>อยากรู้เรื่องไหนของตลาด?</h3><p className="muted">เริ่มจากคำถามที่รองรับ แล้วตรวจรายละเอียดผลทางขวา</p><div className="chat-examples">{examples.map(example => <button key={example} disabled={pending} onClick={() => setQuestion(example)}>{example}</button>)}</div></>}
        {messages.map((m, i) => <div key={i}><div className="message user"><small>คุณ</small>{m.question}</div><button className={`message ${selected === i ? "selected" : ""}`} onClick={() => { setSelected(i); setMobileView("result"); }}><small>{m.reply.error ? "ยังตอบไม่ได้" : "ผู้ช่วยวิเคราะห์"} · คลิกเพื่อดูผลรอบนี้</small>{m.reply.answer}</button></div>)}
        {pending && <p className="notice" role="status">กำลังตีความคำถามและตรวจผลจากคลังข้อมูล…</p>}
        {failure && <div className="notice warning" role="alert">{failure} · คำถามยังอยู่ในช่องพิมพ์ คุณสามารถลองส่งใหม่ได้</div>}
      </div>
      <form className="chat-form" ref={form} onSubmit={e => { e.preventDefault(); void send(); }}><label><span>คำถาม</span><textarea aria-label="คำถาม" placeholder="เช่น แนวโน้มสินเชื่อจังหวัดเชียงใหม่" maxLength={1000} value={question} onChange={e => setQuestion(e.target.value)} disabled={pending} onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); form.current?.requestSubmit(); } }} /></label><div className="chat-form-bottom"><span>{question.length}/1,000 · Ctrl+Enter เพื่อส่ง</span><button className="button primary" type="submit" disabled={pending || !question.trim()}><Send size={15} />{pending ? "กำลังถาม…" : "ส่งคำถาม"}</button></div></form>
    </section>
    <section className={`chat-result ${mobileView !== "result" ? "chat-hidden-mobile" : ""}`} aria-label="ผลวิเคราะห์">{pending ? <div className="chat-result-empty" role="status"><MessageSquare size={30} /><h2>กำลังเตรียมผลวิเคราะห์</h2><p>จะแสดงเฉพาะผลของคำถามรอบนี้เมื่อได้รับคำตอบ</p></div> : !active ? <div className="chat-result-empty"><MessageSquare size={32} strokeWidth={1.5} /><h2>คำตอบที่ตรวจสอบได้</h2><p>เมื่อถามข้อมูล คุณจะเห็นตาราง กราฟ หน่วย และ SQL ของคำตอบที่เลือกตรงนี้</p></div> : active.reply.error || !result ? <div className="state" role="status"><h2>{replyHeading(active.reply)}</h2><p style={{ whiteSpace: "pre-line" }}>{active.reply.answer}</p><div className="chat-examples">{active.reply.choices?.map(choice => <button key={choice} onClick={() => { setQuestion(choice); setMobileView("conversation"); }}>{choice}</button>)}</div><p className="muted">ตัวเลือกจะใส่ในช่องคำถามให้ตรวจและส่ง ไม่แสดงผลเก่าแทนคำตอบใหม่</p></div> : <Analysis key={selected} reply={active.reply} index={selected} />}</section></div><Footer />
  </>;
}
