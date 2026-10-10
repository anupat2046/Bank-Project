"""Conversation-aware semantic planning -> validated SQL -> grounded answer."""
from __future__ import annotations
import os
import atexit
import json
import re
from time import perf_counter
from functools import lru_cache
from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from .db import engine
from .query import Clarification, QueryPlan, METRICS, execute_plan, rules_plan
from .intent import safety_check, normalize, extract_metrics
from .observability import capture, record, token_usage, summarize, emit

ACTIVE_PLANNER_VERSION = 'v3'

class ChatState(TypedDict, total=False):
    question: str
    plan: dict | None
    last_plan: dict | None
    result: dict | None
    answer: str
    error: str | None
    mode: str
    choices: list[str]
    pending_question: str | None
    pending_context: dict | None
    history: list[dict]
    planner_strategy: str
    prompt_version: str

class PlanningOutputError(RuntimeError):
    pass

class PlannerDecision(BaseModel):
    status: Literal['ready','clarification','unsupported']
    plan: QueryPlan | None = None
    message: str = ''
    choices: list[str] = Field(default_factory=list, max_length=3)

def _provider() -> str | None:
    if os.getenv('GEMINI_API_KEY','').strip():
        return 'gemini'
    if os.getenv('OPENAI_API_KEY','').strip():
        return 'openai'
    return None

def _llm_decision(question, context, history, prompt_version=ACTIVE_PLANNER_VERSION):
    provider = _provider()
    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = ChatGoogleGenerativeAI(model=os.getenv('GEMINI_MODEL','gemini-2.5-flash'),api_key=os.environ['GEMINI_API_KEY'],temperature=0,timeout=45,max_retries=int(os.getenv('LLM_MAX_RETRIES','1')))
    else:
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),temperature=0,timeout=45,max_retries=1)
    catalog = {k:{'definition':v[0] or 'YoY vs same month prior year','label':v[1],'unit':v[2]} for k,v in METRICS.items()}
    prompt = ('Map a Thai/English analytical question to a decision, not SQL. Never substitute an unsupported metric with credits. '
      'Ambiguous denominator or ranking across multiple metrics requires clarification. No private customers, individual banks, NPL, forecasts or causal claims. '
      'Loans per registered resident is credits_per_person, not credits. It is NOT personal debt. '
      'Comparison: select up to four exact province names. monthly trends group_by=period, intent=trend, limit=25. '
      'Cross-sectional limit is top N; month stocks cannot be summed across time. Use include_yoy for supplemental prior-year changes; metric=credits_yoy_pct for ranking growth. '
      'Filter credits/GPP in million THB, population in persons. GPP is annual, not a monthly trend. policy_rate must be a national trend alone. '
      'Use confirmed previous plan ONLY for follow-ups; a new self-contained question resets old scope. Dates must be first day of month, convert BE to CE. '
      'Explicit chart preference bar/line/table; auto otherwise. If data or definitions are absent, choose unsupported, do not guess. '
      f'Catalog: {json.dumps(catalog,ensure_ascii=False)}\nConfirmed context: {json.dumps(context,ensure_ascii=False)}\n'
      f'Recent conversation: {json.dumps(history[-8:],ensure_ascii=False)}\nQuestion: {question}')
    if prompt_version in ['v2','v3']:
        prompt += '\n'+IMPROVED_PLANNER_INSTRUCTIONS
    started = perf_counter()
    try:
        output = model.with_structured_output(PlannerDecision,include_raw=True).invoke(prompt)
        raw = output.get('raw')
        record('llm',provider=provider,latency_ms=(perf_counter()-started)*1000,**token_usage(raw))
        if output.get('parsing_error') or output.get('parsed') is None:
            record('failure',failure_type='StructuredOutputError',phase='planner')
            raise PlanningOutputError('Invalid structured planner output')
        decision = output['parsed']
        if prompt_version == 'v3':
            decision = validate_decision(decision)
        return decision

    except Exception as exc:
        if 'output' not in locals():
            record('llm',provider=provider,latency_ms=(perf_counter()-started)*1000,failure_type=type(exc).__name__)
        raise

# Revisions are frozen and compared on a development split before held-out testing.
IMPROVED_PLANNER_INSTRUCTIONS = '''
REVISED CONTRACT (v2):
Return clarification/unsupported messages and selectable questions in Thai for Thai users.
Clarification must name the alternatives, e.g. สินเชื่อต่อประชากร vs สินเชื่อต่อสาขา,
and choices must be complete analytical questions, not just an English metric key.
ยอดออม/เงินออม means deposits; เงินกู้ means credits. Preserve explicit denominators.
For unspecified dates use end_period=null, start_period=null: the SQL compiler selects
the latest available warehouse month, NOT today's date or a guessed month/year.
ย้อนหลัง N เดือน means group_by=period, intent=trend, limit=N and no invented date range.
Keep province names in Thai as written in the question; comparison accepts up to four.
Single province means intent=lookup, multiple provinces means comparison, unless trend.
For supplemental พร้อม YoY use include_yoy=true and retain the primary ratio and all
requested metrics. The compiler computes YoY of EACH eligible requested metric;
never replace a per-person/per-branch ratio's YoY with credits_yoy_pct.
For ranking growth, e.g. สินเชื่อโต YoY สูงสุด, primary is credits_yoy_pct.
Population มากกว่า/เกิน requires strict_filters=[min_population]; อย่างน้อย is inclusive.
No implicit filters: missing thresholds are null; missing exclusion is false for a new question.
For a continuation inherit the confirmed plan including resolved end month, selected provinces,
limit and exclusions. Changing metric with แทน/เปลี่ยนเป็น/แล้วถ้า retains that scope.
For a standalone new question discard old scope. Defaults: province ranking limit=10;
monthly trend limit=25 ONLY if the question does not specify a number or a retained limit.
Do not aggregate annual banking stocks when only a year is given: ask which month.
'''

def validate_decision(decision):
    """Shape invariants only: never repair a metric/date using the golden answer."""
    if decision.status == 'ready':
        if decision.plan is None:
            raise PlanningOutputError('Ready decision requires a plan')
        # A monthly comparison is still a temporal trend, not a cross-sectional ranking.
        if decision.plan.group_by == 'period':
            decision.plan.intent = 'trend'
    elif decision.plan is not None:
        raise PlanningOutputError('Non-ready decision must not contain an executable plan')
    return decision

def _plan(state: ChatState) -> ChatState:
    question = state['question']
    empty = {'plan':None,'result':None,'error':None,'answer':None,'choices':[],'pending_question':None,'pending_context':None}
    context = state.get('last_plan')
    q = normalize(question)
    # A clarification is a conversation event, not a failed SQL execution.
    if state.get('pending_question'):
        context = state.get('pending_context') or context
        if q in ['ต่อประชากร','ประชากร','ต่อคน','ต่อหัว']:
            question = 'เปลี่ยนเป็นสินเชื่อต่อประชากรมากที่สุด'
        elif q in ['ต่อสาขา','สาขา']:
            question = 'เปลี่ยนเป็นสินเชื่อต่อสาขามากที่สุด'
        elif state.get('choices') and question in state['choices']:
            question = 'เปลี่ยนเป็น'+question
        elif q in ['ทั้งสอง','ทั้งคู่']:
            return {**empty,'error':'ต้องการจัดอันดับด้วยสินเชื่อต่อประชากรหรือสินเชื่อต่อสาขาครับ?','mode':'clarification',
              'choices':['สินเชื่อต่อประชากรสูงสุด พร้อมสินเชื่อต่อสาขา','สินเชื่อต่อสาขาสูงสุด พร้อมสินเชื่อต่อประชากร'],'pending_question':state['pending_question'],'pending_context':context}
    try:
        strategy = state.get('planner_strategy','hybrid')
        if strategy == 'llm-only':
            if not _provider():
                raise RuntimeError('No model provider configured')
            decision = _llm_decision(question,context,state.get('history',[]),state.get('prompt_version',ACTIVE_PLANNER_VERSION))
            if decision.status != 'ready' or decision.plan is None:
                raise Clarification(decision.message or 'กรุณาระบุคำถามให้ชัดขึ้น',decision.choices,decision.status=='unsupported')
            return {**empty,'plan':decision.plan.model_dump(mode='json'),'mode':f'LangGraph + LangChain structured LLM ({_provider()})'}
        safety_check(question)
        try:
            plan = rules_plan(question,context,state.get('prompt_version',ACTIVE_PLANNER_VERSION))
            mode = 'LangGraph semantic rules · วางแผนด้วยกฎที่ตรวจสอบได้'
        except Clarification as exc:
            # Known unsupported/ambiguous semantics never reach a forced metric enum.
            if exc.unsupported or exc.choices or extract_metrics(normalize(question)) or strategy == 'rules-only' or not _provider():
                raise
            if state.get('prompt_version'):
                decision = _llm_decision(question,context,state.get('history',[]),state['prompt_version'])
            else:
                decision = _llm_decision(question,context,state.get('history',[]))
            if decision.status != 'ready' or decision.plan is None:
                raise Clarification(decision.message or 'กรุณาระบุคำถามให้ชัดขึ้น',decision.choices,decision.status=='unsupported')
            plan = decision.plan
            mode = f'LangGraph + LangChain structured LLM ({_provider()})'
        return {**empty,'plan':plan.model_dump(mode='json'),'mode':mode}
    except Clarification as exc:
        pending_context = context
        if exc.choices:
            neutral = re.sub(r'สินเชื่อ\s*(?:เทียบกับ|ต่อ)\s*(?:สาขา\s*(?:และ|กับ)\s*ประชากร|ประชากร\s*(?:และ|กับ)\s*สาขา)','สินเชื่อ',normalize(state['question']))
            try:
                pending_context = rules_plan(neutral,context,state.get('prompt_version',ACTIVE_PLANNER_VERSION)).model_dump(mode='json')
            except (Clarification,ValueError):
                pass
        return {**empty,'error':str(exc),'mode':'unsupported' if exc.unsupported else 'clarification',
          'choices':exc.choices,'pending_question':None if exc.unsupported else state['question'],'pending_context':pending_context}
    except ValueError:
        return {**empty,'error':'แผนคำถามไม่ผ่านการตรวจสอบ กรุณาระบุตัวชี้วัดและช่วงเวลาใหม่','mode':'clarification'}
    except Exception as exc:
        record('failure',failure_type=type(exc).__name__,phase='planner')
        return {**empty,'error':'ผู้ให้บริการ AI ไม่พร้อมใช้งาน กรุณาลองใหม่ภายหลัง','mode':'error'}

def _route(state):
    return 'error' if state.get('error') else 'execute'

def _execute(state):
    try:
        result = execute_plan(QueryPlan.model_validate(state['plan']))
        # Pin resolved end month in memory, rather than letting later refreshes move it.
        confirmed = {**state['plan'],'end_period':result['period']}
        return {'result':result,'last_plan':confirmed}
    except (Clarification,ValueError) as exc:
        return {'result':None,'error':str(exc),'mode':'clarification','choices':[]}
    except Exception:
        record('failure',failure_type='WarehouseUnavailable',phase='execute')
        return {'result':None,'error':'ไม่สามารถอ่านผลจากคลังข้อมูลได้ กรุณาลองใหม่','mode':'error','choices':[]}

def _answer(state):
    result = state.get('result')
    if result is None:
        answer = state.get('error') or 'ไม่สามารถตอบได้'
    elif not result['rows']:
        answer = 'ไม่มีข้อมูลที่คำนวณตัวชี้วัดได้ตามงวดและเงื่อนไขนี้ (รวมกรณีไม่มีฐาน YoY); ไม่ใช้ค่าศูนย์หรือผลเก่าแทน'
    else:
        rows,plan = result['rows'],result['plan']
        first = rows[-1] if plan['group_by']=='period' else rows[0]
        value=first['value']
        rendered=f'{value:,.2f}' if value is not None else 'ไม่มีค่า'
        prefix=f"{result['metric_label']}: {first.get('name_th') or first['period']} {rendered} {result['unit']}"
        if plan['group_by']=='period':
            latest=[r for r in rows if r['period']==rows[-1]['period']]
            values=' / '.join(f"{r.get('name_th') or 'รวมประเทศ'} {r['value']:,.2f} {result['unit']}" if r['value'] is not None else f"{r.get('name_th') or 'รวมประเทศ'} ไม่มีค่า" for r in latest)
            answer=f"{result['metric_label']} ล่าสุด {values} · งวด {result['period']} · แสดง {len({r['period'] for r in rows})} เดือน"
        elif plan['intent']=='ranking' and not plan.get('province') and not plan.get('provinces'):
            direction='ต่ำสุด' if plan['ascending'] else 'สูงสุด'
            answer=prefix+f" · {direction}ใน {result['eligible_count']} จังหวัดที่มีข้อมูลและเข้าเกณฑ์ · แสดง {len(rows)} จังหวัด · งวด {result['period']}"
        else:
            values=' / '.join(f"{r['name_th']} {r['value']:,.2f} {result['unit']}" for r in rows[:4])
            answer=f"{result['metric_label']}: {values} · ผลเฉพาะ {len(rows)} จังหวัดที่เลือก ไม่ใช่อันดับทั่วประเทศ · งวด {result['period']}"
        if len(result['metrics'])>1:
            answer += ' · มี '+ ' / '.join(m['label'] for m in result['metrics'][1:])+' ในตาราง'
    history = [*state.get('history',[]),{'role':'user','content':state['question']},{'role':'assistant','content':answer}][-20:]
    return {'answer':answer,'history':history}

@lru_cache(maxsize=1)
def graph():
    builder=StateGraph(ChatState)
    builder.add_node('plan',_plan); builder.add_node('execute',_execute); builder.add_node('answer',_answer)
    builder.add_edge(START,'plan')
    builder.add_conditional_edges('plan',_route,{'error':'answer','execute':'execute'})
    builder.add_edge('execute','answer'); builder.add_edge('answer',END)
    dsn=engine().url.render_as_string(hide_password=False).replace('postgresql+psycopg://','postgresql://')
    manager=PostgresSaver.from_conn_string(dsn)
    saver=manager.__enter__(); saver.setup()
    atexit.register(lambda: manager.__exit__(None,None,None))
    return builder.compile(checkpointer=saver)

def ask(question: str,session_id: str='default') -> dict[str,Any]:
    started = perf_counter()
    with capture() as events:
        try:
            state=graph().invoke({'question':question},config={'configurable':{'thread_id':session_id}})
            reply = {k:state.get(k) for k in ('answer','result','error','mode','choices')}
            status = state['mode'] if state['mode'] in ['clarification','unsupported','error'] else 'ready'
            emit(summarize(events,(perf_counter()-started)*1000,status))
            return reply
        except Exception:
            record('failure',failure_type='GraphUnavailable',phase='graph')
            emit(summarize(events,(perf_counter()-started)*1000,'error'))
            raise
