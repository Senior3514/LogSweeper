"""Unit tests for LogSweeper models."""

from src.logsweeper.storage.models import Event


def test_event_creation():
    event = Event(
        id=None,
        timestamp="2024-01-01T00:00:00",
        source="test",
        hostname="localhost",
        category="json",
        message="test message",
        raw='{"message": "test message"}',
    )
    assert event.source == "test"
    assert event.message == "test message"
    assert event.id is None


def test_event_to_dict():
    event = Event(
        id=1,
        timestamp="2024-01-01T00:00:00",
        source="test",
        hostname="localhost",
        category="json",
        message="hello",
        raw="hello",
    )
    d = event.to_dict()
    assert d["id"] == 1
    assert d["source"] == "test"


def test_event_to_dict_no_id():
    event = Event(
        id=None,
        timestamp="2024-01-01T00:00:00",
        source="test",
        hostname="",
        category="raw",
        message="line",
        raw="line",
    )
    d = event.to_dict()
    assert "id" not in d
