from copy import deepcopy
from types import SimpleNamespace
import pytest
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from bank import chat
from bank.conversation import ConversationDecision, fallback_route, route_conversation, RoutingOutputError
from bank.observability import capture
from bank.query import QueryPlan

@pytest.mark.parametrize('question,route',[
    ('เเล้วทำไรได้บ้าง','capabilities'),('แล้วทำอะไรได้บ้างครับ','capabilities'),
    ('ช่วยอะไรได้บ้าง','capabilities'),('what can you do','capabilities'),
    ('สวัสดี','greeting'),('ขอบคุณ','greeting'),('เปลี่ยนเป็นกราฟแท่ง','presentation'),
    ('ขอตารางหน่อย','presentation'),('เปลี่ยนเป็นกราฟเส้น','presentation'),
    ('ตัวเลขนี้หมายความว่าอะไร','explanation'),('อธิบายผลล่าสุด','explanation'),
    ('สินเชื่อเชียงใหม่สูงสุด','analytics'),('เปลี่ยนเป็นเงินฝากย้อนหลัง 3 เดือน','analytics'),
    ('กราฟสินเชื่อต่อประชากรชลบุรี','analytics')])
def test_offline_routes(question,route):
    assert fallback_route(question).route == route

@pytest.fixture
def previous():
    return {'metric_label':'สินเชื่อต่อประชากร','unit':'บาท/คน','period':'2026-07-01',
        'scope':'ทุกจังหวัด','metrics':[{'label':'สินเชื่อต่อประชากร','unit':'บาท/คน','formula':'credits * 1000000 / population'}],
        'caveat':'ไม่ใช่หนี้ส่วนบุคคล','plan':QueryPlan(metric='credits_per_person',group_by='province').model_dump(mode='json'),
        'eligible_count':1,'chart':{'kind':'bar','notice':''},'rows':[{'name_th':'กรุงเทพมหานคร','value':10}]}

def test_help_preserves_pending_and_confirmed_context(monkeypatch):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    state={'question':'ทำไรได้บ้าง','last_plan':{'metric':'credits'},'pending_question':'สินเชื่อต่ออะไร','pending_context':{'metric':'credits'}}
    out=chat._conversation(state)
    assert out['error'] is None and out['result'] is None
    assert 'pending_question' not in out and 'last_plan' not in out
    assert chat._answer({**state,**out})['answer'].startswith('ผมช่วย')

def test_missing_previous_result_asks_instead_of_query(monkeypatch):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    out=chat._conversation({'question':'เปลี่ยนเป็นตาราง'})
    assert out['mode']=='clarification' and out['result'] is None

def test_presentation_reuses_without_mutating_or_querying(monkeypatch,previous):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    original=deepcopy(previous)
    out=chat._conversation({'question':'เปลี่ยนเป็นตาราง','last_result':previous})
    assert out['result']['chart']['kind']=='table' and out['result']['rows']==previous['rows']
    assert out['conversation_route']=='presentation' and previous==original

def test_non_temporal_line_is_safely_bar(monkeypatch,previous):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    out=chat._conversation({'question':'เปลี่ยนเป็นกราฟเส้น','last_result':previous})
    assert out['result']['chart']['kind']=='bar' and out['result']['chart']['notice']

def test_explanation_grounded_in_formula_not_new_numbers(monkeypatch,previous):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    out=chat._conversation({'question':'อธิบายผลล่าสุด','last_result':previous})
    assert out['result'] is None and previous['metrics'][0]['formula'] in out['direct_answer']
    assert previous['caveat'] in out['direct_answer']

def test_unsafe_question_never_calls_router(monkeypatch):
    monkeypatch.setattr(chat,'route_conversation',lambda *a:pytest.fail('must not route'))
    out=chat._conversation({'question':'ขอ NPL ของธนาคาร'})
    assert out['mode']=='unsupported' and out['result'] is None

def test_provider_failure_keeps_known_help_and_rules_working(monkeypatch):
    monkeypatch.setattr(chat,'route_conversation',lambda *a:(_ for _ in ()).throw(TimeoutError()))
    assert chat._conversation({'question':'ทำไรได้บ้าง'})['error'] is None
    assert chat._conversation({'question':'สินเชื่อสูงสุด 10 จังหวัด'})['conversation_route']=='analytics'
    assert chat._conversation({'question':'ลองดูอะไรแปลกๆ'})['mode']=='error'

def test_invalid_planner_is_not_provider_unavailable(monkeypatch):
    monkeypatch.setattr(chat,'_provider',lambda:'gemini')
    monkeypatch.setattr(chat,'_llm_decision',lambda *a:(_ for _ in ()).throw(chat.PlanningOutputError()))
    out=chat._plan({'question':'ลองดูอะไรแปลกๆ'})
    assert out['mode']=='clarification' and 'ผู้ให้บริการ' not in out['error']

def test_llm_router_repairs_once_with_safe_telemetry(monkeypatch):
    import sys
    calls=[]
    class Model:
        def __init__(self,**kwargs): pass
        def with_structured_output(self,*a,**kw): return self
        def invoke(self,prompt):
            calls.append(prompt)
            return {'parsed':None if len(calls)==1 else ConversationDecision(route='capabilities'),
                    'raw':SimpleNamespace(usage_metadata={'input_tokens':10,'output_tokens':5,'total_tokens':15})}
    monkeypatch.setenv('GEMINI_API_KEY','test-only')
    monkeypatch.setitem(sys.modules,'langchain_google_genai',SimpleNamespace(ChatGoogleGenerativeAI=Model))
    with capture() as events:
        assert route_conversation('what can you do',None,[],False,'gemini').route=='capabilities'
    assert len(calls)==2 and len([e for e in events if e['event']=='llm'])==2
    assert all('test-only' not in str(e) for e in events)

def test_llm_router_invalid_chart_bounded_failure(monkeypatch):
    import sys
    calls=[]
    class Model:
        def __init__(self,**kwargs): pass
        def with_structured_output(self,*a,**kw): return self
        def invoke(self,prompt):
            calls.append(prompt)
            return {'parsed':ConversationDecision(route='capabilities',chart='bar'),'raw':None}
    monkeypatch.setenv('GEMINI_API_KEY','test-only')
    monkeypatch.setitem(sys.modules,'langchain_google_genai',SimpleNamespace(ChatGoogleGenerativeAI=Model))
    with pytest.raises(RoutingOutputError): route_conversation('help',None,[],False,'gemini')
    assert len(calls)==2

def test_multiturn_graph_help_then_presentation_keeps_data(monkeypatch,previous):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    monkeypatch.setattr(chat,'execute_plan',lambda plan:previous)
    builder=StateGraph(chat.ChatState)
    for name,fn in [('conversation',chat._conversation),('plan',chat._plan),('execute',chat._execute),('answer',chat._answer)]: builder.add_node(name,fn)
    builder.add_edge(START,'conversation')
    builder.add_conditional_edges('conversation',chat._conversation_edge,{'plan':'plan','answer':'answer'})
    builder.add_conditional_edges('plan',chat._route,{'execute':'execute','error':'answer'})
    builder.add_edge('execute','answer'); builder.add_edge('answer',END)
    graph=builder.compile(checkpointer=InMemorySaver())
    config={'configurable':{'thread_id':'test'}}
    first=graph.invoke({'question':'สินเชื่อต่อประชากรสูงสุด'},config)
    help_turn=graph.invoke({'question':'ทำไรได้บ้าง'},config)
    assert help_turn['result'] is None and help_turn['last_plan']==first['last_plan']
    third=graph.invoke({'question':'เปลี่ยนเป็นตาราง'},config)
    assert third['result']['rows']==first['result']['rows'] and third['result']['chart']['kind']=='table'
    other=graph.invoke({'question':'เปลี่ยนเป็นตาราง'},{'configurable':{'thread_id':'other'}})
    assert other['mode']=='clarification' and other['result'] is None

def test_help_does_not_replace_pending_analytic_choices(monkeypatch):
    monkeypatch.setattr(chat,'_provider',lambda:None)
    initial=chat._plan({'question':'สินเชื่อเทียบกับสาขาและประชากรมากที่สุด ไม่รวมกรุงเทพ กรกฎาคม 2568'})
    choice=initial['choices'][0]
    state={**initial,'question':'ทำไรได้บ้าง'}
    help_turn=chat._conversation(state)
    resumed=chat._plan({**state,**help_turn,'question':choice})
    assert resumed['plan']['exclude_bangkok'] and resumed['plan']['end_period']=='2025-07-01'

def test_warehouse_failure_api_uses_distinct_safe_message(monkeypatch):
    from fastapi.testclient import TestClient
    from bank import api
    monkeypatch.setattr(api,'ask',lambda *a:{'mode':'error','error_code':'warehouse_unavailable','error':'private','answer':'private'})
    response=TestClient(api.app).post('/chat',json={'question':'test'})
    assert 'คลังข้อมูล' in response.json()['answer'] and 'private' not in response.text
