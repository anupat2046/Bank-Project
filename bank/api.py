from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from .chat import ask
from .db import read_engine
from .etl import build_mart, run_source
from .analytics import metadata, overview_data, snapshot, province_history, source_data, resolve_period, read
from .competency import QUESTIONS, queries, run_question, question_query

app = FastAPI(title="Thailand Regional Banking Intelligence", version="0.1.0")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(default="demo", min_length=1, max_length=100)


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


@app.post("/chat")
def chat(payload: ChatRequest):
    if len(payload.question) > 1000:
        raise HTTPException(400, "Question is too long")
    result = ask(payload.question, payload.session_id)
    if result.get("mode") == "error":
        result.update(error="ผู้ให้บริการ AI ไม่พร้อมใช้งาน กรุณาลองใหม่ภายหลัง", answer="ผู้ให้บริการ AI ไม่พร้อมใช้งาน กรุณาลองใหม่ภายหลัง")
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
