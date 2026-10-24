"use client";

import { createContext, useContext, useRef, useState } from "react";
import { ChatReply } from "@/lib/data";

type Message = { question: string; reply: ChatReply };
function useConversationState() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selected, setSelected] = useState(-1);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [mobileView, setMobileView] = useState("conversation");
  const session = useRef("");
  const inFlight = useRef(false);
  const send = async () => {
    if (!question.trim() || inFlight.current) return;
    inFlight.current = true;
    if (!session.current) session.current = crypto.randomUUID();
    const input = question.trim();
    setPending(true); setFailure(null); setSelected(-1);
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: input, session_id: session.current }), signal: AbortSignal.timeout(95000) });
      const reply = await response.json();
      if (!response.ok) throw new Error("ไม่สามารถส่งคำถามได้ กรุณาลองใหม่");
      setMessages(previous => [...previous, { question: input, reply: reply as ChatReply }]);
      setSelected(messages.length); setQuestion(""); setMobileView("result");
    } catch (error) {
      setFailure(error instanceof Error && error.name === "TimeoutError" ? "ใช้เวลาตอบนานกว่าปกติ กรุณาลองส่งคำถามอีกครั้ง" : "เชื่อมต่อผู้ช่วยไม่ได้ กรุณาตรวจการเชื่อมต่อแล้วลองใหม่");
    } finally { inFlight.current = false; setPending(false); }
  };
  const reset = () => {
    if (inFlight.current) return;
    session.current = crypto.randomUUID(); setMessages([]); setSelected(-1);
    setQuestion(""); setFailure(null); setMobileView("conversation");
  };
  return { question, setQuestion, messages, selected, setSelected, pending, failure, mobileView, setMobileView, send, reset };
}
const Conversation = createContext<ReturnType<typeof useConversationState> | null>(null);

// Lives above route pages: navigation preserves the session, draft, and in-flight reply.
// Memory only; a reload starts a new conversation and clears the browser-side history.
export function ConversationProvider({ children }: { children: React.ReactNode }) {
  return <Conversation.Provider value={useConversationState()}>{children}</Conversation.Provider>;
}
export function useConversation() {
  const state = useContext(Conversation);
  if (!state) throw new Error("Missing conversation provider");
  return state;
}
