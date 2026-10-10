import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  const allowedRead = /^(metadata|overview|provinces|provinces\/\d+\/history|comparison|sources|questions|questions\/CQ\d{2})$/;
  if (!(request.method === "GET" && allowedRead.test(endpoint)) && !(request.method === "POST" && endpoint === "chat")) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }
  try {
    const base = process.env.API_BASE_URL || "http://127.0.0.1:8000";
    const url = new URL(endpoint, base.replace(/\/$/, "") + "/");
    const period = request.nextUrl.searchParams.get("period");
    if (period) url.searchParams.set("period", period);
    const codes = request.nextUrl.searchParams.get("codes");
    if (codes && endpoint === "comparison") url.searchParams.set("codes", codes);
    let body: string | undefined;
    if (request.method === "POST") {
      // A bounded, explicit BFF surface; do not proxy the privileged ETL API.
      const raw = await request.text();
      if (raw.length > 6000) return NextResponse.json({ detail: "Request too large" }, { status: 413 });
      const payload = JSON.parse(raw);
      if (typeof payload.question !== "string" || !payload.question.trim() || payload.question.length > 1000 || typeof payload.session_id !== "string" || payload.session_id.length > 100) {
        return NextResponse.json({ detail: "Invalid chat input" }, { status: 400 });
      }
      body = JSON.stringify({ question: payload.question, session_id: payload.session_id });
    }
    const response = await fetch(url, {
      method: request.method, headers: { "Content-Type": "application/json" }, body,
      cache: "no-store", signal: AbortSignal.timeout(endpoint === "chat" ? 90000 : 15000),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ detail: "บริการข้อมูลไม่พร้อมใช้งาน กรุณาลองใหม่" }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
