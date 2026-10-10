# Local service fallback and telemetry smoke test

Verified on 11 October 2026 (Asia/Bangkok) after rebuilding the API image with the v3 planner, before the conversation-router addition. This is one local integration request, separate from the 24-turn comparison, not an accuracy benchmark or production deployment. See [subsequent routing evidence](../../conversation-routing.md).

- Endpoint: Next.js same-origin proxy `POST /api/chat` at `127.0.0.1:3000`.
- Authored public question: `ช่วยดูยอดที่คนเอามาฝากไว้กับธนาคารทั้งประเทศย้อนหลัง 3 เดือน`.
- Actual mode: `LangGraph + LangChain structured LLM (gemini)`.
- Error: none; primary metric `deposits`, `limit=3`, three warehouse result rows, latest banking period `2026-07-01`.
- Operational log aggregation: one request, ready, one LLM call, 3,471.57 ms server response latency, 1,306 input tokens and 403 output tokens; usage available.
- Estimated USD cost: unavailable because token rates were not configured. This is not evidence that the request was free.

The proxy, LangGraph checkpointed service, live Gemini planner, read-only SQL execution and JSON telemetry were exercised together. No key, session identifier, raw provider metadata or exception string is included here. The function-level benchmark's timings do not include this HTTP/checkpoint boundary; this test does.

Inspect current operational metrics (history depends on local Docker-log retention):

```powershell
docker compose logs --no-log-prefix --no-color api |
  .\.venv\Scripts\python.exe -m tools.observe_chat
```
