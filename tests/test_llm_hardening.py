from types import SimpleNamespace
import pytest
from bank import llm_runtime as runtime, chat
from bank.query import QueryPlan, Clarification, rules_plan
from bank.semantic_validation import validate_semantics
from bank.insights import explain_result, InsightSelection
from bank.observability import capture, summarize


@pytest.fixture(autouse=True)
def reset_circuits():
    runtime._circuits.clear()
    yield
    runtime._circuits.clear()


@pytest.mark.parametrize('message,expected', [
    ('RESOURCE_EXHAUSTED key=secret', 'quota_exhausted'),
    ('API_KEY_INVALID secret', 'authentication_failed'),
    ('PERMISSION_DENIED', 'authentication_failed'),
    ('404 NOT_FOUND', 'model_unavailable'), ('timed out', 'provider_timeout'),
    ('unknown secret', 'provider_failure')])
def test_safe_error_taxonomy(message, expected):
    assert runtime.classify_failure(Exception(message)) == expected


def test_quota_breaker_avoids_repeat_requests_and_never_leaks(monkeypatch):
    calls = []
    class Model:
        def with_structured_output(self, *args, **kwargs): return self
        def invoke(self, prompt):
            calls.append(1)
            raise Exception('RESOURCE_EXHAUSTED api_key=very-private')
    with capture() as events:
        for _ in range(2):
            with pytest.raises(runtime.ProviderUnavailable):
                runtime.invoke_structured(Model(), object, 'private question', 'gemini', 'router')
    assert len(calls) == 1
    assert runtime.provider_health('gemini')['last_failure'] == 'quota_exhausted'
    assert 'very-private' not in str(events) and 'private question' not in str(events)
    assert summarize(events, 1, 'ready')['provider_errors'] == 1
    monkeypatch.setenv('GEMINI_API_KEY', 'rotated')
    assert not runtime.provider_health('gemini')['circuit_open']


def test_circuit_recovers_after_cooldown(monkeypatch):
    current = [10]
    monkeypatch.setattr(runtime, 'monotonic', lambda: current[0])
    runtime._circuits[runtime._identity('gemini')] = {'until':20, 'reason':'quota_exhausted'}
    current[0] = 21
    model = SimpleNamespace(with_structured_output=lambda *a,**kw:SimpleNamespace(invoke=lambda p:{'raw':None}))
    runtime.invoke_structured(model, object, 'q', 'gemini', 'router')
    assert runtime.provider_health('gemini')['last_failure'] is None


def test_request_budget_caps_calls_and_deadline(monkeypatch):
    model = SimpleNamespace(with_structured_output=lambda *a,**kw:SimpleNamespace(invoke=lambda p:{'raw':None}))
    with runtime.request_budget():
        for _ in range(3): runtime.invoke_structured(model, object, 'q', 'gemini', 'router')
        with pytest.raises(runtime.ProviderUnavailable, match='request_budget_exhausted'):
            runtime.invoke_structured(model, object, 'q', 'gemini', 'planner')
    with runtime.request_budget():
        runtime._request.get()['deadline'] = -1
        with pytest.raises(runtime.ProviderUnavailable): runtime.build_model('gemini')


@pytest.mark.parametrize('question,changes', [
    ('สินเชื่อต่อประชากรสูงสุด 5', {'metric':'credits','metrics':['credits']}),
    ('เงินฝากสูงสุด 5 กรกฎาคม 2568', {'end_period':'2568-07-01'}),
    ('เงินฝากสูงสุด 5 ประชากรมากกว่า 1 ล้านคน', {'strict_filters':[]}),
    ('เงินฝากเชียงใหม่', {'province':'ชลบุรี'}),
    ('เงินฝากสูงสุด 5 ไม่รวมกรุงเทพ', {'exclude_bangkok':False}),
    ('สินเชื่อต่อสาขาสูงสุด 5 พร้อม YoY', {'include_yoy':False}),
    ('สินเชื่อสูงสุด 5 สินเชื่ออย่างน้อย 2 พันล้านบาท', {'min_credits':2}),
])
def test_explicit_semantic_conflict_is_not_executed(question, changes):
    plan = rules_plan(question, version='v4').model_dump(mode='json')
    plan.update(changes)
    with pytest.raises(Clarification):
        validate_semantics(question, QueryPlan.model_validate(plan))


def test_iso_buddhist_year_and_billion_units():
    plan = rules_plan('สินเชื่อสูงสุด 5 2568-07 สินเชื่อมากกว่า 2 พันล้านบาท', version='v4')
    assert str(plan.end_period) == '2025-07-01' and plan.min_credits == 2000
    assert 'min_credits' in plan.strict_filters
    validate_semantics('สินเชื่อสูงสุด 5 2568-07 สินเชื่อมากกว่า 2 พันล้านบาท', plan)


@pytest.mark.parametrize('text,field,value,strict', [
    ('ประชากร > 5 แสนคน','min_population',500000,True),
    ('ประชากร >= 2 พันคน','min_population',2000,False),
    ('สินเชื่อมากกว่า 4 พันบาท','min_credits',0.004,True),
    ('สินเชื่ออย่างน้อย 5 แสนบาท','min_credits',0.5,False),
])
def test_threshold_units_and_symbolic_strictness(text,field,value,strict):
    plan = rules_plan('สินเชื่อสูงสุด 5 '+text, version='v4')
    assert getattr(plan,field) == value and (field in plan.strict_filters) == strict


def test_known_metric_does_not_block_language_fallback(monkeypatch):
    monkeypatch.setattr(chat, '_provider', lambda:'gemini')
    monkeypatch.setattr(chat, 'rules_plan', lambda *a: (_ for _ in ()).throw(Clarification('unrecognized phrasing')))
    calls = []
    def decide(*a):
        calls.append(1)
        return chat.PlannerDecision(status='ready', plan=QueryPlan(metric='credits',group_by='province'))
    monkeypatch.setattr(chat, '_llm_decision', decide)
    assert chat._plan({'question':'สินเชื่อสูงสุด'})['plan']['metric'] == 'credits'
    assert calls == [1]


def test_missing_month_does_not_reach_provider(monkeypatch):
    monkeypatch.setattr(chat, '_provider', lambda:'gemini')
    monkeypatch.setattr(chat, '_llm_decision', lambda *a:pytest.fail('ambiguous year must ask'))
    assert chat._plan({'question':'สินเชื่อปี 2568'})['mode'] == 'clarification'


def test_safe_insights_reject_unverified_ids(monkeypatch):
    from bank import insights
    result = {'metric_label':'เงินฝาก', 'unit':'ล้านบาท', 'period':'2026-07-01',
        'scope':'เฉพาะจังหวัดที่เลือก','plan':{'group_by':'province'},
        'rows':[{'name_th':'เชียงใหม่','value':20},{'name_th':'ชลบุรี','value':30}],
        'metrics':[{'label':'เงินฝาก','unit':'ล้านบาท','formula':'SUM(deposits)'}],
        'sources':['BOT'], 'caveat':'ยอดคงค้างไม่ใช่ยอดปล่อยใหม่'}
    monkeypatch.setattr(insights, 'build_model', lambda *a:object())
    monkeypatch.setattr(insights, 'invoke_structured', lambda *a:{'parsed':InsightSelection(evidence_ids=['fabricated'])})
    answer, mode = explain_result(result,'อธิบายผลล่าสุด','gemini')
    assert mode == 'verified evidence' and '10.00' in answer and '30.00' in answer
    assert 'ไม่ใช่ข้อสรุปนอกขอบเขต' in answer and 'fabricated' not in answer


def test_api_default_sessions_are_unique():
    from bank.api import ChatRequest
    assert ChatRequest(question='a').session_id != ChatRequest(question='b').session_id


@pytest.mark.parametrize('question', [
    'สินเชื่อรายอำเภอ', 'เงินฝากเดือนหน้า', 'สินเชื่อสูงสุด ประชากรน้อยกว่า 1000',
    'สินเชื่อสูงสุด เงินฝากอย่างน้อย 2000',
])
def test_unsupported_scope_or_filter_is_not_silently_ignored(question):
    out = chat._plan({'question':question})
    assert out['mode'] == 'unsupported' and out['plan'] is None


def test_pending_month_reply_reuses_original_metric():
    initial = chat._plan({'question':'สินเชื่อปี 2568'})
    result = chat._plan({**initial,'question':'กรกฎาคม 2568'})
    assert result['plan']['metric'] == 'credits' and result['plan']['end_period'] == '2025-07-01'


def test_router_outage_does_not_block_pending_short_answer(monkeypatch):
    initial = chat._plan({'question':'สินเชื่อปี 2568'})
    monkeypatch.setattr(chat, 'route_conversation', lambda *a: (_ for _ in ()).throw(runtime.ProviderUnavailable('quota_exhausted')))
    state = {**initial,'question':'กรกฎาคม 2568'}
    routed = chat._conversation(state)
    assert routed['error'] is None and routed['conversation_route'] == 'analytics'
    assert chat._plan({**state,**routed})['plan']['end_period'] == '2025-07-01'


def test_model_evidence_selection_is_bounded(monkeypatch):
    from bank import insights
    result = {'metric_label':'สินเชื่อ','unit':'ล้านบาท','period':'2026-07-01','scope':'ทุกจังหวัด',
        'plan':{'group_by':'period'},'rows':[{'period':'2026-06-01','value':10},{'period':'2026-07-01','value':15}],
        'metrics':[],'sources':['BOT'],'caveat':'not causal'}
    monkeypatch.setattr(insights, 'build_model', lambda *a:object())
    monkeypatch.setattr(insights, 'invoke_structured', lambda *a:{'parsed':InsightSelection(evidence_ids=['trend_0'])})
    answer, mode = explain_result(result,'อธิบายผลล่าสุด','gemini')
    assert mode == 'LLM-selected verified evidence' and '+5.00' in answer
    assert 'ไม่ใช่ YoY' in answer and 'BOT' in answer
