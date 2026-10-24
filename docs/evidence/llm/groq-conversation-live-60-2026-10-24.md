# Groq live conversation regression — 24 October 2026

The deployed local HTTP service completed **60/60 authored conversation turns**, across 20 three-turn scenarios, using Groq `openai/gpt-oss-20b`. All route, status, expected-plan, presentation/context and independently calculated result checks passed. This extends the [initial three-turn smoke](groq-service-smoke-2026-10-24.json); that earlier artifact remains unchanged.

[Raw 60-turn report](groq-conversation-live-60-2026-10-24.json) · [Runtime and dataset fingerprints](groq-conversation-live-60-runtime-2026-10-24.json) · [Authored scenarios](../../../tests/fixtures/conversation_regression.json)

## Observed results

| Check | Result |
| --- | --- |
| Planned / attempted / passed | 60 / 60 / 60; no failed or unrun turns |
| Independent warehouse arithmetic | 40/40 applicable result-bearing turns passed, including reused presentation results |
| Turns with real model calls | 57 |
| Turns with zero model calls | 3: C18-1 ambiguous denominator, C19-1 NPL, C20-1 forecast; handled by the pre-router gates |
| Total model calls | 67 |
| Provider errors / quota stops | 0 / 0 |
| Router structured-output repairs | 4 events across C01-1, C11-1, C12-1 and C16-1; all four turns passed after one bounded repair |
| Observed input / output / total tokens | 43,069 / 3,742 / 46,811 |
| Estimated cost | Unknown; token prices were not configured, so no zero-cost claim is made |
| HTTP response latency | Median 755.14 ms; p95 1,601.29 ms; maximum 2,412.75 ms |
| Request pacing | Ten seconds between HTTP turns, excluded from response-latency measurements |
| Warehouse snapshot | 1,925 rows, 77 provinces and 25 months; latest period July 2026 |

The raw report retains the four `RoutingOutputError` events even though the final responses passed. These were recoverable structured-output failures, not provider HTTP errors. They are included in the 67 calls and token totals; the run was not a first-attempt-perfect router result. There was no selective rerun of failed cases.

Coverage included 24 analytical routes, 20 presentation routes, six explanations, eight capabilities responses and two unsupported routes. The scenarios exercised ratios, ranking direction/limits, Bangkok exclusion, province comparisons, Buddhist-year dates, strict/inclusive population filters, monetary-unit conversion, multiple metrics and YoY, monthly trends, policy rates, clarification resolution and refusal. The evaluator calculated expected numbers independently from warehouse records, rather than trusting the returned SQL or answer text.

The service reported a closed Groq circuit with no recorded provider failure after the run, and its warehouse health and web/API checks were available. This is a dated observation, not continuous availability monitoring.

## Reproduce

```powershell
# Calls the configured live provider through the running API.
# Up to three model calls per turn; stop on provider/transport failure.
.\.venv\Scripts\python.exe -m tools.evaluate_conversation --live --base-url http://127.0.0.1:8000 --max-requests 60 --delay 10 --progress --out data/eval/groq-conversation-live-new.json
```

The delay bounds request frequency but does not establish compliance with an account's current quota. The pacing/progress CLI additions were also checked with a three-turn offline run, which passed with zero model calls.

## Scope and limits

This is one pass over a previously authored regression corpus, **not held-out model accuracy**. The application uses a hybrid planner: recognized analytical wording can use deterministic rules after LLM routing, while validated plans compile to read-only SQL. Passing this run does not establish an LLM-only score, representative Thai-language generalization, concurrency/load performance or account billing tier. It also does not assess free-form explanation quality: explanations select allowlisted evidence and render verified facts.

The prompts, application behavior and fixture were not tuned during this run. The runtime fingerprint records the deployed files and the repository reference. The deployed `bank/chat.py` retained an unused timer and redundant exception re-raise already removed from the repository; the inspected diff contained no planner-validation or provider-call changes. No deployment was changed during the evaluation. Separate held-out questions and repeated trials remain future evaluation work.
