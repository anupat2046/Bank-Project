"""Live routing-only validation on fresh authored phrases; never executes SQL."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter, sleep

from dotenv import load_dotenv
from bank.chat import _provider
from bank.conversation import route_conversation, RoutingOutputError
from bank.llm_runtime import request_budget, ProviderUnavailable
from bank.observability import capture, summarize
from bank.query import QueryPlan

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Explicitly authorize calls to the configured provider')
    parser.add_argument('--delay', type=float, default=10)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, default=ROOT/'tests/fixtures/router_validation.json')
    args = parser.parse_args()
    if not args.live: parser.error('Use --live to call the configured provider')
    if not 0 <= args.delay <= 60: parser.error('--delay must be 0..60 seconds')
    if args.out.exists(): parser.error('Output exists; choose a new path to retain previous results')
    load_dotenv(ROOT/'.env', override=False)
    provider = _provider()
    if not provider: parser.error('No provider configured')
    fixture = args.fixture
    cases = json.loads(fixture.read_text(encoding='utf-8'))
    context = QueryPlan(metric='credits_per_person',group_by='province',limit=5,end_period='2026-07-01').model_dump(mode='json')
    results, blocked = [], None
    for index, case in enumerate(cases):
        if index: sleep(args.delay)
        print(f"Running {index+1}/{len(cases)}: {case['id']}", file=sys.stderr, flush=True)
        failures, decision = [], None
        started = perf_counter()
        with capture() as events, request_budget():
            try:
                decision = route_conversation(case['question'],context if case.get('has_result') else None,
                                              [],bool(case.get('has_result')),provider)
            except ProviderUnavailable as exc:
                blocked = exc.reason
                failures.append('provider')
            except RoutingOutputError:
                failures.append('invalid_output')
        elapsed = (perf_counter()-started)*1000
        if decision:
            if decision.route != case['route']: failures.append('route')
            if decision.chart != case['chart']: failures.append('chart')
        results.append({'id':case['id'],'errors':failures,
                        'route':decision.route if decision else None,'chart':decision.chart if decision else None,
                        'latency_ms':round(elapsed,2),'telemetry':summarize(events,elapsed,'error' if failures else 'ready')})
        if blocked: break
    defaults = {'groq':'openai/gpt-oss-20b','gemini':'gemini-2.5-flash','openai':'gpt-4.1-mini'}
    report = {'measured_at':datetime.now(timezone.utc).isoformat(),'mode':'live direct router; no SQL',
        'dataset':'authored routing validation; not representative or untouched held-out evidence',
        'provider':provider,'model':os.getenv(provider.upper()+'_MODEL',defaults[provider]),
        'delay_seconds':args.delay,'planned':len(cases),'attempted':len(results),
        'passed':sum(not row['errors'] for row in results),'not_run':len(cases)-len(results),
        'blocked_reason':blocked,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'source_sha256_lf':{name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                            for name in ['bank/conversation.py','bank/llm_runtime.py']},'cases':results}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    rendered = json.dumps(report,ensure_ascii=False,indent=2)
    args.out.write_text(rendered+'\n',encoding='utf-8')
    print(rendered)
    return 2 if blocked else 1 if any(row['errors'] for row in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
