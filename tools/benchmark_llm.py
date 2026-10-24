"""Explicit live comparison, resumable per trial; public authored fixtures only."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
import platform
from importlib.metadata import version as package_version
from pathlib import Path
import statistics
import time
from dotenv import load_dotenv
from sqlalchemy import text
from bank import chat
from bank.db import read_engine
from bank.query import QueryPlan, requested_metrics, _provinces, Clarification
from bank.observability import capture, summarize

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['metric','group_by','intent','limit','ascending','exclude_bangkok','start_period','end_period',
          'min_population','min_credits','min_gpp','max_branch_density','strict_filters']
TAXONOMY = {'metric':'metric','group_by':'aggregation','intent':'intent','limit':'limit',
 'ascending':'ordering','exclude_bangkok':'province','start_period':'period','end_period':'period',
 'min_population':'filter','min_credits':'filter','min_gpp':'filter','max_branch_density':'filter','strict_filters':'filter'}

def expected_plan(case, as_of):
    data = {'group_by':'province', **case['expected']}
    data.setdefault('end_period',as_of)
    return QueryPlan.model_validate(data)

def differences(actual, expected, as_of):
    a,b = actual.model_dump(mode='json'),expected.model_dump(mode='json')
    a['end_period'] = a['end_period'] or as_of
    b['end_period'] = b['end_period'] or as_of
    errors = {TAXONOMY.get(k,k) for k in FIELDS if a[k]!=b[k]}
    province_codes={str(name).lower():p['province_code'] for p in _provinces() for name in [p['name_th'],p['name_en']]}
    def names(p): return {province_codes.get(name.lower(),name.lower()) for name in [*p.provinces,*([p.province] if p.province else [])]}
    if names(actual)!=names(expected): errors.add('province')
    # Additional display metrics are allowed, but requested ones must be present.
    if not set(requested_metrics(expected)).issubset(requested_metrics(actual)): errors.add('metrics')
    expected_chart = expected.chart if expected.chart!='auto' else ('line' if expected.group_by=='period' else 'bar')
    actual_chart = actual.chart if actual.chart!='auto' else ('line' if actual.group_by=='period' else 'bar')
    if expected_chart!=actual_chart: errors.add('chart')
    return sorted(errors)

def numeric_match(result, wanted, count, expected):
    if result is None or len(result['rows'])!=len(wanted) or result['eligible_count']!=count: return False
    for a,b in zip(result['rows'],wanted):
        if a['period']!=b['period'] or a.get('province_code')!=b.get('province_code'): return False
        for metric in requested_metrics(expected):
            x,y=a.get(metric),b[metric]
            if y is None:
                if x is not None: return False
            elif x is None or not math.isclose(float(x),float(y),rel_tol=1e-6,abs_tol=1e-6): return False
    return True

def trial(case, state, strategy, version, raw, as_of, oracle):
    started=time.perf_counter()
    state={**state,'question':case['q'],'planner_strategy':strategy,'prompt_version':version}
    with capture() as events:
        state.update(chat._plan(state))
        if not state.get('error'): state.update(chat._execute(state))
        state.update(chat._answer(state))
        status=state['mode'] if state['mode'] in ['clarification','unsupported','error'] else 'ready'
        telemetry=summarize(events,(time.perf_counter()-started)*1000,status,strategy)
    expected_status=case.get('status','ready')
    status_ok=status==expected_status
    errors=[]
    plan_ok=None
    numbers_ok=None
    clarification_ok=None
    if expected_status=='ready':
        target=expected_plan(case,as_of)
        if state.get('plan'):
            errors=differences(QueryPlan.model_validate(state['plan']),target,as_of)
        else: errors=['missing_plan']
        plan_ok=status_ok and not errors
        wanted,count=oracle(raw,target)
        numbers_ok=status_ok and numeric_match(state.get('result'),wanted,count,target)
        if status_ok and not numbers_ok: errors.append('result')
    elif expected_status=='clarification':
        content=' '.join([state.get('answer') or '',*state.get('choices',[])])
        clarification_ok=status_ok and bool(content.strip()) and state.get('result') is None and all(
            any(term in content for term in alternatives) for alternatives in case.get('clarification_terms',[]))
        if not clarification_ok: errors.append('clarification')
    if not status_ok: errors.append('provider_error' if status=='error' else 'status')
    if case.get('dialogue') and any(e in errors for e in ['metric','province','period','missing_plan']): errors.append('context')
    passed=status_ok and (plan_ok and numbers_ok if expected_status=='ready' else clarification_ok if expected_status=='clarification' else state.get('result') is None)
    result=state.get('result')
    row={'id':case['id'],'split':case['split'],'dialogue':case.get('dialogue'),'question':case['q'],
         'strategy':strategy,'prompt_version':version,'expected_status':expected_status,'status':status,
         'status_correct':status_ok,'plan_correct':plan_ok,'numbers_correct':numbers_ok,
         'clarification_correct':clarification_ok,'passed':bool(passed),'error_categories':sorted(set(errors)),
         'expected_plan':expected_plan(case,as_of).model_dump(mode='json') if expected_status=='ready' else None,
         'actual_plan':state.get('plan'),'message':state.get('answer'),'choices':state.get('choices',[]),
         'row_count':len(result['rows']) if result else None,'first_row':result['rows'][0] if result and result['rows'] else None,
         'telemetry':telemetry}
    return row,state

def aggregate(rows):
    grouped={}
    for strategy in sorted({r['strategy'] for r in rows}):
        group=[r for r in rows if r['strategy']==strategy]
        timings=sorted(r['telemetry']['latency_ms'] for r in group)
        def score(field):
            values=[r[field] for r in group if r[field] is not None]
            return {'correct':sum(values),'total':len(values)}
        calls=[r['telemetry'] for r in group if r['telemetry']['llm_calls']]
        def tokens(key):
            return sum(t[key] for t in calls) if all(t[key] is not None for t in calls) else None
        costs=[t['estimated_cost_usd'] for t in calls]
        grouped[strategy]={'passed':sum(r['passed'] for r in group),'total':len(group),
          'status':score('status_correct'),'plan':score('plan_correct'),'numbers':score('numbers_correct'),'clarification':score('clarification_correct'),
          'latency_p50_ms':statistics.median(timings),'latency_p95_ms':timings[max(0,math.ceil(.95*len(timings))-1)],
          'errors':sum(r['status']=='error' for r in group),'error_rate':sum(r['status']=='error' for r in group)/len(group),
          'clarification_count':sum(r['status']=='clarification' for r in group),
          'llm_calls':sum(t['llm_calls'] for t in calls),'input_tokens':tokens('input_tokens'),'output_tokens':tokens('output_tokens'),
          'usage_reported_calls':sum(t['total_tokens'] is not None for t in calls),
          'estimated_cost_usd':sum(costs) if all(c is not None for c in costs) else None,
          'failure_categories':dict(Counter(e for r in group for e in r['error_categories']))}
    return grouped

def may_use_llm(strategy, case, state, version):
    """Pacing preview only; it does not supply a plan or context to the trial."""
    if strategy=='llm-only': return True
    if strategy=='rules-only': return False
    try:
        chat.rules_plan(case['q'],state.get('last_plan'),version)
        return False
    except Clarification as exc:
        return not (exc.unsupported or exc.choices or chat.extract_metrics(chat.normalize(case['q'])))
    except ValueError:
        return False

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--split',choices=['dev','heldout'],default='dev')
    parser.add_argument('--version',choices=['v1','v2','v3','v4'],default='v1')
    parser.add_argument('--output',required=True,help='JSON artifact path relative to project root')
    parser.add_argument('--delay',type=float,default=6,help='Seconds between turns (0..60); does not assert a provider quota')
    parser.add_argument('--max-live-calls',type=int,default=40)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--retry-setup-failures',action='store_true',help='Only retry zero-request missing-SDK failures; preserve original setup evidence')
    args=parser.parse_args()
    if not 0<=args.delay<=60 or not 1<=args.max_live_calls<=80: parser.error('Invalid bounded delay/call budget')
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/'docs/evidence') and not output.is_relative_to(ROOT/'data'):
        parser.error('Reports must be under docs/evidence or private data')
    if output.exists() and not args.resume: parser.error('Output exists: choose another path or --resume')
    load_dotenv(ROOT/'.env',override=False)
    provider = chat._provider() if args.live else None
    if args.live and provider not in {'gemini','groq','openai'}: parser.error('Live comparison requires a configured provider; never pass a key on CLI')
    if args.live and provider == 'gemini':
        import langchain_google_genai # Fail preflight before producing measured model trials.
    if not args.live: chat._provider=lambda:None
    fixture=ROOT/'tests/fixtures/llm_eval_cases.json'
    corpus=json.loads(fixture.read_text(encoding='utf-8'))
    cases=[c for c in corpus['cases'] if c['split']==args.split]
    strategies=['rules-only','llm-only','hybrid'] if args.live else ['rules-only']
    spec=importlib.util.spec_from_file_location('numeric_oracle',ROOT/'tests/test_chat_analytics.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with read_engine().connect() as conn:
        raw=[dict(r) for r in conn.execute(text('SELECT * FROM mart_province_month ORDER BY period,province_code')).mappings()]
    as_of=max(r['period'] for r in raw).isoformat()
    fingerprint=hashlib.sha256(json.dumps(raw,default=str,sort_keys=True).encode()).hexdigest()
    defaults = {'groq':'openai/gpt-oss-20b','gemini':'gemini-2.5-flash','openai':'gpt-4.1-mini'}
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'live':args.live,'provider':provider,
            'model':os.getenv(provider.upper()+'_MODEL',defaults[provider]) if provider else None,'prompt_version':args.version,
            'split':args.split,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
            'warehouse_sha256':fingerprint,'as_of':as_of,'warehouse_rows':len(raw),
            'request_budget':args.max_live_calls,'delay_seconds':args.delay,'rows':[],
            'runtime':{'python':platform.python_version(),'langchain_google_genai':package_version('langchain-google-genai') if args.live else None},
            'rubric':'full scope + required metrics; canonical province codes; independent arithmetic; Thai clarification term rubric',
            'clarification_rubric_is_heuristic':True,
            'code_sha256':hashlib.sha256(b''.join((ROOT/p).read_bytes() for p in ['bank/chat.py','bank/intent.py','bank/query.py','bank/observability.py','tools/benchmark_llm.py'])).hexdigest()}
    if args.resume:
        old=json.loads(output.read_text(encoding='utf-8'))
        for field in ['live','model','prompt_version','split','fixture_sha256','warehouse_sha256']:
            if old[field]!=report[field]: parser.error(f'Resume mismatch: {field}')
        report=old
        if args.retry_setup_failures:
            failed=[r for r in report['rows'] if r['status']=='error' and r['telemetry']['llm_calls']==0
                    and 'ModuleNotFoundError' in r['telemetry']['failure_types']]
            report.setdefault('setup_failures',[]).extend(failed)
            report['rows']=[r for r in report['rows'] if r not in failed]
    output.parent.mkdir(parents=True,exist_ok=True)
    def save():
        report['summary']=aggregate(report['rows'])
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    calls=sum(r['telemetry']['llm_calls'] for r in report['rows'])
    error_streak=0
    for strategy in strategies:
        states={}
        for case in cases:
            saved=next((r for r in report['rows'] if r['strategy']==strategy and r['id']==case['id']),None)
            key=case.get('dialogue',case['id'])
            state=states.get(key,{})
            if saved:
                # Reconstruct predicted confirmed context, not golden context, without re-requesting.
                if saved['status']=='ready' and saved['actual_plan']:
                    state['last_plan']={**saved['actual_plan'],'end_period':saved['actual_plan'].get('end_period') or as_of}
                state['history']=[*state.get('history',[]),{'role':'user','content':case['q']},{'role':'assistant','content':saved['message']}][-20:]
                states[key]=state
                continue
            if strategy!='rules-only' and (calls>=args.max_live_calls or error_streak>=3):
                report['stop_reason']='Live call budget reached' if calls>=args.max_live_calls else 'Three consecutive provider/system failures'
                save();print(report['stop_reason'],flush=True);return 2
            if may_use_llm(strategy,case,state,args.version):time.sleep(args.delay)
            row,state=trial(case,state,strategy,args.version,raw,as_of,module.oracle)
            states[key]=state
            calls+=row['telemetry']['llm_calls']
            error_streak=error_streak+1 if row['status']=='error' else 0
            report['rows'].append(row);save()
            print(f"{strategy} {case['id']} {row['status']} pass={row['passed']} errors={row['error_categories']} calls={calls}",flush=True)
    report.pop('stop_reason',None)
    report['completed_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2),flush=True)
    return 0 # A measured model failure is a valid benchmark result, not a harness failure.

if __name__=='__main__':raise SystemExit(main())
