# LLM engineering: evaluation and observability

This project treats natural-language planning as a measurable component, not a successful HTTP request. The [measured comparison](evidence/llm/results.md) and its raw JSON artifacts separate model errors from infrastructure failures, numerical correctness and appropriate clarification.

The separate [local service fallback smoke evidence](evidence/llm/service-smoke.md) confirms the HTTP/checkpoint/provider/SQL boundary and token telemetry before the conversation-router addition. It is not combined with the comparison's accuracy denominator. The [subsequent routing checks](conversation-routing.md) are separate integration evidence, not router accuracy scores.

## Experimental design

The original 80-question deterministic corpus remains a regression suite. A separate [24-turn authored corpus](../tests/fixtures/llm_eval_cases.json) has **10 development turns and 14 held-out turns**, including different three-turn dialogues. The split was created before model evaluation; held-out model outcomes were not used to tune v3. It is a small purposive sample, not a representative or random estimate of Thai-language accuracy.

All three strategies use the same questions, warehouse snapshot, bounded SQL executor, deterministic answer renderer and independent Python arithmetic oracle:

- **Rules-only:** no provider requests; unsupported wording can require clarification.
- **LLM-only:** every planning turn uses Gemini structured output. This is not unrestricted model-generated SQL: validated plans still pass through the read-only compiler. The common conversation controller handles history and confirmed scope.
- **Hybrid:** the analytical planner resolves known wording with rules and uses Gemini only for unresolved paraphrases. Known ambiguous/unsupported semantics are not forced through a model. The benchmark does not invoke the application's subsequent conversational router.

Each strategy maintains its **own predicted context**. The next turn does not receive the golden previous plan. A bad first turn can therefore cause measurable context errors later. Benchmark state is in-memory and does not overwrite users' LangGraph checkpoints. The benchmark calls the analytical planning/execution/answer functions, but excludes conversational routing, HTTP, browser, and checkpoint overhead. Later service changes include shorter provider timeouts and distinct planning-error responses; the retained reports describe the historical implementation, not a fresh benchmark of every current change.

## Metrics and rubric

| Dimension | Check |
|---|---|
| Status | Ready, clarification or unsupported as expected; provider/system errors separate |
| Plan | Primary metric, grain, intent, sorting, limit, provinces, exclusions, dates and thresholds; all requested measures must be present |
| Numbers | Expected scope's independently calculated values, row count/order, prior-year alignment and ranking universe |
| Clarification | No result/stale rows, non-empty message and required Thai alternatives/terms |
| Performance | End-to-end function latency and LLM latency; p50/p95, not just average |
| Operations | Provider calls, error rate, clarification count, token metadata and optional estimated cost |

Additional display measures are allowed. Known English and Thai province names are compared by canonical codes; unknown names are not fuzzy-matched. Clarification scoring is an explicit **heuristic**, not a blinded human review. Generated messages/choices are retained in the public authored-corpus reports so a reviewer can inspect that limitation. Numbers are generated deterministically from executed SQL; this evaluates whether the LLM selects the correct analysis, not whether it can perform arithmetic itself.

Error categories include metric, additional measures, province, period, filter, aggregation, intent, ordering, limit, chart, context, result, clarification, status and provider error. “All checks passed” is stricter than status success or SQL validity. Numeric/plan denominators contain only expected-ready turns; clarification denominators contain only expected-clarification turns.

The plan rubric is deliberately strict about fields. An unused/redundant `start_period` on a province query can be a plan mismatch even when the resulting month and all numbers are correct; inspect the separate number score and raw plans before equating every mismatch with a wrong user-facing answer. The dialogue context category flags scope-field differences, not a causal diagnosis of memory failure.

## Development-driven revisions

- **v1:** original lexical parser and prompt, retained for baseline evaluation.
- **v2:** normalize `ยอดออม/เงินออม` to deposits and `เงินกู้` to loans while preserving ratio guards; recognize numbered “มากที่สุด” requests. The prompt explicitly forbids guessed calendar ranges, explains same-metric supplemental YoY, requires Thai clarification and preserves confirmed follow-up scope.
- **v3:** retain v2 and enforce a shape invariant: `group_by=period` has `intent=trend`. Reject ready decisions without a plan and non-ready decisions with an executable plan. These checks do not use expected labels to rewrite a metric/date or fabricate a result.

The intermediate development report is retained. The final application uses v3. Before/after comparisons are measured on both splits, with no tuning after held-out outcomes. A single pass and temperature zero do not establish reproducible accuracy or eliminate model variability. Larger paraphrase sets, user testing and repeated trials remain future work.

## Reproduce a live comparison

Install the project's requirements into the local virtual environment, start PostgreSQL/API, and configure `GEMINI_API_KEY` privately in `.env`. Never pass a key on the command line. These commands send authored public-data questions and conversation context to Gemini, consume quota and can incur charges according to your account. Copying report names below is intentionally prevented from overwriting existing evidence; choose a new name for a new run.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m tools.benchmark_llm --live --split dev --version v1 --output data/eval/dev-v1.json
.\.venv\Scripts\python.exe -m tools.benchmark_llm --live --split dev --version v3 --output data/eval/dev-v3.json
# Freeze the implementation before inspecting held-out outcomes.
.\.venv\Scripts\python.exe -m tools.benchmark_llm --live --split heldout --version v1 --output data/eval/heldout-v1.json
.\.venv\Scripts\python.exe -m tools.benchmark_llm --live --split heldout --version v3 --output data/eval/heldout-v3.json
```

The driver disables provider retries, paces potential model calls, writes progress after each completed turn and stops on its explicit call budget or three consecutive system failures. It does not claim the configured delay matches a particular account quota. `--resume` requires the same corpus/model/warehouse. `--retry-setup-failures` only retries **zero-request missing-SDK** failures and preserves their original records separately; it never selectively retries bad model answers. Other aborted setup evidence is retained as incomplete, not scored as a completed benchmark.

The tracked JSON artifacts include fixture and warehouse hashes, model/version, timestamps, expected/actual plans, error categories and request-level telemetry. They contain authored public questions, not customer data. No API keys, DSNs, provider exception strings or raw model metadata are exported. API trials are not backfilled or invented. The results renderer verifies matching coverage and warehouse/corpus hashes before publishing a table.

## Operational telemetry

`bank/observability.py` uses request-local ContextVars. `ask()` emits one allowlisted `bank_chat` JSON event to service logs, including successful, clarification, refusal and error paths. The event contains a new request ID (not the chat session ID), timestamp, response latency, LLM calls/latency, available token counts, error types and status. It does **not** contain questions, SQL, answers, provider keys, DSNs or raw errors. LangGraph's existing conversation checkpoints still store conversation content separately; telemetry redaction is not a checkpoint-retention policy.

```powershell
docker compose logs --no-log-prefix --no-color api |
  .\.venv\Scripts\python.exe -m tools.observe_chat
```

The aggregation tool ignores unrelated logs and never echoes their raw content. Docker logs are local operational storage, not a durable metrics backend; container recreation and rotation can lose history. A production system would require controlled export, retention, alerting and authenticated access.

Structured output uses [`include_raw=True`](https://reference.langchain.com/python/langchain-google-genai/chat_models/ChatGoogleGenerativeAI/with_structured_output) only to extract numeric `usage_metadata`; raw messages are not logged. Google documents [token usage](https://ai.google.dev/gemini-api/docs/tokens) and [account-dependent rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

Optional `.env` fields `LLM_INPUT_USD_PER_MILLION` and `LLM_OUTPUT_USD_PER_MILLION` supply estimated uncached rates for the active model. If rates or provider usage are missing, live cost remains `null`, not zero/free. Cached pricing, tier changes and invoice adjustments are not reconciled; configured estimates are not billing statements. Rules-only turns have zero model calls/tokens. Unknown usage on a failed request is never silently replaced with zero.

## Scope

This is a local prototype: no LangSmith account, external observability vendor, vector database, multi-agent system or production deployment is required or claimed. Evaluation adds no customer-data access and does not alter the Airflow schedule. Current service telemetry includes router calls and bounded route labels, while the historical planner benchmark excludes that routing stage.
