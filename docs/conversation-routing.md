# Bounded conversational analytics

The deployed chat graph now starts with a structured LLM intent router (Gemini when configured), before the existing hybrid analytical planner. The router chooses one of: capabilities, greeting, analytics, clarification, explanation, presentation, unsupported. It cannot execute tools or SQL. Safety checks and the semantic SQL compiler remain authoritative.

Capabilities and greetings use the application's supported-feature catalogue. Explanations render the last confirmed result's definitions, units, scope, period and caveat; they are not free-form causal analysis. Presentation requests copy the last successful result without executing SQL. A line chart without a temporal axis falls back to a bar chart with a notice. Data-changing requests still pass through the analytical planner and read-only warehouse execution.

Confirmed query context, last successful result, pending analytical clarification choices and ordinary conversation history are separate checkpoint fields. Help does not erase a pending analytical clarification. A failed/unsupported turn does not display old data as a new answer. Presentation explicitly labels its reuse of old results.

The router has a 20-second timeout per call, no network retry, and at most one structured-output repair. If it is unavailable, narrowly recognized help/greetings/presentation and rules-understood analytics remain usable. Other failures receive safe messages. Invalid analytical output asks for clarification rather than claiming the provider is down. API error messages are selected by bounded public error codes; exception strings are never returned.

LLM calls produce allowlisted timing/token telemetry. No API keys, raw exception strings, questions or session IDs enter that telemetry. Conversation checkpoints store chat history separately. Shared access requires authenticated session ownership, a retention policy, and access isolation; these controls are not included in the supplied configuration.

The historical 24-turn planner benchmark is unchanged and does **not** measure the new router. Conversation tests cover offline routing, malformed-output repair, provider failure, safety gating, grounded explanation, presentation reuse, pending-context preservation and session isolation. The expanded Python suite passes 170 tests. Live smoke tests are integration evidence, not a statistically reliable routing accuracy benchmark.

## Live integration smoke — 11 October 2026 (Asia/Bangkok)

Seven sequential HTTP requests through the Next.js `/api/chat` proxy passed expected route/result checks in one new session:

| Turn | Request | Observed result |
| --- | --- | --- |
| 1 | เเล้วทำไรได้บ้าง | capabilities, no error, no analytical rows |
| 2 | สินเชื่อสูงสุด 3 จังหวัด | validated rules planner, 3 rows, bar chart |
| 3 | Explain what the last result means | explanation, no new query result |
| 4 | Change the last result to a table | presentation, same 3 rows, table |
| 5 | What else can you help me do? | capabilities, no analytical rows |
| 6 | Show NPL by individual bank | unsupported, no analytical rows |
| 7 | Change the last result to a bar chart | presentation, preserved 3 rows, bar chart |

This verifies routing, checkpoint continuity and presentation reuse in the running service, not numerical accuracy across new metrics or robustness to every wording. Unsupported NPL is blocked by the safety gate before an LLM call. The remaining turns use the configured Gemini router; the analytical turn's SQL plan remains deterministic. Model latency and token usage include router calls, and the UI distinguishes router provider from planner mode. Structured planner timeouts are 20 seconds, Gemini retries are capped at one (default zero), and OpenAI retries are disabled; OpenAI remains untested live.
