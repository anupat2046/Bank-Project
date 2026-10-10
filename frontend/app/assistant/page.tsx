"use client";

import { useRef, useState } from "react";
import { Download, MessageSquare, Send, Plus } from "lucide-react";
import { Footer, PageHeading } from "@/components/shell";
import { DataTable } from "@/components/table";
import { Bars, TrendChart } from "@/components/charts";
import { ChatReply, downloadCsv } from "@/lib/data";

type Message = { question: string; reply: ChatReply };
const examples = ["สินเชื่อสูงสุด 5 จังหวัด", "แนวโน้มเงินฝากย้อนหลัง", "จังหวัดที่มีสาขาต่อประชากรสูงสุด 10 อันดับ"];

export default function AssistantPage() {
  const [question, setQuestion] = useState(""), [messages, setMessages] = useState<Message[]>([]), [selected, setSelected] = useState(-1), [pending, setPending] = useState(false), [failure, setFailure] = useState<string | null>(null), [view, setView] = useState("chart"), [mobileView, setMobileView] = useState("conversation");
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
    <div className="chat-layout"><section className={`chat-thread ${mobileView !== "conversation" ? "chat-hidden-mobile" : ""}`} aria-label="บทสนทนา"><div className="chat-toolbar"><span>{active ? active.reply.mode.includes("gemini") ? "Gemini · structured plan" : active.reply.mode.includes("กฎ") ? "Rules mode · ไม่ใช้ AI" : active.reply.mode : "โหมดจะแสดงเมื่อได้รับคำตอบ"}</span><button className="text-button" disabled={pending} onClick={() => { session.current = crypto.randomUUID(); setMessages([]); setSelected(-1); setFailure(null); }}><Plus size={14} /> เริ่มใหม่</button></div>
      <div className="chat-messages">{messages.length === 0 && <><h3>อยากรู้เรื่องไหนของตลาด?</h3><p className="muted">เริ่มจากคำถามที่รองรับ แล้วตรวจรายละเอียดผลทางขวา</p><div className="chat-examples">{examples.map(example => <button key={example} disabled={pending} onClick={() => setQuestion(example)}>{example}</button>)}</div></>}
        {messages.map((m, i) => <div key={i}><div className="message user"><small>คุณ</small>{m.question}</div><button className={`message ${selected === i ? "selected" : ""}`} onClick={() => { setSelected(i); setMobileView("result"); }}><small>{m.reply.error ? "ยังตอบไม่ได้" : "ผู้ช่วยวิเคราะห์"} · คลิกเพื่อดูผลรอบนี้</small>{m.reply.answer}</button></div>)}
        {pending && <p className="notice" role="status">กำลังตีความคำถามและตรวจผลจากคลังข้อมูล…</p>}
        {failure && <div className="notice warning" role="alert">{failure} · คำถามยังอยู่ในช่องพิมพ์ คุณสามารถลองส่งใหม่ได้</div>}
      </div>
      <form className="chat-form" ref={form} onSubmit={e => { e.preventDefault(); void send(); }}><label><span>คำถาม</span><textarea aria-label="คำถาม" placeholder="เช่น แนวโน้มสินเชื่อจังหวัดเชียงใหม่" maxLength={1000} value={question} onChange={e => setQuestion(e.target.value)} disabled={pending} onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); form.current?.requestSubmit(); } }} /></label><div className="chat-form-bottom"><span>{question.length}/1,000 · Ctrl+Enter เพื่อส่ง</span><button className="button primary" type="submit" disabled={pending || !question.trim()}><Send size={15} />{pending ? "กำลังถาม…" : "ส่งคำถาม"}</button></div></form>
    </section>
    <section className={`chat-result ${mobileView !== "result" ? "chat-hidden-mobile" : ""}`} aria-label="ผลวิเคราะห์">{pending ? <div className="chat-result-empty" role="status"><MessageSquare size={30} /><h2>กำลังเตรียมผลวิเคราะห์</h2><p>จะแสดงเฉพาะผลของคำถามรอบนี้เมื่อได้รับคำตอบ</p></div> : !active ? <div className="chat-result-empty"><MessageSquare size={32} strokeWidth={1.5} /><h2>คำตอบที่ตรวจสอบได้</h2><p>เมื่อถามข้อมูล คุณจะเห็นตาราง กราฟ หน่วย และ SQL ของคำตอบที่เลือกตรงนี้</p></div> : active.reply.error || !result ? <div className="state error" role="alert"><h2>ยังไม่สามารถตอบคำถามนี้ได้</h2><p>{active.reply.answer}</p><p className="muted">ลองระบุตัวชี้วัด จังหวัด หรือช่วงเวลาให้ชัดขึ้น ไม่แสดงผลเก่าแทนคำตอบใหม่</p></div> : <>
      <div className="panel-heading"><div><h2>{result.metric_label}</h2><p className="muted">หน่วย: {result.unit} · {result.rows.length} แถวผลลัพธ์</p></div><button className="button subtle" disabled={!result.rows.length} onClick={() => downloadCsv(result.rows, `chat-${result.plan.metric}-${selected + 1}`, undefined, { value: `${result.metric_label} (${result.unit})` })}><Download size={15} />CSV</button></div>
      <p className="notice">{active.reply.answer}</p><div className="tabs"><button className={view === "chart" ? "active" : ""} onClick={() => setView("chart")}>กราฟ</button><button className={view === "table" ? "active" : ""} onClick={() => setView("table")}>ตาราง</button></div>
      {result.rows.length === 0 ? <div className="empty">ไม่มีข้อมูลตรงเงื่อนไข</div> : view === "table" ? <DataTable rows={result.rows} columnLabels={{ value: `${result.metric_label} (${result.unit})` }} filename={`chat-${result.plan.metric}-${selected + 1}`} /> : result.plan.group_by === "period" ? <TrendChart rows={result.rows} series={[{ key: "value", name: result.metric_label, color: "#087d65" }]} unit={result.unit} height={330} /> : <Bars rows={result.rows} valueKey="value" unit={result.unit} />}
      <p className="muted section">แหล่งข้อมูล: {result.sources.join(" · ")}</p><p className="notice warning">{result.caveat}</p><details className="sql"><summary>SQL และพารามิเตอร์ของคำตอบรอบนี้</summary><pre>{result.sql}</pre><pre>{JSON.stringify(result.parameters, null, 2)}</pre></details>
    </>}</section></div><Footer />
  </>;
}
