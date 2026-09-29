from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import (Column, Date, DateTime, Float, Integer, MetaData,
                        String, Table, Text, create_engine, func, text)

metadata = MetaData()
province = Table("dim_province", metadata,
    Column("province_code", Integer, primary_key=True),
    Column("name_en", String(100), nullable=False),
    Column("name_th", String(100)),
)
month = Table("dim_month", metadata,
    Column("period", Date, primary_key=True),
    Column("year_ce", Integer, nullable=False),
    Column("year_be", Integer, nullable=False),
    Column("month_number", Integer, nullable=False),
)
bank = Table("fact_bank_month", metadata,
    Column("province_code", Integer, primary_key=True),
    Column("period", Date, primary_key=True),
    Column("branches", Integer),
    Column("deposits_million_baht", Float),
    Column("credits_million_baht", Float),
    Column("source_sha256", String(64), nullable=False),
)
population = Table("fact_population_year", metadata,
    Column("province_code", Integer, primary_key=True),
    Column("reference_year", Integer, primary_key=True),
    Column("population", Integer, nullable=False),
    Column("source_sha256", String(64), nullable=False),
)
gpp = Table("fact_gpp_year", metadata,
    Column("province_code", Integer, primary_key=True),
    Column("reference_year", Integer, primary_key=True),
    Column("gpp_million_baht", Float, nullable=False),
    Column("source_last_modified", Date),
    Column("source_sha256", String(64), nullable=False),
)
macro = Table("fact_macro_year", metadata,
    Column("reference_year", Integer, primary_key=True),
    Column("inflation_pct", Float, nullable=False),
    Column("source_last_updated", Date, nullable=False),
    Column("source_sha256", String(64), nullable=False),
)
policy = Table("fact_policy_event", metadata,
    Column("event_date", Date, primary_key=True),
    Column("policy_rate_pct", Float, nullable=False),
    Column("decision", String(80)),
    Column("source_sha256", String(64), nullable=False),
)
mart = Table("mart_province_month", metadata,
    Column("province_code", Integer, primary_key=True),
    Column("period", Date, primary_key=True),
    Column("name_en", String(100), nullable=False),
    Column("name_th", String(100)),
    Column("branches", Integer),
    Column("deposits_million_baht", Float),
    Column("credits_million_baht", Float),
    Column("credit_deposit_ratio_pct", Float),
    Column("population", Integer),
    Column("population_reference_year", Integer),
    Column("branches_per_100k", Float),
    Column("deposits_baht_per_person", Float),
    Column("gpp_million_baht", Float),
    Column("gpp_reference_year", Integer),
    Column("inflation_pct", Float),
    Column("inflation_reference_year", Integer),
    Column("policy_rate_pct", Float),
    Column("policy_event_date", Date),
)
source_manifest = Table("source_manifest", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(40), nullable=False),
    Column("url", Text, nullable=False),
    Column("raw_path", Text, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("reference", String(50)),
    Column("fetched_at", DateTime(timezone=True), server_default=func.now()),
)
etl_run = Table("etl_run", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(40), nullable=False),
    Column("status", String(20), nullable=False),
    Column("rows_loaded", Integer, nullable=False, default=0),
    Column("detail", Text),
    Column("started_at", DateTime(timezone=True), server_default=func.now()),
)


@lru_cache(maxsize=1)
def engine():
    url = os.getenv("DATABASE_URL", "postgresql+psycopg://bank:bank_dev_password@127.0.0.1:5433/bank")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 8})


@lru_cache(maxsize=1)
def read_engine():
    url = os.getenv("READ_DATABASE_URL", "postgresql+psycopg://bank_reader:bank_reader_dev_password@127.0.0.1:5433/bank")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 8})


def init_db():
    metadata.create_all(engine())
    # Forward-only additive migration for workspaces initialized before the API source.
    with engine().begin() as conn:
        conn.execute(text("ALTER TABLE fact_gpp_year ADD COLUMN IF NOT EXISTS source_last_modified DATE"))
        conn.execute(text("ALTER TABLE mart_province_month ADD COLUMN IF NOT EXISTS inflation_pct DOUBLE PRECISION"))
        conn.execute(text("ALTER TABLE mart_province_month ADD COLUMN IF NOT EXISTS inflation_reference_year INTEGER"))
        conn.execute(text("ALTER TABLE mart_province_month ADD COLUMN IF NOT EXISTS policy_rate_pct DOUBLE PRECISION"))
        conn.execute(text("ALTER TABLE mart_province_month ADD COLUMN IF NOT EXISTS policy_event_date DATE"))
