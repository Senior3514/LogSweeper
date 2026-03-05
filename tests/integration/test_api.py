"""Integration tests for the LogSweeper API."""

import json
import os
import tempfile

import pytest

from src.logsweeper.api.app import create_app


@pytest.fixture
def client():
    os.environ["LOGSWEEPER_DB_PATH"] = tempfile.mktemp(suffix=".db")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if os.path.exists(os.environ["LOGSWEEPER_DB_PATH"]):
        os.unlink(os.environ["LOGSWEEPER_DB_PATH"])


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "version" in data


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
