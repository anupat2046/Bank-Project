# Bounded conversational analytics

The chat graph starts with a structured LLM intent router when the selected provider (Groq, Gemini or OpenAI) is configured, before the hybrid analytical planner. Without a provider, or during a provider failure, supported requests use bounded deterministic routing. The router chooses one of: capabilities, greeting, analytics, clarification, explanation, presentation, unsupported. It cannot execute tools or SQL. Safety checks and the semantic SQL compiler remain authoritative.

The router emits only `route` and `chart`; unexpected properties are rejected. `chart` must be `auto` outside presentation, including analytical requests that explicitly ask for a graph or table. The analytical planner chooses those charts. Presentation redraws unchanged data; changes to Top N/order, provinces/series, filters, dates or metrics remain analytics. A non-geographic, rules-based guard rejects presentation that conflicts with recognized row-changing constraints without querying the warehouse; it ignores unrequested parser defaults for limit/order. Planner-only status/plan instructions are kept out of Router and Insight prompts. See the [contract correction and retained validation failures](evidence/llm/router-contract-fix-2026-10-24.md).

Capabilities and greetings use the application's supported-feature catalogue. Explanations include verified, scope-limited observations (displayed extrema/gaps or per-series endpoint changes), definitions, units, period, sources and caveats. An available LLM selects allowlisted evidence IDs; the application renders all numbers and text. Invalid selections or provider failures retain deterministic evidence. This is deliberately not free-form causal analysis. Presentation requests copy the last successful result without executing SQL. A line chart without a temporal axis falls back to a bar chart with a notice. Data-changing requests still pass through the analytical planner and read-only warehouse execution.

Confirmed query context, last successful result, pending analytical clarification choices and ordinary conversation history are separate checkpoint fields. Help does not erase a pending analytical clarification. A failed/unsupported turn does not display old data as a new answer. Presentation explicitly labels its reuse of old results.

Provider calls have a maximum configured 12-second SDK timeout, no network retries, at most three calls per request and a 45-second admission budget (not a hard wall-clock cancellation guarantee). The router has at most one structured-output repair. A process-local circuit pauses calls after quota failures (300 seconds), authentication/model failures (600 seconds), or transient failures (30 seconds). A later request probes after the cooldown; rotating the key/model uses a new circuit. There is no autonomous retry loop or automatic billing/model change. If unavailable, narrowly recognized help/greetings/presentation and rules-understood analytics remain usable. Other failures receive safe messages. Invalid analytical output asks for clarification rather than claiming the provider is down. API error messages are selected by bounded public error codes; exception strings are never returned.

The v4 analytical contract checks recognized explicit metrics/ratios, provinces, dates, exclusions, direction, thresholds, strictness, requested measures and numbered limits. Conflicts ask for confirmation rather than silently rewriting the plan. Buddhist-year ISO dates and billion-THB thresholds are normalized. This lexical coverage is not proof of understanding arbitrary language. Genuine ambiguity/unsupported requests stay bounded; unrecognized phrasing is eligible for LLM planning even when a metric was recognized.

`GET /ai/health` and chat `provider_status` expose only bounded failure classes/cooldown, not exception strings or credentials. They describe the current process, not an active provider probe. A `ready` analytical answer can coexist with a provider outage; the UI explicitly identifies this fallback. Same-session turns are serialized within an API process, and omitted API session IDs receive a new UUID. Multiple API workers still require distributed session locking and a shared breaker if deployed that way.

LLM calls produce allowlisted timing/token telemetry. No API keys, raw exception strings, questions or session IDs enter that telemetry. Conversation checkpoints store chat history separately. Shared access requires authenticated session ownership, a retention policy, and access isolation; these controls are not included in the supplied configuration.

The historical 24-turn planner benchmark is unchanged and does **not** measure the new router. Current checks and live-provider limitations are recorded in [October 24 hardening evidence](evidence/llm/hardening-2026-10-24.md). The additional 60-turn HTTP regression covers routing, real warehouse arithmetic, metric/limit follow-ups, clarification resolution, presentation reuse and help/explanation. It is authored regression evidence, not an untouched held-out split or a live Gemini accuracy score.

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

This historical check verifies routing, checkpoint continuity and presentation reuse, not numerical accuracy across new metrics or robustness to every wording. Unsupported NPL was blocked before an LLM call. The remaining turns used the configured Gemini router; the analytical turn's SQL plan remained deterministic. At that time, planner timeouts were 20 seconds and Gemini retries were capped at one (default zero). Current limits are documented above; OpenAI remains untested live.
