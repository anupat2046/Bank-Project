# Groq integration — 24 October 2026

Groq is supported through the existing OpenAI-compatible LangChain client at the fixed `https://api.groq.com/openai/v1` endpoint. The configured model is `openai/gpt-oss-20b`; this model identifier does not send requests to the OpenAI API. No additional dependency was installed.

Explicit `LLM_PROVIDER=groq` never falls back to Gemini/OpenAI when the key is missing or the provider fails. Existing keys may remain privately configured without being used. Billing tier is controlled by the provider account, not verified or changed by this application. Free-tier limits are not unlimited-use guarantees.

## Initial integration checks

- 212 Python tests passed, including explicit-provider selection, no cross-provider fallback, fixed Groq endpoint, bounded settings and structured-output adapter configuration.
- A direct live router check returned `greeting`, one model call, no provider error and 438 total tokens.
- Five development attempts using JSON Schema mode (best-effort and strict) failed with `json_validate_failed` for the nested optional plan. Observed issues included null values for array fields and omitted required fields. These failures are not hidden or counted as successful evaluations.
- The compatibility adapter uses JSON Object Mode, embeds the schema in the prompt, parses with Pydantic and applies the existing semantic guard before SQL. This is **not** constrained/strict-schema decoding. Invalid structured output cannot execute a query.
- A subsequent direct planner check returned `ready`, `credits_per_person`, Top 3, one model call and 2,501 total tokens. This is one authored development case, not a quality benchmark.
- The initial deployed HTTP smoke passed three authored turns: loans-per-person Top 7, a follow-up changing the limit to Top 3, and presentation reuse as a table. Route, plan and real warehouse arithmetic checks passed. See the [raw smoke report](groq-service-smoke-2026-10-24.json).
- The service reported provider `groq` with no open circuit or recorded provider failure after the smoke. This is runtime evidence for the tested calls, not continuous health monitoring.
- `.env` is ignored by Git, not tracked, and excluded from Docker build context. No key value is included in this evidence. A key exposed in chat must be revoked and replaced privately before continued/shared use.

The initial smoke attempted only **3/60** conversation-regression turns. A later [full live Groq run](groq-conversation-live-60-2026-10-24.md) completed **60/60**, with **40/40 arithmetic checks**, **67 model calls** and no provider errors. Four router structured-output repairs were retained in the evidence. This is authored hybrid-system regression, not held-out or LLM-only accuracy. The offline regression and historical Gemini planner scores remain separate evidence. Costs remain unknown when rates/usage are unavailable, not automatically zero because a free plan exists.

The later [router contract correction](router-contract-fix-2026-10-24.md), completed on 25 October in Asia/Bangkok, records 235 tests and staged live checks: a full 60/60 HTTP run with 40/40 arithmetic checks, followed by a final targeted 3/3 policy-chart confirmation without repair/fallback. Earlier four repairs, host timeouts, the intermediate 58/60 run and the policy guard fallback remain documented with their source fingerprints. The final targeted check is kept separate from the preceding full-corpus run.

The API was updated using the existing dependency image plus changed application files; a clean dependency installation was not performed. The frontend was not changed by this provider integration. Full held-out Thai-language evaluation, repeated trials and account-specific quota/load checks remain outstanding.
