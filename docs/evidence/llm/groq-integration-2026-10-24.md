# Groq integration — 24 October 2026

Groq is supported through the existing OpenAI-compatible LangChain client at the fixed `https://api.groq.com/openai/v1` endpoint. The configured model is `openai/gpt-oss-20b`; this model identifier does not send requests to the OpenAI API. No additional dependency was installed.

Explicit `LLM_PROVIDER=groq` never falls back to Gemini/OpenAI when the key is missing or the provider fails. Existing keys may remain privately configured without being used. Billing tier is controlled by the provider account, not verified or changed by this application. Free-tier limits are not unlimited-use guarantees.

## Recorded checks

- 212 Python tests passed, including explicit-provider selection, no cross-provider fallback, fixed Groq endpoint, bounded settings and structured-output adapter configuration.
- A direct live router check returned `greeting`, one model call, no provider error and 438 total tokens.
- Five development attempts using JSON Schema mode (best-effort and strict) failed with `json_validate_failed` for the nested optional plan. Observed issues included null values for array fields and omitted required fields. These failures are not hidden or counted as successful evaluations.
- The compatibility adapter uses JSON Object Mode, embeds the schema in the prompt, parses with Pydantic and applies the existing semantic guard before SQL. This is **not** constrained/strict-schema decoding. Invalid structured output cannot execute a query.
- A subsequent direct planner check returned `ready`, `credits_per_person`, Top 3, one model call and 2,501 total tokens. This is one authored development case, not a quality benchmark.
- The deployed HTTP service passed three authored turns: loans-per-person Top 7, a follow-up changing the limit to Top 3, and presentation reuse as a table. Route, plan and real warehouse arithmetic checks passed. See the [raw smoke report](groq-service-smoke-2026-10-24.json).
- The service reported provider `groq` with no open circuit or recorded provider failure after the smoke. This is runtime evidence for the tested calls, not continuous health monitoring.
- `.env` is ignored by Git, not tracked, and excluded from Docker build context. No key value is included in this evidence. A key exposed in chat must be revoked and replaced privately before continued/shared use.

Only **3/60** conversation-regression turns were attempted live in this smoke; the remaining 57 were not run. The earlier 60/60 offline regression and historical Gemini planner scores must not be presented as Groq live accuracy. Costs remain unknown when rates/usage are unavailable, not automatically zero because a free plan exists.

The API was updated using the existing dependency image plus changed application files; a clean dependency installation was not performed. The frontend was not changed by this provider integration. Full held-out Thai-language evaluation, repeated trials and account-specific quota/load checks remain outstanding.
