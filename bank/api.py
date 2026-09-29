from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from .chat import ask
from .db import read_engine
from .etl import build_mart, run_source

app = FastAPI(title="Thailand Regional Banking Intelligence", version="0.1.0")


class ChatRequest(BaseModel):
    question: str
    session_id: str = "demo"


@app.get("/health")
def health():
    with read_engine().connect() as conn:
        periods = conn.execute(text("SELECT COUNT(DISTINCT period), MAX(period) FROM mart_province_month")).one()
    return {"status": "ok", "months_loaded": periods[0], "latest_period": str(periods[1])}


@app.get("/overview")
def overview():
    with read_engine().connect() as conn:
        latest = conn.execute(text("SELECT MAX(period) FROM mart_province_month")).scalar_one()
        if latest is None:
            raise HTTPException(503, "Warehouse is empty")
        total = conn.execute(text("SELECT SUM(credits_million_baht) credits, SUM(deposits_million_baht) deposits, SUM(branches) branches FROM mart_province_month WHERE period=:p"), {"p": latest}).mappings().one()
        trend = conn.execute(text("SELECT period, SUM(credits_million_baht) credits, SUM(deposits_million_baht) deposits FROM mart_province_month GROUP BY period ORDER BY period")).mappings().all()
        provinces = conn.execute(text("SELECT name_th, name_en, province_code, credits_million_baht, deposits_million_baht, branches FROM mart_province_month WHERE period=:p ORDER BY credits_million_baht DESC"), {"p": latest}).mappings().all()
    return {"latest_period": latest.isoformat(), "totals": dict(total),
            "trend": [{**dict(r), "period": r["period"].isoformat()} for r in trend],
            "provinces": [dict(r) for r in provinces]}


@app.post("/chat")
def chat(payload: ChatRequest):
    if len(payload.question) > 1000:
        raise HTTPException(400, "Question is too long")
    return ask(payload.question, payload.session_id)


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
