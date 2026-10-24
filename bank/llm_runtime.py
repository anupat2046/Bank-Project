"""Bounded provider calls and process-local circuit breakers; never expose raw errors."""
from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
import os
import json
from threading import Lock
from time import monotonic, perf_counter

from .observability import record, token_usage

_request = ContextVar('llm_request_budget', default=None)
_circuits = {}
_lock = Lock()


class ProviderUnavailable(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def classify_failure(exc):
    # Inspect in memory only. Never return/log exception text or request URLs.
    value = str(exc).lower()
    if any(s in value for s in ['resource_exhausted', 'quota', '429']):
        return 'quota_exhausted'
    if any(s in value for s in ['api_key_invalid', 'api key expired', 'permission_denied', 'unauthenticated', '401', '403']):
        return 'authentication_failed'
    if any(s in value for s in ['not_found', '404']):
        return 'model_unavailable'
    if isinstance(exc, TimeoutError) or 'timeout' in value or 'timed out' in value:
        return 'provider_timeout'
    return 'provider_failure'


def _identity(provider):
    prefix = {'gemini':'GEMINI','groq':'GROQ','openai':'OPENAI'}.get(provider,'UNCONFIGURED')
    # A rotated key/model gets a new circuit, without storing or publishing the key.
    digest = sha256(os.getenv(prefix+'_API_KEY', '').encode()).digest()
    return provider, os.getenv(prefix+'_MODEL', ''), digest


def provider_health(provider):
    with _lock:
        entry = _circuits.get(_identity(provider), {})
        remaining = max(0, entry.get('until', 0)-monotonic())
        return {'provider': provider, 'circuit_open': remaining > 0,
                'retry_after_seconds': int(remaining)+1 if remaining else 0,
                'last_failure': entry.get('reason'),
                'scope': 'current API process; configuration is not a successful health probe'}


@contextmanager
def request_budget():
    token = _request.set({'deadline': monotonic()+45, 'calls': 0})
    try:
        yield
    finally:
        _request.reset(token)


def build_model(provider):
    budget = _request.get()
    remaining = budget['deadline']-monotonic() if budget else 12
    if remaining <= 0:
        raise ProviderUnavailable('request_budget_exhausted')
    kwargs = dict(temperature=0, timeout=min(12, remaining), max_retries=0)
    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            api_key=os.environ['GEMINI_API_KEY'], **kwargs)
    from langchain_openai import ChatOpenAI
    if provider == 'groq':
        return ChatOpenAI(model=os.getenv('GROQ_MODEL','openai/gpt-oss-20b'),
            api_key=os.environ['GROQ_API_KEY'], base_url='https://api.groq.com/openai/v1',
            max_tokens=2048, reasoning_effort='low', **kwargs)
    return ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'), **kwargs)


def invoke_structured(model, schema, prompt, provider, phase):
    health = provider_health(provider)
    if health['circuit_open']:
        record('failure', phase=phase, failure_type='circuit_open')
        raise ProviderUnavailable(health['last_failure'])
    budget = _request.get()
    if budget and (budget['calls'] >= 3 or monotonic() >= budget['deadline']):
        record('failure', phase=phase, failure_type='request_budget_exhausted')
        raise ProviderUnavailable('request_budget_exhausted')
    if budget:
        budget['calls'] += 1
    started = perf_counter()
    try:
        # The current nested optional plan failed Groq's server schema validation
        # in live checks. JSON mode is explicit compatibility, never a relaxation
        # of local Pydantic/semantic validation or permission to execute raw SQL.
        options = {'method':'json_mode'} if provider == 'groq' else {}
        if provider == 'groq':
            prompt += ('\nReturn one JSON object matching this schema. Omit unused optional fields '
                       'rather than filling them with null. Array fields must be arrays, never null. '
                       'For non-ready decisions plan=null; for ready decisions return a plan object.\n'
                       +json.dumps(schema.model_json_schema(), ensure_ascii=False))
        output = model.with_structured_output(schema, include_raw=True, **options).invoke(prompt)
    except Exception as exc:
        reason = classify_failure(exc)
        with _lock:
            # One failure opens the circuit, avoiding quota storms and repeated waits.
            cooldown = 300 if reason == 'quota_exhausted' else 600 if reason in ['authentication_failed', 'model_unavailable'] else 30
            _circuits[_identity(provider)] = {'until': monotonic()+cooldown, 'reason': reason}
        record('llm', provider=provider, phase=phase,
               latency_ms=(perf_counter()-started)*1000, failure_type=reason)
        raise ProviderUnavailable(reason) from None
    with _lock:
        _circuits.pop(_identity(provider), None)
    record('llm', provider=provider, phase=phase,
           latency_ms=(perf_counter()-started)*1000, **token_usage(output.get('raw')))
    return output
