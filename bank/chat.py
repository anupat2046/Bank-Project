"""Bounded LangGraph workflow: classify -> plan -> validated SQL -> answer."""
from __future__ import annotations

import os
import atexit
from functools import lru_cache
from typing import Any, TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from .db import engine
from .query import Clarification, QueryPlan, execute_plan, rules_plan


class ChatState(TypedDict, total=False):
    question: str
    plan: dict
    result: dict
    answer: str
    error: str
    mode: str


def _provider() -> str | None:
    """Prefer the selected Gemini provider; preserve OpenAI as an optional fallback."""
    if os.getenv("GEMINI_API_KEY", "").strip():
        return "gemini"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return None


def _plan(state: ChatState) -> ChatState:
    question = state["question"]
    try:
        provider = _provider()
        if provider:
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                model = ChatGoogleGenerativeAI(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                    api_key=os.environ["GEMINI_API_KEY"],
                    temperature=0,
                )
            else:
                from langchain_openai import ChatOpenAI
                model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0)
            planner = model.with_structured_output(QueryPlan)
            prompt = (
                "You map Thai or English banking questions to a QueryPlan. "
                "Only use supported fields. No raw SQL. group_by=period only for monthly trends "
                "or the national policy_rate metric; policy_rate must not have a province. "
                "otherwise province means latest available month. For trends use limit=25. "
                "Do not infer private bank/customer data. "
                "If user asks unrelated data, the caller will handle unsupported metric. "
                f"Question: {question}"
            )
            plan = planner.invoke(prompt)
            mode = f"LangGraph + LangChain structured LLM ({provider})"
        else:
            plan = rules_plan(question)
            mode = "กฎภาษาไทย (ไม่ใช้ AI เพราะยังไม่มี GEMINI_API_KEY หรือ OPENAI_API_KEY)"
        return {"plan": plan.model_dump(mode="json"), "result": None,
                "error": None, "answer": None, "mode": mode}
    except (Clarification, ValueError) as exc:
        return {"result": None, "error": str(exc), "mode": "clarification"}
    except Exception as exc:
        return {"result": None, "error": f"LLM ไม่พร้อมใช้งาน: {type(exc).__name__}: {exc}", "mode": "error"}


def _route(state: ChatState) -> str:
    return "error" if state.get("error") else "execute"


def _execute(state: ChatState) -> ChatState:
    try:
        result = execute_plan(QueryPlan.model_validate(state["plan"]))
        return {"result": result}
    except (Clarification, ValueError) as exc:
        return {"result": None, "error": str(exc)}
    except Exception as exc:
        return {"result": None, "error": f"Query failed: {type(exc).__name__}: {exc}"}


def _answer(state: ChatState) -> ChatState:
    result = state.get("result")
    if result is None:
        return {"answer": state.get("error", "ไม่สามารถตอบได้")}
    rows = result["rows"]
    if not rows:
        return {"answer": "ไม่มีข้อมูลตรงเงื่อนไขที่ถาม"}
    trend = result["plan"]["group_by"] == "period"
    first = rows[-1] if trend else rows[0]
    value = first.get("value")
    rendered = f"{value:,.2f}" if value is not None else "ไม่มีค่า"
    name = first.get("name_th") or first.get("period") or ""
    if trend:
        return {"answer": f"{result['metric_label']} ล่าสุด {name}: {rendered} {result['unit']} (แสดง {len(rows)} เดือน)"}
    return {"answer": f"{result['metric_label']}: {name} {rendered} {result['unit']} (อันดับแรกจาก {len(rows)} จังหวัด)"}


@lru_cache(maxsize=1)
def graph():
    builder = StateGraph(ChatState)
    builder.add_node("plan", _plan)
    builder.add_node("execute", _execute)
    builder.add_node("answer", _answer)
    builder.add_edge(START, "plan")
    builder.add_conditional_edges("plan", _route, {"error": "answer", "execute": "execute"})
    builder.add_edge("execute", "answer")
    builder.add_edge("answer", END)
    dsn = engine().url.render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
    manager = PostgresSaver.from_conn_string(dsn)
    saver = manager.__enter__()
    saver.setup()
    atexit.register(lambda: manager.__exit__(None, None, None))
    return builder.compile(checkpointer=saver)


def ask(question: str, session_id: str = "default") -> dict[str, Any]:
    state = graph().invoke({"question": question},
                           config={"configurable": {"thread_id": session_id}})
    return {k: state.get(k) for k in ("answer", "result", "error", "mode")}
