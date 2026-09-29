"""Airflow orchestration. Each request performs validated, atomic source ETL."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


def run_job(job: str):
    url = f"http://api:8000/etl/{job}"
    token = os.environ["ETL_API_TOKEN"]
    request = Request(url, data=b"{}", method="POST",
                      headers={"X-ETL-Token": token, "Content-Type": "application/json"})
    with urlopen(request, timeout=240) as response:
        print(response.read().decode("utf-8"))


with DAG(
    dag_id="bank_regional_daily",
    start_date=pendulum.datetime(2026, 9, 1, tz="Asia/Bangkok"),
    schedule_interval="0 7 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["bank", "real-data", "etl"],
) as dag:
    bot = PythonOperator(task_id="load_bot", python_callable=run_job, op_kwargs={"job": "bot"})
    dopa = PythonOperator(task_id="load_dopa", python_callable=run_job, op_kwargs={"job": "dopa"})
    nesdc = PythonOperator(task_id="load_nesdc", python_callable=run_job, op_kwargs={"job": "nesdc"})
    worldbank = PythonOperator(task_id="load_worldbank_api", python_callable=run_job, op_kwargs={"job": "worldbank"})
    policy = PythonOperator(task_id="load_bot_policy_workbook", python_callable=run_job, op_kwargs={"job": "policy"})
    mart = PythonOperator(task_id="build_mart", python_callable=run_job, op_kwargs={"job": "mart"})
    [bot, dopa, nesdc, worldbank, policy] >> mart
