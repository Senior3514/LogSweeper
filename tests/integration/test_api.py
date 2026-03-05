"""Integration tests for the LogSweeper API - including security hardening."""

import json
import os
import tempfile

import pytest

from src.logsweeper.api.app import create_app
from src.logsweeper.ingest.file_ingest import set_allowed_paths


@pytest.fixture
def client():
    os.environ["LOGSWEEPER_DB_PATH"] = tempfile.mktemp(suffix=".db")
    os.environ.pop("LOGSWEEPER_API_KEY", None)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists(os.environ["LOGSWEEPER_DB_PATH"]):
        os.unlink(os.environ["LOGSWEEPER_DB_PATH"])


@pytest.fixture
def auth_client():
    """Client with API key authentication enabled."""
    os.environ["LOGSWEEPER_DB_PATH"] = tempfile.mktemp(suffix=".db")
    os.environ["LOGSWEEPER_API_KEY"] = "test-secret-key-123"
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists(os.environ["LOGSWEEPER_DB_PATH"]):
        os.unlink(os.environ["LOGSWEEPER_DB_PATH"])
    del os.environ["LOGSWEEPER_API_KEY"]


# === Health Check ===

def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "events_count" in data


# === Ingestion ===

def test_ingest_lines(client):
    resp = client.post(
        "/api/ingest",
        json={"source": "test", "lines": ['{"message":"event1"}', "raw line 2"]},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ingested"
    assert data["count"] == 2


def test_events_empty(client):
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["events"] == []
    assert data["total"] == 0


def test_ingest_and_query(client):
    client.post(
        "/api/ingest",
        json={"source": "integration", "lines": ['{"message":"hello"}', '{"message":"world"}']},
    )
    resp = client.get("/api/events")
    data = resp.get_json()
    assert data["total"] == 2
    assert len(data["events"]) == 2


def test_event_detail(client):
    client.post("/api/ingest", json={"source": "test", "lines": ['{"message":"detail test"}']})
    events = client.get("/api/events").get_json()
    event_id = events["events"][0]["id"]

    resp = client.get(f"/api/events/{event_id}")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "detail test"


def test_event_not_found(client):
    resp = client.get("/api/events/9999")
    assert resp.status_code == 404


def test_sources_and_categories(client):
    client.post("/api/ingest", json={"source": "src1", "lines": ['{"message":"a"}']})
    client.post("/api/ingest", json={"source": "src2", "lines": ["raw line"]})

    sources = client.get("/api/sources").get_json()
    assert "src1" in sources["sources"]
    assert "src2" in sources["sources"]

    categories = client.get("/api/categories").get_json()
    assert "json" in categories["categories"]
    assert "raw" in categories["categories"]


def test_search(client):
    client.post("/api/ingest", json={"source": "test", "lines": ['{"message":"error occurred"}', '{"message":"all good"}']})
    resp = client.get("/api/events?search=error")
    data = resp.get_json()
    assert data["total"] == 1
    assert "error" in data["events"][0]["message"]


def test_ingest_no_body(client):
    resp = client.post("/api/ingest")
    assert resp.status_code == 400


def test_ingest_invalid_body(client):
    resp = client.post("/api/ingest", json={"source": "test"})
    assert resp.status_code == 400


# === Stats Endpoint ===

def test_stats_empty(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_events"] == 0
    assert data["source_count"] == 0
    assert data["category_count"] == 0


def test_stats_with_data(client):
    client.post("/api/ingest", json={"source": "app1", "lines": ['{"message":"a"}']})
    client.post("/api/ingest", json={"source": "app2", "lines": ["raw"]})
    resp = client.get("/api/stats")
    data = resp.get_json()
    assert data["total_events"] == 2
    assert data["source_count"] == 2
    assert data["category_count"] == 2
    assert "app1" in data["sources"]
    assert "app2" in data["sources"]


# === Security: Input Validation ===

def test_ingest_lines_not_array(client):
    resp = client.post("/api/ingest", json={"source": "test", "lines": "not-an-array"})
    assert resp.status_code == 400
    assert "array" in resp.get_json()["error"]


def test_ingest_line_not_string(client):
    resp = client.post("/api/ingest", json={"source": "test", "lines": [123, 456]})
    assert resp.status_code == 400
    assert "string" in resp.get_json()["error"]


def test_ingest_source_sanitized(client):
    resp = client.post(
        "/api/ingest",
        json={"source": "<script>alert(1)</script>", "lines": ["test"]},
    )
    assert resp.status_code == 200
    # Source should be sanitized to "api" since it contains invalid chars
    events = client.get("/api/events").get_json()
    assert events["events"][0]["source"] == "api"


def test_offset_validation(client):
    """Negative offset should be clamped to 0."""
    resp = client.get("/api/events?offset=-100")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["offset"] == 0


def test_limit_validation(client):
    """Limit > 1000 should be clamped to 1000."""
    resp = client.get("/api/events?limit=99999")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["limit"] == 1000


def test_invalid_limit_string(client):
    """Non-numeric limit should default to 100."""
    resp = client.get("/api/events?limit=abc")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["limit"] == 100


# === Security: Headers ===

def test_security_headers(client):
    resp = client.get("/healthz")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert resp.headers.get("Cache-Control") == "no-store"


# === Security: Path Traversal ===

def test_file_ingest_path_traversal(client):
    """Ingesting /etc/passwd via file path should be blocked."""
    resp = client.post("/api/ingest", json={"source": "test", "file": "/etc/passwd"})
    assert resp.status_code == 403


def test_file_ingest_relative_traversal(client):
    """Relative path traversal should be blocked."""
    resp = client.post("/api/ingest", json={"source": "test", "file": "/var/log/../../../etc/passwd"})
    assert resp.status_code == 403


# === Security: SSRF ===

def test_url_ingest_ssrf_localhost(client):
    """Ingesting from localhost should be blocked."""
    resp = client.post("/api/ingest", json={"source": "test", "url": "http://localhost:6379/"})
    assert resp.status_code == 403


def test_url_ingest_ssrf_internal(client):
    """Ingesting from internal IPs should be blocked."""
    resp = client.post("/api/ingest", json={"source": "test", "url": "http://169.254.169.254/latest/meta-data"})
    assert resp.status_code == 403


# === Security: API Key Auth ===

def test_api_key_healthz_no_auth(auth_client):
    """Healthz should work without API key even when auth is enabled."""
    resp = auth_client.get("/healthz")
    assert resp.status_code == 200


def test_api_key_required(auth_client):
    """Endpoints should require API key when configured."""
    resp = auth_client.get("/api/events")
    assert resp.status_code == 401


def test_api_key_wrong_key(auth_client):
    """Wrong API key should be rejected."""
    resp = auth_client.get("/api/events", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_api_key_correct(auth_client):
    """Correct API key should grant access."""
    resp = auth_client.get("/api/events", headers={"X-API-Key": "test-secret-key-123"})
    assert resp.status_code == 200


def test_api_key_ingest(auth_client):
    """Ingest should work with correct API key."""
    resp = auth_client.post(
        "/api/ingest",
        json={"source": "test", "lines": ["hello"]},
        headers={"X-API-Key": "test-secret-key-123"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 1


# === Pagination ===

def test_pagination(client):
    """Test pagination with limit and offset."""
    lines = [f'{{"message":"event{i}"}}' for i in range(25)]
    client.post("/api/ingest", json={"source": "paging", "lines": lines})

    # Page 1
    resp = client.get("/api/events?limit=10&offset=0")
    data = resp.get_json()
    assert len(data["events"]) == 10
    assert data["total"] == 25

    # Page 2
    resp = client.get("/api/events?limit=10&offset=10")
    data = resp.get_json()
    assert len(data["events"]) == 10

    # Page 3 (partial)
    resp = client.get("/api/events?limit=10&offset=20")
    data = resp.get_json()
    assert len(data["events"]) == 5
