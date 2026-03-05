"""Unit tests for LogSweeper database."""

import os
import tempfile

import pytest

from src.logsweeper.storage.db import Database
from src.logsweeper.storage.models import Event


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(path)
    yield database
    os.unlink(path)


def test_insert_and_query(db):
    event = Event(
        id=None,
        timestamp="2024-01-01T00:00:00",
        source="test",
        hostname="localhost",
        category="json",
        message="hello world",
        raw='{"message":"hello world"}',
    )
    event_id = db.insert_event(event)
    assert event_id >= 1

    results = db.query_events()
    assert len(results) == 1
    assert results[0]["message"] == "hello world"


def test_query_by_source(db):
    for src in ["web", "web", "cli"]:
        db.insert_event(Event(None, "2024-01-01", src, "", "raw", "msg", "msg"))

    web_events = db.query_events(source="web")
    assert len(web_events) == 2

    cli_events = db.query_events(source="cli")
    assert len(cli_events) == 1


def test_search(db):
    db.insert_event(Event(None, "2024-01-01", "test", "", "raw", "error in auth", "error in auth"))
    db.insert_event(Event(None, "2024-01-01", "test", "", "raw", "all good", "all good"))

    results = db.query_events(search="error")
    assert len(results) == 1
    assert "error" in results[0]["message"]


def test_count(db):
    for i in range(5):
        db.insert_event(Event(None, "2024-01-01", "test", "", "raw", f"msg {i}", f"msg {i}"))
    assert db.count_events() == 5
    assert db.count_events(source="test") == 5
    assert db.count_events(source="other") == 0


def test_get_event(db):
    eid = db.insert_event(Event(None, "2024-01-01", "test", "", "raw", "hello", "hello"))
    result = db.get_event(eid)
    assert result is not None
    assert result["message"] == "hello"
    assert db.get_event(9999) is None


def test_get_sources_and_categories(db):
    db.insert_event(Event(None, "2024-01-01", "web", "", "json", "a", "a"))
    db.insert_event(Event(None, "2024-01-01", "cli", "", "raw", "b", "b"))

    sources = db.get_sources()
    assert "web" in sources
    assert "cli" in sources

    categories = db.get_categories()
    assert "json" in categories
    assert "raw" in categories


def test_insert_events_batch(db):
    events = [Event(None, "2024-01-01", "batch", "", "raw", f"msg {i}", f"msg {i}") for i in range(10)]
    count = db.insert_events(events)
    assert count == 10
    assert db.count_events() == 10
