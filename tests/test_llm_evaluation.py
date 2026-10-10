import json
from types import SimpleNamespace
import pytest
from bank.observability import capture, record, summarize, token_usage
from bank.query import QueryPlan
from tools.benchmark_llm import differences, aggregate, ROOT

def test_telemetry_allowlist_and_unknown_usage(monkeypatch):
    monkeypatch.delenv('LLM_INPUT_USD_PER_MILLION',raising=False)
    monkeypatch.delenv('LLM_OUTPUT_USD_PER_MILLION',raising=False)
    with capture() as events:
        record('llm',provider='gemini',latency_ms=10,api_key='private',question='private',error_message='private')
        record('failure',failure_type='TimeoutError',phase='planner')
    out=summarize(events,20,'error')
    assert out['llm_calls']==1 and out['input_tokens'] is None
    assert out['estimated_cost_usd'] is None and out['error']
    assert 'private' not in json.dumps(out) and 'private' not in json.dumps(events)

def test_usage_and_configured_cost(monkeypatch):
    monkeypatch.setenv('LLM_INPUT_USD_PER_MILLION','1')
    monkeypatch.setenv('LLM_OUTPUT_USD_PER_MILLION','2')
    raw=SimpleNamespace(usage_metadata={'input_tokens':100,'output_tokens':50,'total_tokens':150,'output_token_details':{'reasoning':10}})
    with capture() as events: record('llm',latency_ms=5,**token_usage(raw))
    out=summarize(events,10,'ready')
    assert out['estimated_cost_usd']==pytest.approx(.0002)
    assert out['reasoning_tokens']==10
    monkeypatch.setenv('LLM_OUTPUT_USD_PER_MILLION','nan')
    assert summarize(events,10,'ready')['estimated_cost_usd'] is None

def test_contextvar_isolation():
    with capture() as outer:
        record('llm',input_tokens=1)
        with capture() as inner: record('llm',input_tokens=2)
        record('llm',input_tokens=3)
    assert [e['input_tokens'] for e in outer]==[1,3]
    assert [e['input_tokens'] for e in inner]==[2]

def test_split_dialogues_do_not_leak():
    cases=json.loads((ROOT/'tests/fixtures/llm_eval_cases.json').read_text(encoding='utf-8'))['cases']
    assert len(cases)==24 and len({c['id'] for c in cases})==24
    assert len({c['q'] for c in cases})==24
    dev={c['dialogue'] for c in cases if c['split']=='dev' and c.get('dialogue')}
    heldout={c['dialogue'] for c in cases if c['split']=='heldout' and c.get('dialogue')}
    assert dev.isdisjoint(heldout)

def test_full_plan_comparison_catches_unlabelled_filters():
    expected=QueryPlan(metric='credits_per_person',group_by='province',limit=3,end_period='2026-07-01')
    wrong=QueryPlan(metric='credits',group_by='province',limit=10,exclude_bangkok=True)
    assert {'metric','limit','province','metrics'}.issubset(differences(wrong,expected,'2026-07-01'))
    assert differences(expected,expected,'2026-07-01')==[]

def test_rules_zero_tokens_not_false_paid_cost(monkeypatch):
    monkeypatch.delenv('LLM_INPUT_USD_PER_MILLION',raising=False)
    out=summarize([],5,'clarification','rules-only')
    assert out['llm_calls']==0 and out['total_tokens']==0 and out['clarification']

def test_missing_usage_does_not_become_zero_in_aggregate():
    row={'strategy':'llm-only','passed':False,'status_correct':False,'plan_correct':False,'numbers_correct':False,
         'clarification_correct':None,'status':'error','error_categories':['provider_error'],
         'telemetry':summarize([{'event':'llm','latency_ms':20}],20,'error')}
    out=aggregate([row])['llm-only']
    assert out['input_tokens'] is None and out['errors']==1 and out['error_rate']==1

def test_english_province_alias_is_not_false_semantic_failure():
    a=QueryPlan(metric='credits',group_by='province',intent='comparison',provinces=['Chiengmai','Chonburi'])
    b=QueryPlan(metric='credits',group_by='province',intent='comparison',provinces=['เชียงใหม่','ชลบุรี'])
    assert differences(a,b,'2026-07-01')==[]

def test_v2_lexical_fix_preserves_ratio_and_limit():
    from bank.query import rules_plan
    plan=rules_plan('เงินกู้ต่อคนมากที่สุด 3 จังหวัด',version='v2')
    assert plan.metric=='credits_per_person' and plan.limit==3
    plan=rules_plan('ช่วยดูยอดออมของทั้งประเทศตามเดือนย้อนหลัง 3 เดือนหน่อย',version='v2')
    assert plan.metric=='deposits' and plan.group_by=='period' and plan.limit==3

def test_service_telemetry_is_emitted_without_question(monkeypatch):
    import bank.chat as chat
    outputs=[]
    monkeypatch.setattr(chat,'emit',outputs.append)
    def invoke(*args,**kwargs):
        record('llm',latency_ms=2,input_tokens=10,output_tokens=5,total_tokens=15)
        return {'mode':'clarification','answer':'choose metric','error':'choose metric','choices':[]}
    monkeypatch.setattr(chat,'graph',lambda:SimpleNamespace(invoke=invoke))
    chat.ask('secret-test-question','private-session')
    assert outputs[0]['llm_calls']==1 and outputs[0]['total_tokens']==15 and outputs[0]['clarification']
    assert 'secret-test-question' not in json.dumps(outputs) and 'private-session' not in json.dumps(outputs)

def test_v3_temporal_intent_validation_never_changes_metric_or_dates():
    from bank.chat import PlannerDecision, validate_decision
    plan=QueryPlan(metric='credits_per_person',group_by='period',intent='comparison',provinces=['เชียงใหม่','ชลบุรี'],limit=3)
    decision=validate_decision(PlannerDecision(status='ready',plan=plan))
    assert decision.plan.intent=='trend' and decision.plan.metric=='credits_per_person'
    assert decision.plan.end_period is None and decision.plan.limit==3
    with pytest.raises(RuntimeError): validate_decision(PlannerDecision(status='ready'))
    with pytest.raises(RuntimeError): validate_decision(PlannerDecision(status='unsupported',plan=plan))

def test_log_aggregation_never_echoes_raw_content():
    from tools.observe_chat import aggregate_events
    rows=['provider error private-key',json.dumps({'event':'bank_chat',**summarize([],10,'ready')}),
          json.dumps({'event':'unrelated','api_key':'private-key'})]
    output=aggregate_events(rows)
    assert output['requests']==1 and 'private-key' not in json.dumps(output)
