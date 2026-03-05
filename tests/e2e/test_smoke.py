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
    os.environ.pop("LOGSWEEPER_API_KEY", None)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_full_flow(client):
    """Smoke test: health -> ingest -> query -> detail -> stats."""
    # 1. Health check
    resp = client.get("/healthz")
    assert resp.status_code == 200
    health = resp.get_json()
    assert health["status"] == "ok"
    assert health["events_count"] == 0

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

    # 8. Stats
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    stats = resp.get_json()
    assert stats["total_events"] == 4
    assert stats["source_count"] == 1
    assert "smoke-test" in stats["sources"]


def test_security_hardening_e2e(client):
    """End-to-end security verification."""
    # Security headers present on all responses
    resp = client.get("/healthz")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"

    # Path traversal blocked
    resp = client.post("/api/ingest", json={"source": "test", "file": "/etc/passwd"})
    assert resp.status_code == 403

    # SSRF blocked
    resp = client.post("/api/ingest", json={"source": "test", "url": "http://127.0.0.1:80/"})
    assert resp.status_code == 403

    # Invalid input rejected
    resp = client.post("/api/ingest", json={"source": "test", "lines": "not-a-list"})
    assert resp.status_code == 400

    # Offset clamped
    resp = client.get("/api/events?offset=-1")
    assert resp.status_code == 200
    assert resp.get_json()["offset"] == 0

    # Limit clamped
    resp = client.get("/api/events?limit=99999")
    assert resp.status_code == 200
    assert resp.get_json()["limit"] == 1000


def test_batch_ingest_and_paginate(client):
    """Test large batch ingestion and pagination."""
    lines = [f'{{"message":"batch event {i}","timestamp":"2024-01-01T00:{i // 60:02d}:{i % 60:02d}Z"}}' for i in range(100)]
    resp = client.post("/api/ingest", json={"source": "batch-test", "lines": lines})
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 100

    # First page
    resp = client.get("/api/events?limit=25&offset=0")
    data = resp.get_json()
    assert data["total"] == 100
    assert len(data["events"]) == 25

    # Last page
    resp = client.get("/api/events?limit=25&offset=75")
    data = resp.get_json()
    assert len(data["events"]) == 25

    # Filter by source
    resp = client.get("/api/events?source=batch-test")
    data = resp.get_json()
    assert data["total"] == 100

    # Search
    resp = client.get("/api/events?search=batch+event+50")
    data = resp.get_json()
    assert data["total"] >= 1
