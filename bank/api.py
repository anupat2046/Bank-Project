from __future__ import annotations

import os
from contextlib import asynccontextmanager
from time import perf_counter
from datetime import date
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from .chat import ask
from .chat import _provider
from .llm_runtime import provider_health
from .db import read_engine
from . import operations
from starlette.concurrency import run_in_threadpool
from .etl import build_mart, run_source
from .analytics import metadata, overview_data, snapshot, province_history, source_data, resolve_period, read
from .competency import QUESTIONS, queries, run_question, question_query

@asynccontextmanager
async def lifespan(app):
    if operations.enabled():
        from .db import init_db
        await run_in_threadpool(init_db)
    yield


app = FastAPI(title="Thailand Regional Banking Intelligence", version="0.1.0", lifespan=lifespan)


@app.middleware('http')
async def measure_request(request, call_next):
    started = perf_counter()
    token = operations.live_request.set(True)
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        operations.live_request.reset(token)
        route = request.scope.get('route')
        # Route templates avoid storing province IDs, unknown paths or query strings.
        route_name = getattr(route, 'path', 'unmatched')
        await run_in_threadpool(operations.persist, dict(
            kind='api', route=route_name, status=str(status),
            latency_ms=(perf_counter()-started)*1000))


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)


@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Warehouse temporarily unavailable"})


@app.get("/metadata")
def get_metadata():
    return metadata()


@app.get("/provinces")
def get_snapshot(period: date | None = None):
    return snapshot(period)


@app.get("/provinces/{code}/history")
def get_history(code: int, period: date | None = None):
    return province_history(code, period)


@app.get("/sources")
def get_sources():
    return source_data()


@app.get("/comparison")
def get_comparison(codes: str = Query(pattern=r"^\d{1,2}(,\d{1,2}){0,3}$"), period: date | None = None):
    selected, _ = resolve_period(period)
    ids = sorted(set(int(c) for c in codes.split(',')))
    params = {f"c{i}": code for i, code in enumerate(ids)}
    slots = ','.join(':'+key for key in params)
    params['p'] = selected
    rows = read(f"SELECT * FROM mart_province_month WHERE province_code IN ({slots}) AND period<=:p ORDER BY period,province_code", params)
    if len({r['province_code'] for r in rows}) != len(ids):
        raise HTTPException(404, "Province has no data")
    return {"period": selected, "rows": rows}


@app.get("/questions")
def get_questions():
    return [{"id": q[0], "title": q[1], "sources": q[2], "fields": q[3],
             "view": q[4], "caveat": q[5]} for q in QUESTIONS]


@app.get("/questions/{qid}")
def get_question(qid: str, period: date | None = None):
    if qid not in queries():
        raise HTTPException(404, "Unknown competency question")
    selected, _ = resolve_period(period)
    item = next(q for q in get_questions() if q["id"] == qid)
    sql, _ = question_query(qid, selected)
    return {**item, "period": selected, "rows": run_question(qid, selected), "sql": sql,
            "sql_scope": "Catalog SQL evaluated on rows with period <= selected month", "parameters": {"as_of": selected}}


@app.get("/health")
def health():
    with read_engine().connect() as conn:
        periods = conn.execute(text("SELECT COUNT(DISTINCT period), MAX(period) FROM mart_province_month")).one()
    return {"status": "ok", "months_loaded": periods[0], "latest_period": str(periods[1])}


@app.get("/overview")
def overview(period: date | None = None):
    return overview_data(period)


@app.get('/ai/health')
def ai_health():
    provider = _provider()
    return provider_health(provider) if provider else {
        'provider': None, 'circuit_open': False, 'last_failure': None,
        'scope': 'rules-only; no provider configured'}


@app.post("/chat")
def chat(payload: ChatRequest):
    if len(payload.question) > 1000:
        raise HTTPException(400, "Question is too long")
    result = ask(payload.question, payload.session_id)
    if result.get('mode') == 'error':
        # Public messages are selected by a bounded code, never a provider exception string.
        message = ('ไม่สามารถอ่านผลจากคลังข้อมูลได้ กรุณาลองใหม่'
            if result.get('error_code') == 'warehouse_unavailable'
            else 'ไม่สามารถติดต่อผู้ให้บริการ AI ได้ กรุณาลองใหม่ หรือเลือกคำถามตัวอย่าง')
        result.update(error=message,answer=message)
    return result


@app.post("/etl/{job}")
def run_etl(job: str, x_etl_token: str | None = Header(default=None)):
    required = os.getenv("ETL_API_TOKEN")
    if not required or x_etl_token != required:
        raise HTTPException(403, "Invalid ETL token")
    if job not in {"bot", "dopa", "nesdc", "worldbank", "policy", "mart"}:
        raise HTTPException(404, "Unknown ETL job")
    result = build_mart() if job == "mart" else run_source(job)
    if result["status"] != "success":
        raise HTTPException(500, result)
    return result
