"""Web API contracts checked against the real warehouse, no paid LLM calls."""
from datetime import date

from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from bank.api import app
from bank.competency import QUESTIONS, run_question

client = TestClient(app)


def test_overview_matches_snapshot_and_yoy():
    meta = client.get('/metadata').json()
    assert len(meta['provinces']) == 77
    assert len(meta['periods']) >= 25
    current = client.get('/overview').json()
    rows = client.get('/provinces', params={'period': current['period']}).json()['rows']
    assert len(rows) == 77
    assert current['totals']['credits'] == sum(r['credits_million_baht'] for r in rows)
    assert 0 <= current['concentration']['bangkok_share_pct'] <= current['concentration']['top5_share_pct'] <= 100
    assert current['changes']['credits'] is not None
    old = client.get('/overview', params={'period': meta['periods'][-1]}).json()
    assert old['changes']['credits'] is None
    assert all(r['period'] <= old['period'] for r in old['trend'])
    assert client.get('/overview?period=1990-01-01').status_code == 404
    assert client.get('/overview?period=not-a-date').status_code == 422


def test_province_history_and_sources_are_public_only():
    history = client.get('/provinces/50/history').json()['rows']
    assert history and all(r['province_code'] == 50 for r in history)
    assert client.get('/provinces/999/history').status_code == 404
    compare = client.get('/comparison?codes=50,20').json()['rows']
    assert len(compare) >= 50 and {r['province_code'] for r in compare} == {50, 20}
    assert client.get('/comparison?codes=50,20,10,30,40').status_code == 422
    assert client.get('/comparison?codes=50,99').status_code == 404
    sources = client.get('/sources').json()
    assert len(sources['sources']) == 5
    assert sources['coverage']['provinces'] == 77
    assert all(s['freshness'] == 'not_checked' for s in sources['sources'])
    assert all('raw_path' not in s for s in sources['sources'])
    assert all('detail' not in r for r in sources['runs'])


def test_question_api_all_ten_and_historical_scope():
    meta = client.get('/metadata').json()
    period = date.fromisoformat(meta['periods'][0])
    assert len(client.get('/questions').json()) == 10
    for q in QUESTIONS:
        result = client.get('/questions/' + q[0]).json()
        assert result['rows'] == jsonable_encoder(run_question(q[0], period))
        assert result['sql'] and result['parameters']['as_of'] == period.isoformat()
    oldest = meta['periods'][-1]
    early = client.get('/questions/CQ05', params={'period': oldest}).json()
    assert len(early['rows']) == 1 and early['rows'][0]['period'] == oldest
    assert client.get('/questions/CQ04', params={'period': oldest}).json()['rows'] == []
    assert client.get('/questions/CQ99').status_code == 404


def test_chat_input_bounds_and_provider_errors_are_redacted(monkeypatch):
    import bank.api as api
    monkeypatch.setattr(api, 'ask', lambda *args: {'mode': 'error', 'error': 'private-provider-detail', 'answer': 'private-provider-detail', 'result': None})
    reply = client.post('/chat', json={'question': 'test', 'session_id': 'web-test'})
    assert reply.status_code == 200 and 'private-provider-detail' not in reply.text
    assert client.post('/chat', json={'question': ''}).status_code == 422
    assert client.post('/chat', json={'question': 'a'*1001}).status_code == 422
