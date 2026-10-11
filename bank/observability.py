"""Request-local, allowlisted telemetry: no questions, keys, DSNs or raw errors."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import math
import os
from time import perf_counter
from uuid import uuid4

_events = ContextVar('bank_observation_events', default=None)
logger = logging.getLogger('bank.telemetry')
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

@contextmanager
def capture():
    events = []
    token = _events.set(events)
    try:
        yield events
    finally:
        _events.reset(token)

def record(event, **values):
    events = _events.get()
    if events is not None:
        allowed = {'latency_ms', 'provider', 'input_tokens', 'output_tokens', 'total_tokens',
                   'reasoning_tokens', 'failure_type', 'phase', 'route'}
        events.append({'event': event, **{k:v for k,v in values.items() if k in allowed}})

def token_usage(raw):
    usage = getattr(raw, 'usage_metadata', None) or {}
    def number(key):
        value = usage.get(key)
        return value if isinstance(value, int) and value >= 0 else None
    details = usage.get('output_token_details') or {}
    reasoning = details.get('reasoning')
    return {'input_tokens':number('input_tokens'), 'output_tokens':number('output_tokens'),
            'total_tokens':number('total_tokens'),
            'reasoning_tokens':reasoning if isinstance(reasoning,int) and reasoning >= 0 else None}

def summarize(events, latency_ms, status, strategy='hybrid'):
    calls = [e for e in events if e['event']=='llm']
    def total(key):
        # Unknown usage remains unknown; a rules-only turn is truly zero calls/tokens.
        if not calls: return 0
        values = [e.get(key) for e in calls]
        return sum(values) if all(isinstance(v,int) for v in values) else None
    usage = {key:total(key) for key in ['input_tokens','output_tokens','total_tokens','reasoning_tokens']}
    cost = None
    try:
        input_price = float(os.environ['LLM_INPUT_USD_PER_MILLION'])
        output_price = float(os.environ['LLM_OUTPUT_USD_PER_MILLION'])
        if (all(math.isfinite(v) and v >= 0 for v in [input_price,output_price])
            and usage['input_tokens'] is not None and usage['output_tokens'] is not None):
            cost = (usage['input_tokens']*input_price+usage['output_tokens']*output_price)/1_000_000
    except (KeyError, ValueError):
        pass
    return {'request_id':str(uuid4()),'timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'strategy':strategy,'status':status,'latency_ms':round(latency_ms,2),
            'llm_calls':len(calls),'llm_latency_ms':round(sum(e.get('latency_ms',0) for e in calls),2),
            'provider_errors':sum(bool(e.get('failure_type')) for e in calls),
            **usage,'estimated_cost_usd':cost,'cost_basis':'configured uncached token rates' if cost is not None else 'not configured / usage unavailable',
            'clarification':status=='clarification','error':status=='error',
            'routes':[e['route'] for e in events if e.get('route') in ['capabilities','greeting','analytics','clarification','explanation','presentation','unsupported']],
            'failure_types':[e['failure_type'] for e in events if e.get('failure_type')]}

def emit(summary):
    logger.info(json.dumps({'event':'bank_chat',**summary},ensure_ascii=False))
    from .operations import persist_chat
    persist_chat(summary)
