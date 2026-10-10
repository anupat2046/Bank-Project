"""Explicit, bounded benchmark. --live incurs configured provider requests."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
from sqlalchemy import text
from dotenv import load_dotenv
from bank.db import read_engine
from bank.query import Clarification, execute_plan, rules_plan
from bank.chat import _llm_decision, _provider

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Call the configured LLM for each selected question; quota/cost applies')
    parser.add_argument('--limit',type=int,default=80)
    args=parser.parse_args()
    if not 1<=args.limit<=80: parser.error('limit must be 1..80')
    root=Path(__file__).resolve().parents[1]
    if args.live:
        load_dotenv(root/'.env',override=False)
        if not _provider(): parser.error('No configured model key; never pass keys on the command line')
    spec=importlib.util.spec_from_file_location('golden_oracle',root/'tests/test_chat_analytics.py')
    oracle_module=importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle_module)
    cases=json.loads((root/'tests/fixtures/chat_cases.json').read_text(encoding='utf-8'))[:args.limit]
    with read_engine().connect() as conn:
        raw=[dict(r) for r in conn.execute(text('SELECT * FROM mart_province_month ORDER BY period,province_code')).mappings()]
    results=[]
    for i,case in enumerate(cases,1):
        row={'id':f'TH{i:02d}','question':case['q'],'status_correct':False,'plan_correct':False,'result_correct':False}
        try:
            if args.live:
                decision=_llm_decision(case['q'],case.get('context'),[])
                status=decision.status; plan=decision.plan
            else:
                try: plan=rules_plan(case['q'],case.get('context')); status='ready'
                except Clarification as exc: plan=None; status='unsupported' if exc.unsupported else 'clarification'
            expected_status=case.get('status','ready')
            row['status_correct']=status==expected_status
            if expected_status!='ready':
                row['plan_correct']=row['result_correct']=row['status_correct'] and plan is None
            elif plan is not None and status=='ready':
                serialized=plan.model_dump(mode='json')
                row['plan_correct']=all(serialized[k]==v for k,v in case['plan'].items())
                # Reject semantic mismatch rather than credit a valid but irrelevant SQL query.
                if row['plan_correct']:
                    actual=execute_plan(plan)
                    expected,count=oracle_module.oracle(raw,plan)
                    matched=len(expected)==len(actual['rows']) and actual['eligible_count']==count
                    for got,wanted in zip(actual['rows'],expected):
                        matched=matched and got['period']==wanted['period'] and got.get('province_code')==wanted.get('province_code')
                        for key in oracle_module.requested_metrics(plan):
                            a,b=got[key],wanted[key]
                            matched=matched and (a is None and b is None or a is not None and b is not None and abs(float(a)-float(b))<=max(1e-6,abs(float(b))*1e-6))
                    row['result_correct']=bool(matched)
        except Exception as exc:
            # Never print provider error strings which may include sensitive request data.
            row['failure_type']=type(exc).__name__
        results.append(row)
    summary={'mode':'live LLM' if args.live else 'deterministic semantic planner','questions':len(results),
      'status_correct':sum(r['status_correct'] for r in results),'plan_correct':sum(r['plan_correct'] for r in results),
      'result_correct':sum(r['result_correct'] for r in results),'cases':results}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if summary['result_correct']==len(results) else 1

if __name__=='__main__':
    raise SystemExit(main())
