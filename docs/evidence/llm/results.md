# Live Gemini comparison results

Measured locally on 11 October 2026 (Asia/Bangkok), using `gemini-2.5-flash` and the same 1,925-row warehouse snapshot. These are single-pass results on a small authored corpus, not a population accuracy estimate.

Ten development turns and fourteen held-out turns (including separate three-turn conversations) were evaluated per strategy. The held-out results were not used to tune the final v3 contract. Each strategy carries its own predicted confirmed context, not the golden previous answer.

| Split | Version | Strategy | All checks | Plan | Numbers | Clarification | API/system errors | p50 / p95 ms | LLM calls | Input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| dev | v1 | rules-only | 8/10 | 6/8 | 6/8 | 1/1 | 0 | 35 / 54 | 0 | 0 / 0 |
| dev | v1 | llm-only | 4/10 | 3/8 | 3/8 | 0/1 | 0 | 3329 / 21015 | 10 | 9333 / 7496 |
| dev | v1 | hybrid | 9/10 | 7/8 | 7/8 | 1/1 | 0 | 26 / 3549 | 2 | 1793 / 594 |
| dev | v3 | rules-only | 10/10 | 8/8 | 8/8 | 1/1 | 0 | 19 / 40 | 0 | 0 / 0 |
| dev | v3 | llm-only | 10/10 | 8/8 | 8/8 | 1/1 | 0 | 3424 / 4998 | 10 | 13515 / 3480 |
| dev | v3 | hybrid | 10/10 | 8/8 | 8/8 | 1/1 | 0 | 22 / 46 | 0 | 0 / 0 |
| heldout | v1 | rules-only | 12/14 | 8/10 | 8/10 | 3/3 | 0 | 21 / 43 | 0 | 0 / 0 |
| heldout | v1 | llm-only | 6/14 | 3/10 | 7/10 | 2/3 | 0 | 2930 / 5226 | 14 | 13157 / 4205 |
| heldout | v1 | hybrid | 12/14 | 8/10 | 8/10 | 3/3 | 0 | 21 / 2886 | 2 | 1796 / 511 |
| heldout | v3 | rules-only | 14/14 | 10/10 | 10/10 | 3/3 | 0 | 18 / 41 | 0 | 0 / 0 |
| heldout | v3 | llm-only | 6/14 | 3/10 | 8/10 | 2/3 | 0 | 3464 / 6568 | 14 | 18771 / 5466 |
| heldout | v3 | hybrid | 14/14 | 10/10 | 10/10 | 3/3 | 0 | 18 / 39 | 0 | 0 / 0 |

## Interpretation and changes

- The final LLM-only planner passes 10/10 development turns but only 6/14 held-out turns under the strict all-checks rubric (unchanged from the 6/14 baseline). Held-out numeric correctness improves from 7/10 to 8/10 expected-ready turns. Development improvement did **not** establish broad generalization.
- Residual v3 failures include explicit Buddhist-year conversion (H02/H06), strict versus inclusive thresholds (H07) and refusal instead of asking for a month (H11). Some period/context flags are redundant start-date mismatches (H01/H12/H13/H14) with correct numbers; the report keeps that distinction visible. These held-out cases were not used for further tuning.
- Final hybrid and rules-only each pass 14/14 held-out turns, with zero model calls on that particular split. The baseline hybrid passes 9/10 development turns versus 8/10 for rules-only, but both pass 12/14 held-out turns. The evidence supports deterministic coverage and conservative routing, not a claim that adding an LLM always improves answers.
- The four main comparison reports contain 52 completed Gemini calls, plus 10 calls in the intermediate v2 development report and one separately verified production fallback smoke request. Initial missing-SDK failures consumed zero model requests.

- v1 is the original prompt and lexical parser. Development failures included invented unavailable dates, incorrect supplemental ratio YoY, English clarification choices and lost conversation scope.
- v2 added explicit date/YoY/Thai-language/scope instructions and development-driven synonyms (`ยอดออม`, `เงินกู้`). Its [intermediate development report](dev-v2-live.json) is retained, including remaining temporal-intent errors.
- v3 retains that prompt and adds a shape invariant: period-grouped results have trend intent. It rejects ready-without-plan and non-ready executable plans. Validation does not use golden labels to change metrics, dates or numerical results.
- The hybrid baseline can resolve some paraphrases that rules alone misses, but it can also inherit LLM mistakes. After lexical improvements, this small final corpus may exercise few or no hybrid LLM calls: do not interpret that as a broad test of the fallback. Larger unseen paraphrase corpora and repeated trials are still needed.
- All modes share the same bounded read-only SQL executor, independent arithmetic oracle and conversation controller. “LLM-only” means LLM-only planning, not unguarded arbitrary SQL. Strategy selection is benchmark-only, not a public API option.

## Scoring and limitations

Ready turns require correct full scope/primary metric, all requested measures, row order/count and independently computed numbers. Additional display measures are allowed. Names are compared using known province codes. No-result turns must not expose stale rows. Clarification quality uses a documented Thai term/alternatives rubric; it is a heuristic, not a blinded human assessment.

Plan and number denominators include only expected-ready cases; clarification denominators include only expected-clarification cases. “All checks” also includes unsupported refusals. API/system error rate is reported separately from semantic errors; returning a valid HTTP response is not scored as success. Full-plan equality is intentionally strict: a redundant start date on a single-month province query can fail the plan check while the independently checked numerical result is correct. A context tag marks a scope-related divergence in a dialogue, not proof that memory was the root cause.

Latency includes planner, SQL and answer processing, but excludes harness pacing and golden-label scoring. It includes cold initialization where encountered. Each completed turn was attempted once with provider retries disabled; no repeated-run confidence interval is claimed. SDK setup failures made no model requests and are preserved separately in the baseline report, not silently counted as model errors or discarded successful/failed model trials.

Actual provider token usage is recorded, including available reasoning-token counts. Prices were not configured, so live cost estimates are **null**, not “free” or zero. Optional configured uncached rates are an estimate only, not a billing reconciliation.

## Raw evidence

- [dev v1: plans, messages, error categories and telemetry](dev-v1-live.json) — completed 2026-10-10T18:52:25.306425+00:00; warehouse SHA-256 `f14d8f3b54c3e9e2901ba9c5c105bca342e6fa349558721a78493e421dbef290`.
- [dev v3: plans, messages, error categories and telemetry](dev-v3-live.json) — completed 2026-10-10T18:56:33.667191+00:00; warehouse SHA-256 `f14d8f3b54c3e9e2901ba9c5c105bca342e6fa349558721a78493e421dbef290`.
- [heldout v1: plans, messages, error categories and telemetry](heldout-v1-live.json) — completed 2026-10-10T18:58:48.261471+00:00; warehouse SHA-256 `f14d8f3b54c3e9e2901ba9c5c105bca342e6fa349558721a78493e421dbef290`.
- [heldout v3: plans, messages, error categories and telemetry](heldout-v3-live.json) — completed 2026-10-10T19:01:43.246323+00:00; warehouse SHA-256 `f14d8f3b54c3e9e2901ba9c5c105bca342e6fa349558721a78493e421dbef290`.

Corpus: [versioned authored labels](../../../tests/fixtures/llm_eval_cases.json). Reproduction and operational telemetry: [evaluation guide](../../llm-evaluation.md).
