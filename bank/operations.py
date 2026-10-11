"""Best-effort operational metrics. No request bodies, query strings or errors."""
from contextvars import ContextVar
import logging
import os

from sqlalchemy import insert
from .db import engine, operation_metric

live_request = ContextVar('live_operation_request', default=False)
logger = logging.getLogger(__name__)
FIELDS = {'kind', 'route', 'status', 'latency_ms', 'llm_calls',
          'provider_errors', 'total_tokens', 'estimated_cost_usd'}


def enabled():
    return os.getenv('OPERATIONS_METRICS_ENABLED', 'false').lower() == 'true'


def persist(values):
    if not enabled():
        return
    try:
        with engine().begin() as conn:
            conn.execute(insert(operation_metric).values(**{
                key: value for key, value in values.items() if key in FIELDS
            }))
    except Exception:
        # Observability must not replace a successful analytical response with an error.
        logger.warning('Operational metric write failed')


def persist_chat(summary):
    if live_request.get():
        persist(dict(kind='chat', route='/chat', status=summary['status'],
                     latency_ms=summary['latency_ms'], llm_calls=summary['llm_calls'],
                     provider_errors=summary['provider_errors'],
                     total_tokens=summary['total_tokens'],
                     estimated_cost_usd=summary['estimated_cost_usd']))
