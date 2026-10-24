"""Provider selection is testable without sending any model requests."""
import sys
from types import SimpleNamespace
import pytest

from bank.chat import _plan, _provider, PlannerDecision
from bank.query import QueryPlan


@pytest.fixture(autouse=True)
def isolated_provider_config(monkeypatch):
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    monkeypatch.delenv('GROQ_API_KEY', raising=False)


def test_explicit_groq_does_not_use_existing_gemini(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER','groq')
    monkeypatch.setenv('GROQ_API_KEY','test-groq')
    monkeypatch.setenv('GEMINI_API_KEY','test-gemini')
    assert _provider() == 'groq'


def test_missing_selected_key_never_switches_to_paid_provider(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER','groq')
    monkeypatch.setenv('GEMINI_API_KEY','test-gemini')
    assert _provider() is None


def test_none_disables_all_provider_calls(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER','none')
    monkeypatch.setenv('GROQ_API_KEY','test-groq')
    assert _provider() is None


def test_groq_uses_fixed_endpoint_and_bounded_settings(monkeypatch):
    from bank.llm_runtime import build_model
    calls = {}
    monkeypatch.setenv('GROQ_API_KEY','test-groq')
    monkeypatch.setitem(sys.modules,'langchain_openai',SimpleNamespace(ChatOpenAI=lambda **kw:calls.update(kw) or object()))
    build_model('groq')
    assert calls['base_url'] == 'https://api.groq.com/openai/v1'
    assert calls['api_key'] == 'test-groq' and calls['max_retries'] == 0
    assert calls['model'] == 'openai/gpt-oss-20b' and calls['max_tokens'] == 2048


def test_groq_structured_output_keeps_local_validation(monkeypatch):
    from bank.llm_runtime import invoke_structured, _circuits
    calls = {}
    class Model:
        def with_structured_output(self, schema, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(invoke=lambda prompt:{'parsed':PlannerDecision(status='clarification'),'raw':None})
    _circuits.clear()
    output = invoke_structured(Model(), PlannerDecision, 'public test', 'groq', 'planner')
    assert output['parsed'].status == 'clarification'
    assert calls == {'include_raw':True,'method':'json_mode'}


def test_rules_mode_when_no_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert _provider() is None


def test_gemini_is_selected_when_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "another-test-key")
    assert _provider() == "gemini"


def test_openai_remains_optional(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "  ")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert _provider() == "openai"


def test_gemini_builds_validated_plan_without_network(monkeypatch):
    calls = {}

    class FakeGemini:
        def __init__(self, **kwargs):
            calls.update(kwargs)

        def with_structured_output(self, schema, include_raw=False):
            assert schema is PlannerDecision
            assert include_raw
            return SimpleNamespace(invoke=lambda prompt: {'raw':SimpleNamespace(usage_metadata={'input_tokens':100,'output_tokens':20,'total_tokens':120}), 'parsed':PlannerDecision(status="ready", plan=QueryPlan(metric="deposits", group_by="period", intent="trend", limit=25)), 'parsing_error':None})

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "langchain_google_genai", SimpleNamespace(ChatGoogleGenerativeAI=FakeGemini))
    result = _plan({"question": "ช่วยดูยอดที่คนเอามาฝากไว้กับธนาคารตามเวลาหน่อย"})
    assert result["plan"]["metric"] == "deposits"
    assert result["mode"].endswith("(gemini)")
    assert calls["model"] == "gemini-2.5-flash"
    assert calls["api_key"] == "test-key"
