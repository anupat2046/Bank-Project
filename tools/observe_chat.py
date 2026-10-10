"""Aggregate allowlisted bank_chat JSON events from stdin; never echo raw logs."""
import json
import math
import statistics
import sys
from collections import Counter

def aggregate_events(lines):
    events=[]
    for line in lines:
        try: event=json.loads(line)
        except (ValueError,TypeError): continue
        if isinstance(event,dict) and event.get('event')=='bank_chat': events.append(event)
    if not events: return {'requests':0}
    timing=sorted(float(e['latency_ms']) for e in events if isinstance(e.get('latency_ms'),(int,float)) and math.isfinite(e['latency_ms']))
    def usage(key):
        values=[e.get(key) for e in events]
        return sum(values) if all(isinstance(v,int) and v>=0 for v in values) else None
    return {'requests':len(events),'statuses':dict(Counter(e.get('status','unknown') for e in events)),
            'error_rate':sum(e.get('status')=='error' for e in events)/len(events),
            'clarification_count':sum(e.get('status')=='clarification' for e in events),
            'latency_p50_ms':statistics.median(timing) if timing else None,
            'latency_p95_ms':timing[max(0,math.ceil(.95*len(timing))-1)] if timing else None,
            'llm_calls':sum(e.get('llm_calls',0) for e in events),'input_tokens':usage('input_tokens'),
            'output_tokens':usage('output_tokens'),'unknown_usage_requests':sum(e.get('total_tokens') is None for e in events),
            'estimated_cost_usd':sum(e['estimated_cost_usd'] for e in events) if all(e.get('estimated_cost_usd') is not None for e in events) else None}

if __name__=='__main__':print(json.dumps(aggregate_events(sys.stdin),indent=2))
