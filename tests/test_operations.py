import json
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import text
from bank import operations
from bank.api import app
from bank.db import read_engine
from bank.observability import summarize


def test_metric_write_is_allowlisted_and_best_effort(monkeypatch):
    monkeypatch.setenv('OPERATIONS_METRICS_ENABLED', 'true')
    eng = MagicMock()
    monkeypatch.setattr(operations, 'engine', lambda: eng)
    operations.persist(dict(kind='api', status='200', latency_ms=1, question='private', api_key='private'))
    statement = eng.begin.return_value.__enter__.return_value.execute.call_args.args[0]
    assert 'private' not in str(statement.compile().params)
    eng.begin.side_effect = RuntimeError('private connection error')
    operations.persist(dict(kind='api', status='200', latency_ms=1))


def test_non_http_evaluation_does_not_persist_chat(monkeypatch):
    saved = []
    monkeypatch.setattr(operations, 'persist', saved.append)
    summary = summarize([{'event': 'llm', 'failure_type': 'TimeoutError'}], 20, 'error')
    assert summary['provider_errors'] == 1 and summary['total_tokens'] is None
    operations.persist_chat(summary)
    assert saved == []
    token = operations.live_request.set(True)
    try:
        operations.persist_chat(summary)
    finally:
        operations.live_request.reset(token)
    assert saved[0]['provider_errors'] == 1
    assert saved[0]['total_tokens'] is None


def test_http_metrics_do_not_store_unknown_path_or_query(monkeypatch):
    saved = []
    monkeypatch.setattr(operations, 'persist', saved.append)
    response = TestClient(app).get('/private-path?key=secret')
    assert response.status_code == 404
    assert saved[-1]['route'] == 'unmatched'
    assert 'secret' not in json.dumps(saved)
    assert 'private-path' not in json.dumps(saved)


def test_chat_telemetry_crosses_http_worker_context(monkeypatch):
    from bank.observability import emit
    saved = []
    monkeypatch.setattr(operations, 'persist', saved.append)
    def fake_ask(*args):
        emit(summarize([], 3, 'clarification'))
        return {'mode': 'clarification', 'answer': 'Select a metric'}
    monkeypatch.setattr('bank.api.ask', fake_ask)
    assert TestClient(app).post('/chat', json={'question': 'test'}).status_code == 200
    assert [r['kind'] for r in saved] == ['chat', 'api']
    assert saved[0]['total_tokens'] == 0
    assert saved[0]['status'] == 'clarification'


def test_dashboard_queries_with_reader_role():
    root = Path(__file__).resolve().parents[1]
    dashboards = list((root/'grafana/dashboards').glob('*.json'))
    assert len(dashboards) == 3
    with read_engine().connect() as conn:
        assert conn.execute(text('SELECT current_user')).scalar_one() == 'bank_reader'
        for path in dashboards:
            spec = json.loads(path.read_text())
            assert len(spec['panels']) == 7
            for panel in spec['panels']:
                for target in panel.get('targets', []):
                    sql = target['rawSql']
                    sql = sql.replace('$__timeFilter(started_at)', "started_at >= now()-interval '7 days'")
                    sql = sql.replace('$__timeFilter(recorded_at)', "recorded_at >= now()-interval '7 days'")
                    conn.execute(text(sql)).all()
