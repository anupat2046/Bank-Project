"""Provider selection is testable without sending any model requests."""
import sys
from types import SimpleNamespace

from bank.chat import _plan, _provider
from bank.query import QueryPlan


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

        def with_structured_output(self, schema):
            assert schema is QueryPlan
            return SimpleNamespace(invoke=lambda prompt: QueryPlan(metric="deposits", group_by="period"))

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "langchain_google_genai", SimpleNamespace(ChatGoogleGenerativeAI=FakeGemini))
    result = _plan({"question": "แนวโน้มเงินฝาก"})
    assert result["plan"]["metric"] == "deposits"
    assert result["mode"].endswith("(gemini)")
    assert calls["model"] == "gemini-2.5-flash"
    assert calls["api_key"] == "test-key"
