"""Generate a reviewer-facing results artifact from completed measured reports."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'docs/evidence/llm'

def main():
    reports={}
    for split in ['dev','heldout']:
        for version in ['v1','v3']:
            path=DIRECTORY/f'{split}-{version}-live.json'
            report=json.loads(path.read_text(encoding='utf-8'))
            if not report.get('completed_utc') or report.get('stop_reason'): raise ValueError(f'Incomplete report: {path.name}')
            ids={r['id'] for r in report['rows']}
            for strategy in ['rules-only','llm-only','hybrid']:
                measured=[r['id'] for r in report['rows'] if r['strategy']==strategy]
                if len(measured)!=len(ids) or set(measured)!=ids: raise ValueError('Unequal coverage')
            reports[(split,version)]=report
    if len({r['warehouse_sha256'] for r in reports.values()})!=1: raise ValueError('Warehouse snapshots differ')
    if len({r['fixture_sha256'] for r in reports.values()})!=1: raise ValueError('Fixture snapshots differ')
    text=['# Live Gemini comparison results','',
          'Measured locally on 11 October 2026 (Asia/Bangkok), using `gemini-2.5-flash` and the same 1,925-row warehouse snapshot. These are single-pass results on a small authored corpus, not a population accuracy estimate.','',
          'These are historical **analytical planner** measurements, before the subsequent conversation router and service timeout/error-handling changes. Router calls and HTTP overhead are outside the reported latency/token figures. See [current verification scope](../../verification.md).','',
          'Ten development turns and fourteen held-out turns (including separate three-turn conversations) were evaluated per strategy. The held-out results were not used to tune the final v3 contract. Each strategy carries its own predicted confirmed context, not the golden previous answer.','',
          '| Split | Version | Strategy | All checks | Plan | Numbers | Clarification | API/system errors | p50 / p95 ms | LLM calls | Input / output tokens |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    def score(value):return f"{value['correct']}/{value['total']}"
    for split in ['dev','heldout']:
        for version in ['v1','v3']:
            r=reports[(split,version)]
            for strategy in ['rules-only','llm-only','hybrid']:
                s=r['summary'][strategy]
                text.append(f"| {split} | {version} | {strategy} | {s['passed']}/{s['total']} | {score(s['plan'])} | {score(s['numbers'])} | {score(s['clarification'])} | {s['errors']} | {s['latency_p50_ms']:.0f} / {s['latency_p95_ms']:.0f} | {s['llm_calls']} | {s['input_tokens']} / {s['output_tokens']} |")
    text += ['', '## Interpretation and changes','',
      '- The final LLM-only planner passes 10/10 development turns but only 6/14 held-out turns under the strict all-checks rubric (unchanged from the 6/14 baseline). Held-out numeric correctness improves from 7/10 to 8/10 expected-ready turns. Development improvement did **not** establish broad generalization.','- Residual v3 failures include explicit Buddhist-year conversion (H02/H06), strict versus inclusive thresholds (H07) and refusal instead of asking for a month (H11). Some period/context flags are redundant start-date mismatches (H01/H12/H13/H14) with correct numbers; the report keeps that distinction visible. These held-out cases were not used for further tuning.','- Final hybrid and rules-only each pass 14/14 held-out turns, with zero model calls on that particular split. The baseline hybrid passes 9/10 development turns versus 8/10 for rules-only, but both pass 12/14 held-out turns. The evidence supports deterministic coverage and conservative routing, not a claim that adding an LLM always improves answers.','- The four main comparison reports contain 52 completed Gemini calls, plus 10 calls in the intermediate v2 development report and one separately verified local service fallback smoke request. Initial missing-SDK failures consumed zero model requests.','',
      '- v1 is the original prompt and lexical parser. Development failures included invented unavailable dates, incorrect supplemental ratio YoY, English clarification choices and lost conversation scope.','- v2 added explicit date/YoY/Thai-language/scope instructions and development-driven synonyms (`ยอดออม`, `เงินกู้`). Its [intermediate development report](dev-v2-live.json) is retained, including remaining temporal-intent errors.','- v3 retains that prompt and adds a shape invariant: period-grouped results have trend intent. It rejects ready-without-plan and non-ready executable plans. Validation does not use golden labels to change metrics, dates or numerical results.','- The hybrid baseline can resolve some paraphrases that rules alone misses, but it can also inherit LLM mistakes. After lexical improvements, this small final corpus may exercise few or no hybrid LLM calls: do not interpret that as a broad test of the fallback. Larger unseen paraphrase corpora and repeated trials are still needed.','- All modes share the same bounded read-only SQL executor, independent arithmetic oracle and conversation controller. “LLM-only” means LLM-only planning, not unguarded arbitrary SQL. Strategy selection is benchmark-only, not a public API option.','',
      '## Scoring and limitations','',
      'Ready turns require correct full scope/primary metric, all requested measures, row order/count and independently computed numbers. Additional display measures are allowed. Names are compared using known province codes. No-result turns must not expose stale rows. Clarification quality uses a documented Thai term/alternatives rubric; it is a heuristic, not a blinded human assessment.','',
      'Plan and number denominators include only expected-ready cases; clarification denominators include only expected-clarification cases. “All checks” also includes unsupported refusals. API/system error rate is reported separately from semantic errors; returning a valid HTTP response is not scored as success. Full-plan equality is intentionally strict: a redundant start date on a single-month province query can fail the plan check while the independently checked numerical result is correct. A context tag marks a scope-related divergence in a dialogue, not proof that memory was the root cause.','',
      'Latency includes planner, SQL and answer processing, but excludes harness pacing and golden-label scoring. It includes cold initialization where encountered. Each completed turn was attempted once with provider retries disabled; no repeated-run confidence interval is claimed. SDK setup failures made no model requests and are preserved separately in the baseline report, not silently counted as model errors or discarded successful/failed model trials.','',
      'Actual provider token usage is recorded, including available reasoning-token counts. Prices were not configured, so live cost estimates are **null**, not “free” or zero. Optional configured uncached rates are an estimate only, not a billing reconciliation.','',
      '## Raw evidence','']
    for (split,version),r in reports.items():
        text.append(f"- [{split} {version}: plans, messages, error categories and telemetry]({split}-{version}-live.json) — completed {r['completed_utc']}; warehouse SHA-256 `{r['warehouse_sha256']}`.")
    text += ['', 'Corpus: [versioned authored labels](../../../tests/fixtures/llm_eval_cases.json). Reproduction and operational telemetry: [evaluation guide](../../llm-evaluation.md).', '']
    (DIRECTORY/'results.md').write_text('\n'.join(text),encoding='utf-8')
    print('\n'.join(text[:len(text)]))

if __name__=='__main__':main()
