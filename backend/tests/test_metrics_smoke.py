from fastapi.testclient import TestClient

from backend.api import app
from backend.realtime.gateway import hub
from services.economy_service import EconomyService


def test_metrics_endpoint_exposes_counters(tmp_path):
    # exercise economy service
    svc = EconomyService(db_path=tmp_path / "test.db")
    svc.ensure_schema()
    svc.deposit(1, 100)

    # exercise realtime service
    import asyncio

    asyncio.run(hub.publish("test", {"hello": "world"}))

    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "economy_transactions_total" in body
    assert "realtime_messages_published_total" in body


def test_request_latency_histogram_records_requests():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert 'http_request_duration_ms_bucket{method="GET",path="/",status="200",le="+Inf"}' in body
    assert 'http_request_duration_ms_count{method="GET",path="/",status="200"}' in body
