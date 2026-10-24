import type { Metadata } from "next";
import { Suspense } from "react";
import "@fontsource/noto-sans-thai/400.css";
import "@fontsource/noto-sans-thai/600.css";
import "@fontsource/noto-sans-thai/700.css";
import "./globals.css";
import { Shell } from "@/components/shell";
import { ConversationProvider } from "@/components/conversation-state";

export const metadata: Metadata = { title: "Bank Intelligence | ตลาดธนาคารรายจังหวัด", description: "สำรวจตลาดธนาคารไทยด้วยข้อมูลสาธารณะจริง ตรวจสอบแหล่งข้อมูลและวิธีคำนวณได้" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="th"><body><ConversationProvider><Suspense fallback={<div className="state">กำลังเปิดพื้นที่วิเคราะห์…</div>}><Shell>{children}</Shell></Suspense></ConversationProvider></body></html>;
}
