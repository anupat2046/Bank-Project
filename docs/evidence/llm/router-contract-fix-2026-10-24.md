# Router contract correction — 24 October 2026 UTC

The correction is verified in stages: the full live HTTP regression passed **60/60 turns and 40/40 arithmetic checks**, then the last policy-chart guard correction passed a targeted **3/3 live turns without repair/fallback**. The delivered code passed **235 Python tests**. The complete run and the final targeted check have separate source fingerprints; the full corpus was not rerun after that last narrow correction. Completion was on 25 October in Asia/Bangkok; artifact filenames retain the UTC date.

The earlier [60-turn live Groq regression](groq-conversation-live-60-2026-10-24.md) passed but needed four output repairs. A bounded [structural reproduction](router-contract-baseline-2026-10-24.json) confirmed all four cases: the model chose `analytics` correctly, then supplied `bar` or `line` instead of the required `chart=auto`. The second call corrected that field. These were route/chart contract conflicts, rather than invalid JSON.

The router now states the chart rule in both its prompt and schema field description: only `presentation` chooses a chart for an unchanged previous result. A request for new data remains `analytics` with `chart=auto`, even when it names a graph, table or trend; the analytical planner handles that visualization. Adding/removing provinces or series is explicitly data-changing. Unexpected router properties are forbidden. Invalid chart/route decisions still fail validation and have at most one bounded repair; they are not silently normalized into passing decisions.

A subsequent full HTTP regression exposed a ranking-limit ambiguity. The final router explicitly treats Top N and ordering changes as analytics, and checks any proposed presentation against a rules-understood analytical plan before accepting it. Recognized changes to row limit/order, metric, period or filters reject presentation and request the bounded repair; a persistently invalid output follows the existing safe fallback. This check supplies no province catalogue and executes no warehouse queries. It is a conservative non-geographic cross-check, not a proof of understanding arbitrary language. The analytical planner still validates geographic scope before execution.

A separate prompt defect was found in the shared Groq adapter: it unconditionally appended Planner-only `status`/`plan` instructions to Router and Insight calls. Those instructions now live in the Planner prompt, while the shared adapter only describes the supplied schema. The reproduction did not emit extra Planner fields, so it does not establish that this separate defect caused the four observed chart conflicts.

## Validation

- **235 Python tests passed**, including rejection/repair of unknown routes, null/missing fields, unexpected plan fields, chart/route conflicts and data-changing presentation decisions. Valid unchanged-data charts use one call without querying the warehouse, including an existing ascending ranking and a six-month policy-rate result. The Planner still receives its ready/non-ready plan contract.
- The offline 60-turn conversation regression passed **60/60**.
- At the preceding prompt-only stage, the [18-phrase routing regression](router-validation-container-2026-10-24.json) passed **18/18**, using **18 model calls** and no repair/provider errors. Its fixture contains Thai/English phrases distinct from the original HTTP regression.
- At that same stage, a separate [eight-phrase follow-up validation](router-followup-validation-2026-10-24.json), frozen before the province/series prompt adjustment, passed **8/8**, using **8 calls** and no repairs/provider errors. It tests adding/removing provinces, unchanged-data chart/table requests, explanations and new analytical results. These earlier scores are not final-guard scores or representative held-out evidence.

- The [eight ranking/presentation phrases](router-ranking-validation-2026-10-24.json) passed **8/8** with **8 calls**, no repairs and no provider errors after adding the row-change guard. Subsequent narrow corrections preserved existing order and row limits when the user did not ask to change them; those edge cases are covered in the final 235-test suite. This staged routing score is kept distinct from the final source fingerprint.

| Live stage | Passed turns | Arithmetic | Model calls | Retained behavior |
| --- | --- | --- | --- | --- |
| [Before correction](groq-conversation-live-60-2026-10-24.json) | 60/60 | 40/40 | 67 | Four chart/route conflicts repaired |
| [Prompt-only correction](groq-conversation-router-fix-60-2026-10-24.json) | 58/60 | 38/39 checked; one expected result absent | 63 | Ranking-limit misroute and dependent stale-limit result |
| [Row-change guard, full HTTP run](groq-conversation-router-fix-final-60-2026-10-24.json) | 60/60 | 40/40 | 64 | One policy-chart presentation used fallback after two rejected decisions |
| [Delivered policy guard, targeted C16](groq-policy-presentation-final-2026-10-24.json) | 3/3 | 2/2 | 3 | No repairs, fallback or provider errors |

The successful full run used 57 model-calling turns and three pre-router-gated turns, with zero provider errors. Its median HTTP response time was 698.52 ms, p95 2,931.95 ms and maximum 6,104.91 ms, excluding ten-second pacing. Usage was 53,078 input and 3,130 output tokens (**56,208 total**), versus 46,811 in the earlier full run. Longer instructions increased total token usage despite fewer model calls; no lower-cost claim is made. Prices were unavailable, so cost remains unknown. Single-pass timings are not a performance benchmark.

In C16-3, the guard compared an unrequested parser default of 25 policy-rate months with the confirmed six months. Both valid presentation decisions were rejected and the graph used its safe fallback. The three `RoutingOutputError` records represent those two validation failures plus the graph's fallback record, all from one turn. The delivered guard compares limit/order changes only when the question explicitly requests them. The live three-turn confirmation then returned the correct policy-rate table with one model call per turn and no fallback. This narrow follow-up result is not relabelled as a new full 60-turn run.

The [delivered runtime record](router-fix-runtime-2026-10-24.json) and [full-run runtime record](router-fix-full-run-runtime-2026-10-24.json) fingerprint their respective deployed source, fixtures, evaluators and warehouse. All inspected deployed application files match the reviewed local files at their captured stage. Only the local API source layer was rebuilt on the existing dependency image; no new dependency installation, database-volume change or provider switch was needed. Code and fixture labels were held fixed within each live run.

## Retained development failures

The [first host validation](router-validation-host-initial-2026-10-24.json) attempted 12/18 cases: ten passed, one added-province request was misrouted as presentation, and one provider timeout stopped the run; six were unrun. The province/series rule was added after that observed failure. This is disclosed development feedback, not an untouched test score.

The [second host validation](router-validation-host-retry-2026-10-24.json) attempted 5/18: four passed, then a provider timeout stopped the run; 13 were unrun. The complete 18- and eight-case checks subsequently ran from the API container with the same configured 12-second SDK timeout and bounded repair policy. The underlying cause of the host-call timeouts was not established. Interrupted runs are retained rather than merged into a completed score or selectively retried by case.

The [prompt-only HTTP run](groq-conversation-router-fix-60-2026-10-24.json) completed all 60 turns, with **58 passed**, zero structured-output repairs and zero provider errors. C01-2 (changing Top 7 to Top 3) was misrouted to presentation; C01-3 consequently reused the seven-row result instead of three rows. Those dependent failures prompted the row-change guard. The [prompt-stage runtime fingerprint](router-fix-prompt-runtime-2026-10-24.json) is retained separately from the final implementation. No failing turn or expected label was removed to obtain a later passing result.

## Reproduce

```powershell
# Direct routing only; no SQL. Calls the configured provider.
.\.venv\Scripts\python.exe -m tools.evaluate_router --live --delay 10 --out data/eval/router-new.json
.\.venv\Scripts\python.exe -m tools.evaluate_router --live --delay 10 --fixture tests/fixtures/router_followup_validation.json --out data/eval/router-followup-new.json
# Full hybrid HTTP service and independent warehouse arithmetic.
.\.venv\Scripts\python.exe -m tools.evaluate_conversation --live --base-url http://127.0.0.1:8000 --max-requests 60 --delay 10 --progress --out data/eval/router-http-new.json
# The final policy-chart confirmation selects one three-turn scenario only.
.\.venv\Scripts\python.exe -m tools.evaluate_conversation --live --base-url http://127.0.0.1:8000 --scenario 16 --max-requests 3 --delay 10 --progress --out data/eval/policy-chart-new.json
```

For the container validation, copy `tools/evaluate_router.py` to `/app/tools/` and its selected JSON fixture to `/app/tests/fixtures/`, creating those directories first, then run `docker compose exec -T api python -B -m tools.evaluate_router --live --delay 10 --out /app/data/eval/router-new.json`. The existing data volume exposes that artifact under local `data/eval/`. Host and container results should remain distinguishable.

These are single-pass authored regression checks, with live routing and bounded hybrid analytics. They do not establish an LLM-only score, broad language understanding, repeated-run reliability, load performance or account billing tier. Longer instructions can change token usage; fewer repair calls alone do not establish lower total token cost. The previous raw reports, repairs and timeouts remain part of the evidence.
