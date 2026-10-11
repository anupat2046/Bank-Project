"""Generate provisioned Grafana dashboards from version-controlled SQL.

Run from the repository root: python tools/build_operations_dashboards.py
All panels use the existing SELECT-only PostgreSQL datasource.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DS = {'type': 'postgres', 'uid': 'bank-postgres'}


def panel(title, sql, kind='table', description='', unit='none'):
    return dict(title=title, type=kind, datasource=DS,
                description=description,
                targets=[dict(refId='A', datasource=DS, rawSql=sql,
                              format='table', editorMode='code', rawQuery=True)],
                fieldConfig={'defaults': {'unit': unit, 'noValue': 'No observations'}, 'overrides': [
                    {'matcher': {'id': 'byName', 'options': 'reference'},
                     'properties': [{'id': 'unit', 'value': 'string'}]}]},
                options={'showHeader': True} if kind == 'table' else
                {'reduceOptions': {'calcs': ['lastNotNull'], 'fields': '', 'values': False},
                 'colorMode': 'value', 'graphMode': 'none', 'textMode': 'auto'})


def dashboard(uid, title, intro, panels):
    note = dict(id=1, type='text', title='Reading this dashboard',
                gridPos=dict(x=0, y=0, w=24, h=4),
                options={'mode': 'markdown', 'content': intro})
    for i, p in enumerate(panels):
        p.update(id=i+2, gridPos=dict(x=0, y=4+i*7, w=24, h=7))
    return dict(uid=uid, title=title, schemaVersion=39, version=1,
                tags=['bank-intelligence', 'operations'], timezone='Asia/Bangkok',
                refresh='1m', time={'from': 'now-7d', 'to': 'now'},
                templating={'list': []}, annotations={'list': []},
                links=[{'title': label, 'url': '/d/'+key, 'type': 'link'} for key, label in [
                    ('thai-bank-regions', 'Pipeline Health'), ('bank-data-quality', 'Data Quality'),
                    ('bank-ai-operations', 'AI & API Operations')]], panels=[note, *panels])


pipeline = dashboard('thai-bank-regions', 'Bank Operations / Pipeline Health',
    'ETL job records, **not Airflow DAG run history**. `started_at` in the legacy log records completion time; '
    'the tables below label it accordingly. Duration is available only for new runs after the instrumentation update. '
    'No historical durations or scheduled runs are reconstructed. Latest-state panels ignore the time picker; activity panels use it.', [
    panel('Latest recorded result by job (all time)', """
WITH jobs(source) AS (VALUES ('bot'),('dopa'),('nesdc'),('worldbank'),('policy'),('mart'))
SELECT j.source, COALESCE(r.status,'not observed') AS status,
 r.started_at AS recorded_at, r.rows_loaded, ROUND(r.duration_ms::numeric/1000,2) AS duration_seconds,
 EXTRACT(EPOCH FROM (now()-r.started_at))/3600 AS hours_since_record
FROM jobs j LEFT JOIN LATERAL (SELECT * FROM etl_run e WHERE e.source=j.source
 ORDER BY started_at DESC,id DESC LIMIT 1) r ON true ORDER BY j.source"""),
    panel('Recorded job outcomes (selected window)', """SELECT source,status,COUNT(*) AS recorded_runs
FROM etl_run WHERE $__timeFilter(started_at) GROUP BY source,status ORDER BY source,status"""),
    panel('Recent job records (selected window)', """SELECT started_at AS recorded_at,source,status,rows_loaded,
 ROUND(duration_ms::numeric/1000,2) AS duration_seconds
FROM etl_run WHERE $__timeFilter(started_at) ORDER BY started_at DESC,id DESC LIMIT 100""",
          description='Raw exception detail is deliberately excluded. Inspect local service logs for diagnosis.'),
    panel('Recorded failures (selected window)', """SELECT started_at AS recorded_at,source,status
FROM etl_run WHERE $__timeFilter(started_at) AND status<>'success' ORDER BY started_at DESC LIMIT 100"""),
    panel('Job duration p50 / p95 (selected window)', """SELECT source,COUNT(duration_ms) AS measured_runs,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_ms)/1000 AS p50_seconds,
 percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms)/1000 AS p95_seconds
FROM etl_run WHERE $__timeFilter(started_at) GROUP BY source ORDER BY source"""),
    panel('Last successful source load (all time)', """SELECT source,MAX(started_at) AS last_success_recorded_at
FROM etl_run WHERE status='success' GROUP BY source ORDER BY source""",
          description='Successful retrieval is not proof of a newly published source period.')])

quality = dashboard('bank-data-quality', 'Bank Operations / Data Quality & Freshness',
    'These panels query the **current warehouse snapshot** and ignore the time picker. '
    'Retrieval time and reference period are different. Annual sources naturally lag monthly banking data. '
    'NULL GPP/inflation can be expected under availability rules, not necessarily a broken pipeline. '
    'Historical mapping-error counts are not recorded; failed jobs must be investigated in ETL logs.', [
    panel('Warehouse coverage', """SELECT COUNT(*) AS analytical_rows,COUNT(DISTINCT province_code) AS provinces,
 COUNT(DISTINCT period) AS months,MIN(period)::text AS first_month,MAX(period)::text AS latest_month FROM mart_province_month"""),
    panel('Latest available source reference (all time)', """SELECT 'BOT' AS source,MAX(period)::text AS reference FROM fact_bank_month
UNION ALL SELECT 'DOPA',MAX(reference_year)::text FROM fact_population_year
UNION ALL SELECT 'NESDC',MAX(reference_year)::text FROM fact_gpp_year
UNION ALL SELECT 'World Bank',MAX(reference_year)::text FROM fact_macro_year
UNION ALL SELECT 'Policy effective date',MAX(event_date)::text FROM fact_policy_event"""),
    panel('Latest source retrieval', """SELECT source,MAX(fetched_at) AS last_retrieved_at,
 COUNT(*) AS retained_manifests FROM source_manifest GROUP BY source ORDER BY source""",
          description='Publication/revision metadata is shown separately below; this table is retrieval time only.'),
    panel('Annual source publication / revision metadata', """SELECT 'NESDC' AS source,MAX(source_last_modified)::text AS source_revision_date FROM fact_gpp_year
UNION ALL SELECT 'World Bank',MAX(source_last_updated)::text FROM fact_macro_year"""),
    panel('Coverage and missing values by banking month', """SELECT period::text,COUNT(*) AS rows,
 COUNT(DISTINCT province_code) AS provinces,77-COUNT(DISTINCT province_code) AS provinces_short_of_77,
 COUNT(*) FILTER(WHERE population IS NULL) AS population_missing,
 COUNT(*) FILTER(WHERE gpp_million_baht IS NULL) AS gpp_unavailable,
 COUNT(*) FILTER(WHERE inflation_pct IS NULL) AS inflation_unavailable,
 COUNT(*) FILTER(WHERE policy_rate_pct IS NULL) AS policy_unavailable
FROM mart_province_month GROUP BY period ORDER BY period DESC"""),
    panel('Current integrity checks', """SELECT
 (SELECT COUNT(*) FROM (SELECT province_code,period FROM mart_province_month GROUP BY 1,2 HAVING COUNT(*)>1) d) AS duplicate_keys,
 (SELECT COUNT(*) FROM mart_province_month m LEFT JOIN dim_province p USING(province_code) WHERE p.province_code IS NULL) AS unmapped_province_rows,
 (SELECT COUNT(*) FROM mart_province_month WHERE credits_million_baht<0 OR deposits_million_baht<0 OR branches<0 OR population<=0) AS invalid_values,
 (SELECT COUNT(*) FROM fact_bank_month b LEFT JOIN mart_province_month m USING(province_code,period) WHERE m.period IS NULL) AS bank_rows_missing_from_mart""",
          description='Current-state checks, not a historical data-quality incident counter.')])

ai = dashboard('bank-ai-operations', 'Bank Operations / AI & API Performance',
    'Observed HTTP requests only, from the instrumentation deployment onward. API and chat rows measure different layers; '
    'do not add their counts together. API latency ends when the response is produced and excludes metric persistence. '
    'No prompts, session IDs, keys, query strings or raw errors are stored. '
    '**HTTP success is not answer accuracy.** Offline/live evaluation scores remain in the dated evaluation reports. '
    'Unknown token usage and unconfigured costs remain NULL. Automated HTTP checks also count as traffic.', [
    panel('API requests by route and status', """SELECT route,status,COUNT(*) AS requests
FROM operation_metric WHERE kind='api' AND $__timeFilter(recorded_at) GROUP BY route,status ORDER BY requests DESC"""),
    panel('API latency by route (ms)', """SELECT route,COUNT(*) AS requests,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY latency_ms) AS p50_ms,
 percentile_cont(0.95) WITHIN GROUP(ORDER BY latency_ms) AS p95_ms
FROM operation_metric WHERE kind='api' AND $__timeFilter(recorded_at) GROUP BY route ORDER BY p95_ms DESC"""),
    panel('Assistant outcomes', """SELECT status,COUNT(*) AS turns FROM operation_metric
WHERE kind='chat' AND $__timeFilter(recorded_at) GROUP BY status ORDER BY turns DESC"""),
    panel('Assistant latency and provider failures', """SELECT COUNT(*) AS observed_turns,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY latency_ms) AS p50_ms,
 percentile_cont(0.95) WITHIN GROUP(ORDER BY latency_ms) AS p95_ms,
 SUM(llm_calls) AS model_calls,SUM(provider_errors) AS failed_model_calls
FROM operation_metric WHERE kind='chat' AND $__timeFilter(recorded_at)"""),
    panel('Token usage and configured cost coverage', """SELECT COUNT(*) AS observed_turns,
 COUNT(*) FILTER(WHERE total_tokens IS NULL) AS unknown_usage_turns,
 SUM(total_tokens) AS known_tokens_only,
 COUNT(estimated_cost_usd) AS cost_known_turns,
 SUM(estimated_cost_usd) AS known_estimated_cost_usd
FROM operation_metric WHERE kind='chat' AND $__timeFilter(recorded_at)""",
          description='Partial sums are not full totals when coverage is incomplete. Costs use configured uncached token rates, not billing invoices.'),
    panel('HTTP failures and clarification rate', """SELECT
 100.0*COUNT(*) FILTER(WHERE kind='api' AND status::text ~ '^5')/NULLIF(COUNT(*) FILTER(WHERE kind='api'),0) AS api_5xx_pct,
 100.0*COUNT(*) FILTER(WHERE kind='chat' AND status='clarification')/NULLIF(COUNT(*) FILTER(WHERE kind='chat'),0) AS chat_clarification_pct,
 100.0*COUNT(*) FILTER(WHERE kind='chat' AND status='error')/NULLIF(COUNT(*) FILTER(WHERE kind='chat'),0) AS chat_error_pct
FROM operation_metric WHERE $__timeFilter(recorded_at)""",
          description='A clarification is a valid outcome, not necessarily an error. Empty denominators return NULL.')])

if __name__ == '__main__':
    for filename, spec in [('regional-banking.json', pipeline), ('data-quality.json', quality), ('ai-operations.json', ai)]:
        (ROOT/'grafana'/'dashboards'/filename).write_text(json.dumps(spec, indent=2)+'\n', encoding='utf-8')
        print(f'{filename}: {len(spec["panels"])} panels')
