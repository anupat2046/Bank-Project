"""60-turn regression through HTTP, real warehouse arithmetic, router and context.

Offline uses an in-process HTTP API with in-memory checkpoints, never a model.
Live targets the running API; --max-requests bounds spend, and provider failure
stops the run. This authored regression set is NOT an untouched held-out split.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import importlib.util
import json
import logging
import sys
from time import perf_counter, sleep
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
from sqlalchemy import text
from bank.query import QueryPlan, requested_metrics
from bank.db import read_engine

ROOT = Path(__file__).resolve().parents[1]


def cases():
    scenarios = json.loads((ROOT/'tests/fixtures/conversation_regression.json').read_text(encoding='utf-8'))
    output = []
    for i, scenario in enumerate(scenarios):
        expected = scenario.get('status', 'ready')
        output.append({**scenario,'session':i,'id':f'C{i+1:02d}-1','route':scenario.get('route','analytics')})
        followups = {
            0: ('เอา 3 อันดับ', {**scenario.get('plan', {}),'limit':3}),
            1: ('เปลี่ยนเป็นสินเชื่อต่อประชากรแทน', {**scenario.get('plan', {}),'metric':'credits_per_person'}),
            3: ('เปลี่ยนเป็นเงินฝากต่อประชากรแทน', {**scenario.get('plan', {}),'metric':'deposits_per_person'}),
            4: ('เปลี่ยนเป็นสินเชื่อต่อสาขาแทน', {**scenario.get('plan', {}),'metric':'credits_per_branch'}),
            16: ('กรกฎาคม 2568', {'metric':'credits','end_period':'2025-07-01'}),
            17: ('ต่อประชากร', {'metric':'credits_per_person'}),
        }
        final_plan = scenario.get('plan')
        if i in followups:
            question, final_plan = followups[i]
            output.append({'question':question,'plan':final_plan,'route':'analytics','session':i,'id':f'C{i+1:02d}-2'})
            expected = 'ready'
        else:
            explain = expected == 'ready' and i % 2 == 0
            output.append({'question':'อธิบายผลล่าสุด' if explain else 'แล้วช่วยอะไรได้บ้าง', 'status':'ready',
                           'route':'explanation' if explain else 'capabilities', 'session':i,'id':f'C{i+1:02d}-2'})
        output.append({'question':'เปลี่ยนเป็นตาราง','status':'ready' if expected=='ready' else 'clarification',
            'route':'presentation', 'plan':final_plan,'session':i,'id':f'C{i+1:02d}-3'})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--max-requests', type=int, default=6)
    parser.add_argument('--scenario', type=int, choices=range(1,21), help='Run one authored three-turn scenario; omitted means the full corpus')
    parser.add_argument('--delay', type=float, default=0, help='Seconds between HTTP turns (0..60); does not assert a provider quota')
    parser.add_argument('--progress', action='store_true', help='Print case IDs and progress to stderr without questions or replies')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_requests <= 60: parser.error('--max-requests must be 1..60')
    if not 0 <= args.delay <= 60: parser.error('--delay must be 0..60 seconds')
    spec = importlib.util.spec_from_file_location('independent_arithmetic', ROOT/'tests/test_chat_analytics.py')
    arithmetic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arithmetic)
    with read_engine().connect() as conn:
        raw = [dict(row) for row in conn.execute(text('SELECT * FROM mart_province_month ORDER BY period,province_code')).mappings()]
    as_of = max(row['period'] for row in raw).isoformat()
    results = []
    prefix = 'eval-'+str(uuid4())
    all_cases = cases()
    if args.scenario:
        all_cases = [case for case in all_cases if case['id'].startswith(f'C{args.scenario:02d}-')]
    logging.getLogger('bank.telemetry').disabled = True
    with ExitStack() as stack:
        if args.live:
            client = stack.enter_context(httpx.Client(base_url=args.base_url,timeout=60))
        else:
            from fastapi.testclient import TestClient
            from langgraph.checkpoint.memory import InMemorySaver
            from bank import chat, api
            graph = chat.build_graph(InMemorySaver())
            stack.enter_context(patch.object(chat, 'graph', lambda:graph))
            stack.enter_context(patch.object(chat, '_provider', lambda:None))
            stack.enter_context(patch('bank.operations.enabled', lambda:False))
            client = stack.enter_context(TestClient(api.app))
        blocked = None
        for index, case in enumerate(all_cases[:args.max_requests]):
            if index and args.delay:
                sleep(args.delay)
            if args.progress:
                print(f"Running {index+1}/{args.max_requests}: {case['id']}", file=sys.stderr, flush=True)
            failures = []
            started = perf_counter()
            try:
                response = client.post('/chat',json={'question':case['question'],'session_id':prefix+'-'+str(case['session'])})
            except httpx.HTTPError as exc:
                blocked = 'api_transport_failure'
                results.append({'id':case['id'],'errors':['transport'], 'failure_type':type(exc).__name__})
                break
            elapsed = round((perf_counter()-started)*1000, 2)
            if response.status_code != 200:
                results.append({'id':case['id'],'errors':['http'],'http_status':response.status_code})
                continue
            reply = response.json()
            health = reply.get('provider_status',{})
            if args.live and (health.get('last_failure') or health.get('provider') is None):
                blocked = health.get('last_failure') or 'provider_not_configured'
                results.append({'id':case['id'],'errors':['provider'],'provider_failure':blocked,
                    'latency_ms':elapsed,'telemetry':reply.get('telemetry')})
                break
            status = reply['mode'] if reply['mode'] in ['clarification','unsupported','error'] else 'ready'
            if status != case.get('status','ready'): failures.append('status')
            if reply.get('conversation_route') != case['route']: failures.append('route')
            result = reply.get('result')
            if case.get('plan') and status == 'ready':
                if not result:
                    failures.append('missing_result')
                else:
                    expected = QueryPlan.model_validate({'group_by':'province',**case['plan']})
                    actual = result['plan']
                    for key, value in expected.model_dump(mode='json').items():
                        got_value = actual.get(key)
                        if key == 'metrics':
                            if not set(requested_metrics(expected)).issubset(requested_metrics(QueryPlan.model_validate(actual))):
                                failures.append('plan:metrics')
                            continue
                        if key == 'end_period':
                            got_value, value = got_value or as_of, value or as_of
                        if key == 'chart' and case['route'] == 'presentation':
                            value = 'table'
                        if (set(got_value or []) != set(value) if key in ['provinces','strict_filters'] else got_value != value):
                            failures.append('plan:'+key)
                    wanted, count = arithmetic.oracle(raw, expected)
                    number_match = len(wanted)==len(result['rows']) and count==result['eligible_count']
                    for got, row in zip(result['rows'], wanted):
                        number_match &= got['period']==row['period'] and got.get('province_code')==row.get('province_code')
                        for key in requested_metrics(expected):
                            a,b = got.get(key),row[key]
                            number_match &= (a is None and b is None) or (a is not None and b is not None and abs(float(a)-float(b))<=max(1e-6,abs(float(b))*1e-6))
                    if not number_match: failures.append('numbers')
                    if case['route']=='presentation' and result['chart']['kind']!='table': failures.append('chart')
            elif result is not None:
                failures.append('unexpected_result')
            results.append({'id':case['id'],'errors':failures,'route':reply.get('conversation_route'),'status':status,
                            'latency_ms':elapsed,'telemetry':reply.get('telemetry')})
    report = {'measured_at':datetime.now(timezone.utc).isoformat(),'mode':'live HTTP' if args.live else 'offline in-process HTTP',
        'dataset':'authored conversation regression; not held-out','scenario':args.scenario,'as_of':as_of,'planned':len(all_cases),
        'attempted':len(results),'not_run':len(all_cases)-len(results),'passed':sum(not row['errors'] for row in results),
        'delay_seconds':args.delay,
        'blocked_reason':blocked,'live_evaluation_complete':args.live and blocked is None and len(results)==len(all_cases),
        'live_all_checks_passed':args.live and blocked is None and len(results)==len(all_cases) and all(not row['errors'] for row in results),
        'cases':results}
    rendered = json.dumps(report,ensure_ascii=False,indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(rendered+'\n',encoding='utf-8')
    print(rendered)
    return 2 if blocked else 1 if any(row['errors'] for row in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
