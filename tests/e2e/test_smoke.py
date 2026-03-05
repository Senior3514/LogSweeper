"""E2E smoke tests for LogSweeper.

These tests verify the full flow: ingest -> parse -> store -> query.
Run against a real (temporary) database.
"""

import os
import tempfile

import pytest

from src.logsweeper.api.app import create_app


@pytest.fixture
def client():
    db_path = tempfile.mktemp(suffix=".db")
    os.environ["LOGSWEEPER_DB_PATH"] = db_path
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_full_flow(client):
    """Smoke test: health -> ingest -> query -> detail."""
    # 1. Health check
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    # 2. Ingest mixed log lines
    lines = [
        '{"timestamp":"2024-06-15T10:00:00Z","message":"User login","hostname":"web1"}',
        '{"timestamp":"2024-06-15T10:01:00Z","message":"DB query slow","host":"db1"}',
        "Jun 15 10:02:00 app1 nginx[5678]: GET /api/events 200",
        "raw unstructured log line",
    ]
    resp = client.post("/api/ingest", json={"source": "smoke-test", "lines": lines})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 4

    # 3. Query all events
    resp = client.get("/api/events")
    data = resp.get_json()
    assert data["total"] == 4

    # 4. Query with filter
    resp = client.get("/api/events?search=login")
    data = resp.get_json()
    assert data["total"] == 1
    assert "login" in data["events"][0]["message"].lower()

    # 5. Event detail
    event_id = data["events"][0]["id"]
    resp = client.get(f"/api/events/{event_id}")
    assert resp.status_code == 200
    detail = resp.get_json()
    assert detail["source"] == "smoke-test"

    # 6. Sources
    resp = client.get("/api/sources")
    assert "smoke-test" in resp.get_json()["sources"]

    # 7. Categories
    resp = client.get("/api/categories")
    cats = resp.get_json()["categories"]
    assert "json" in cats
