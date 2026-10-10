"""80 Thai golden questions plus independent real-data arithmetic and dialogue checks."""
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import text
from bank.db import read_engine
from bank.query import Clarification, QueryPlan, execute_plan, rules_plan, requested_metrics, _validate_query
from bank.chat import ask, _answer, _plan, PlannerDecision

CASES=json.loads((Path(__file__).parent/'fixtures/chat_cases.json').read_text(encoding='utf-8'))

@pytest.fixture(scope='module')
def raw():
    with read_engine().connect() as conn:
        return [dict(r) for r in conn.execute(text('SELECT * FROM mart_province_month ORDER BY period,province_code')).mappings()]

def arithmetic(rows,metric):
    def total(column):
        values=[r[column] for r in rows if r[column] is not None]
        return sum(values) if values else None
    def ratio(n,d,factor=1):
        a,b=total(n),total(d)
        return factor*a/b if a is not None and b else None
    if metric=='credits': return total('credits_million_baht')
    if metric=='deposits': return total('deposits_million_baht')
    if metric=='branches': return total('branches')
    if metric=='gpp': return total('gpp_million_baht')
    if metric=='credits_per_person': return ratio('credits_million_baht','population',1000000)
    if metric=='credits_per_branch': return ratio('credits_million_baht','branches')
    if metric=='deposits_per_person': return ratio('deposits_million_baht','population',1000000)
    if metric=='branches_per_100k': return ratio('branches','population',100000)
    if metric=='credit_deposit_ratio': return ratio('credits_million_baht','deposits_million_baht',100)
    if metric=='policy_rate': return max((r['policy_rate_pct'] for r in rows if r['policy_rate_pct'] is not None),default=None)
    raise AssertionError(metric)

def oracle(raw,plan):
    # This does not call the compiler/catalog or reuse its SQL expressions.
    names=set(plan.provinces+([plan.province] if plan.province else []))
    provincial=plan.group_by=='province' or bool(names)
    groups=defaultdict(list)
    for r in raw:
        if names and r['name_th'] not in names: continue
        if plan.exclude_bangkok and r['province_code']==10: continue
        groups[(r['period'],r['province_code'] if provincial else None)].append(r)
    end=plan.end_period or max(r['period'] for r in raw)
    output=[]
    keys=requested_metrics(plan)
    for (period,code),records in groups.items():
        if (plan.group_by=='province' and period!=end) or period>end or (plan.start_period and plan.group_by=='period' and period<plan.start_period): continue
        constraints=[(plan.min_population,sum(r['population'] or 0 for r in records),'>='),
          (plan.min_credits,arithmetic(records,'credits'),'>='),(plan.min_gpp,arithmetic(records,'gpp'),'>='),
          (plan.max_branch_density,arithmetic(records,'branches_per_100k'),'<=')]
        if any(bound is not None and (value is None or (value<bound if sign=='>=' else value>bound)) for bound,value,sign in constraints): continue
        if any(getattr(plan,key) is not None and value==getattr(plan,key) for key,value in [('min_population',sum(r['population'] or 0 for r in records)),('min_credits',arithmetic(records,'credits')),('min_gpp',arithmetic(records,'gpp'))] if key in plan.strict_filters): continue
        row={'period':period.isoformat()}
        if provincial: row.update(province_code=code,name_th=records[0]['name_th'])
        for metric in keys:
            if metric.endswith('_yoy_pct'):
                base=metric[:-8]
                previous=groups.get((period.replace(year=period.year-1),code))
                now=arithmetic(records,base)
                before=arithmetic(previous,base) if previous else None
                row[metric]=100*(now-before)/before if now is not None and before else None
            else: row[metric]=arithmetic(records,metric)
        output.append(row)
    if plan.group_by=='province':
        output=[r for r in output if r[plan.metric] is not None]
        count=len(output)
        output.sort(key=lambda r: ((r[plan.metric] if plan.ascending else -r[plan.metric]),r['province_code']))
        return output[:plan.limit],count
    periods=sorted({r['period'] for r in output})[-plan.limit:]
    return sorted([r for r in output if r['period'] in periods],key=lambda r:(r['period'],r.get('province_code',0))),0

@pytest.mark.parametrize('case',CASES,ids=[f'TH{i+1:02d}' for i in range(len(CASES))])
def test_golden_question(case,raw):
    if case.get('status'):
        with pytest.raises(Clarification) as exc:
            rules_plan(case['q'],case.get('context'))
        assert exc.value.unsupported==(case['status']=='unsupported')
        return
    plan=rules_plan(case['q'],case.get('context'))
    serialized=plan.model_dump(mode='json')
    for key,expected in case['plan'].items():
        assert serialized[key]==expected,(case['q'],serialized)
    result=execute_plan(plan)
    expected,count=oracle(raw,plan)
    assert len(result['rows'])==len(expected)
    assert result['eligible_count']==count
    for actual,wanted in zip(result['rows'],expected):
        assert actual['period']==wanted['period']
        if 'province_code' in wanted: assert actual['province_code']==wanted['province_code']
        for metric in requested_metrics(plan):
            assert actual[metric]==pytest.approx(wanted[metric]) if wanted[metric] is not None else actual[metric] is None

def test_fixture_size():
    assert 60<=len(CASES)<=100
    assert len({c['q'] for c in CASES})==len(CASES)

def test_multiturn_isolation_and_reset(monkeypatch):
    import bank.chat as chat
    monkeypatch.setattr(chat,'_provider',lambda:None)
    session=str(uuid4())
    one=ask('สินเชื่อต่อประชากรสูงสุด 10',session)
    two=ask('ไม่เอากรุงเทพฯ',session)
    three=ask('เอา 5 อันดับ แล้วเทียบกับปีก่อน',session)
    four=ask('ทำกราฟแท่งให้หน่อย',session)
    assert one['result']['eligible_count']==77
    assert two['result']['eligible_count']==76
    assert three['result']['plan']['metric']=='credits_per_person' and len(three['result']['rows'])==5
    assert 'credits_per_person_yoy_pct' in three['result']['rows'][0]
    assert four['result']['chart']['kind']=='bar'
    assert four['result']['period']==one['result']['period']
    new=ask('เงินฝากสูงสุด 3',session)
    assert not new['result']['plan']['exclude_bangkok'] and new['result']['plan']['metric']=='deposits'
    isolated=ask('เอา 5 อันดับ',str(uuid4()))
    assert isolated['mode']=='clarification' and isolated['result'] is None

def test_clarification_cannot_reuse_stale_results(monkeypatch):
    import bank.chat as chat
    monkeypatch.setattr(chat,'_provider',lambda:None)
    session=str(uuid4())
    ask('สินเชื่อสูงสุด 5',session)
    ambiguous=ask('สินเชื่อเทียบกับสาขาและประชากรมากที่สุด',session)
    assert ambiguous['mode']=='clarification' and ambiguous['result'] is None and len(ambiguous['choices'])==3
    resolved=ask('ต่อประชากร',session)
    assert resolved['result']['plan']['metric']=='credits_per_person'
    blocked=ask('NPL',session)
    assert blocked['mode']=='unsupported' and blocked['result'] is None

def test_rank_universe_and_lookup_language():
    result=execute_plan(QueryPlan(metric='credits_per_person',group_by='province',limit=1))
    answer=_answer({'question':'test','result':result})['answer']
    assert '77 จังหวัด' in answer and 'แสดง 1 จังหวัด' in answer and 'อันดับแรกจาก 1' not in answer
    lookup=execute_plan(rules_plan('สินเชื่อต่อประชากรเชียงใหม่'))
    assert 'ไม่ใช่อันดับทั่วประเทศ' in _answer({'question':'test','result':lookup})['answer']

def test_clarification_preserves_explicit_scope(monkeypatch):
    import bank.chat as chat
    monkeypatch.setattr(chat,'_provider',lambda:None)
    session=str(uuid4())
    result=ask('สินเชื่อเทียบกับสาขาและประชากรมากที่สุด ไม่รวมกรุงเทพ กรกฎาคม 2568',session)
    assert result['mode']=='clarification'
    resolved=ask(result['choices'][0],session)
    assert resolved['result']['plan']['metric']=='credits_per_person'
    assert resolved['result']['plan']['exclude_bangkok']
    assert resolved['result']['period']=='2025-07-01'

def test_strict_filters_units_and_unknown_denominators():
    plan=rules_plan('สินเชื่อสูงสุด 5 ประชากรเกิน 1 ล้านคน')
    assert plan.strict_filters==['min_population']
    assert rules_plan('สินเชื่อสูงสุด 5 สินเชื่ออย่างน้อย 1000000 บาท').min_credits==1
    for question in ['สาขาต่อเงินฝากสูงสุด','สินเชื่อต่อผู้อยู่อาศัยสูงสุด']:
        with pytest.raises(Clarification): rules_plan(question)

def test_dates_null_yoy_and_query_bounds():
    early=execute_plan(QueryPlan(metric='credits',group_by='province',end_period=date(2024,7,1),include_yoy=True))
    assert all(r['credits_yoy_pct'] is None for r in early['rows'])
    empty=execute_plan(QueryPlan(metric='credits_yoy_pct',group_by='province',end_period=date(2024,7,1)))
    assert empty['rows']==[]
    with pytest.raises(Clarification): execute_plan(QueryPlan(metric='credits',group_by='province',end_period=date(2030,1,1)))
    with pytest.raises(Clarification): execute_plan(QueryPlan(metric='gpp',group_by='period'))
    with pytest.raises(Clarification): execute_plan(QueryPlan(metric='policy_rate',group_by='period',province='เชียงใหม่'))
    for sql in ['DELETE FROM mart_province_month','SELECT * FROM source_manifest','SELECT * FROM mart_province_month; SELECT 1', 'WITH x AS (DELETE FROM mart_province_month RETURNING *) SELECT * FROM x']:
        with pytest.raises(ValueError): _validate_query(sql)

def test_llm_decision_uses_history_and_rejects_unsupported(monkeypatch):
    import bank.chat as chat
    monkeypatch.setattr(chat,'_provider',lambda:'gemini')
    captured=[]
    def decide(q,context,history):
        captured.append((context,history))
        return PlannerDecision(status='unsupported',message='ไม่มีข้อมูลนี้')
    monkeypatch.setattr(chat,'_llm_decision',decide)
    state={'question':'ช่วยอ่านภาพเศรษฐกิจหน่อย','last_plan':{'metric':'credits','group_by':'province'},'history':[{'role':'user','content':'เดิม'}]}
    result=_plan(state)
    assert captured and captured[0][0]==state['last_plan'] and captured[0][1]==state['history']
    assert result['mode']=='unsupported' and result['plan'] is None
    # A literal unsupported ratio is blocked before calling the model.
    result=_plan({'question':'สินเชื่อต่อ GPP สูงสุด'})
    assert len(captured)==1 and result['mode']=='unsupported'
