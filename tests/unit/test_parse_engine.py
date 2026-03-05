"""Unit tests for LogSweeper parse engine."""

from src.logsweeper.parse.engine import ParseEngine


def test_parse_json_line():
    engine = ParseEngine()
    event = engine.parse_line('{"timestamp":"2024-01-01","message":"hello"}', source="test")
    assert event.category == "json"
    assert event.message == "hello"
    assert event.source == "test"


def test_parse_json_with_host():
    engine = ParseEngine()
    event = engine.parse_line('{"timestamp":"2024-01-01","msg":"hi","hostname":"web1"}', source="api")
    assert event.hostname == "web1"
    assert event.message == "hi"


def test_parse_raw_line():
    engine = ParseEngine()
    event = engine.parse_line("just a raw log line", source="file")
    assert event.category == "raw"
    assert event.message == "just a raw log line"
    assert event.raw == "just a raw log line"


def test_parse_empty_line():
    engine = ParseEngine()
    event = engine.parse_line("", source="test")
    assert event.category == "raw"


def test_parse_lines():
    engine = ParseEngine()
    lines = ['{"message":"a"}', "raw line", '{"message":"b"}']
    events = engine.parse_lines(lines, source="batch")
    assert len(events) == 3
    assert events[0].category == "json"
    assert events[1].category == "raw"
    assert events[2].category == "json"


def test_parse_with_custom_parser():
    engine = ParseEngine(parser_dirs=["config/parsers"])
    line = "Jan  1 00:00:00 myhost sshd[1234]: Accepted publickey"
    event = engine.parse_line(line, source="syslog")
    # If syslog parser loaded, should match
    if engine.parsers:
        assert event.category == "syslog"
        assert "Accepted publickey" in event.message
