"""Pluggable log parsing engine for LogSweeper."""

import json
import re
import logging
from datetime import datetime
from pathlib import Path

import yaml

from ..storage.models import Event

logger = logging.getLogger(__name__)


class ParserDefinition:
    """A parser loaded from YAML config."""

    def __init__(self, name: str, pattern: str, fields: list[dict]):
        self.name = name
        self.pattern = re.compile(pattern)
        self.fields = fields

    def match(self, line: str) -> dict | None:
        m = self.pattern.match(line)
        if m:
            return m.groupdict()
        return None


class ParseEngine:
    """Pluggable parsing engine supporting JSON, syslog, and custom YAML parsers."""

    def __init__(self, parser_dirs: list[str] | None = None):
        self.parsers: list[ParserDefinition] = []
        if parser_dirs:
            for d in parser_dirs:
                self._load_parsers_from_dir(d)

    def _load_parsers_from_dir(self, directory: str):
        path = Path(directory)
        if not path.exists():
            logger.warning("Parser directory not found: %s", directory)
            return
        for f in path.glob("*.yaml"):
            try:
                with open(f) as fh:
                    defn = yaml.safe_load(fh)
                parser = ParserDefinition(
                    name=defn["name"],
                    pattern=defn["pattern"],
                    fields=defn.get("fields", []),
                )
                self.parsers.append(parser)
                logger.info("Loaded parser: %s", defn["name"])
            except Exception as e:
                logger.error("Failed to load parser %s: %s", f, e)

    def parse_line(self, line: str, source: str = "") -> Event:
        """Parse a single log line, trying JSON first, then custom parsers, then raw."""
        line = line.strip()
        if not line:
            return self._raw_event(line, source)

        # Try JSON
        event = self._try_json(line, source)
        if event:
            return event

        # Try custom YAML-defined parsers
        for parser in self.parsers:
            matched = parser.match(line)
            if matched:
                return Event(
                    id=None,
                    timestamp=matched.get("timestamp", datetime.now().isoformat()),
                    source=source,
                    hostname=matched.get("hostname", ""),
                    category=parser.name,
                    message=matched.get("message", line),
                    raw=line,
                )

        return self._raw_event(line, source)

    def _try_json(self, line: str, source: str) -> Event | None:
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                return Event(
                    id=None,
                    timestamp=data.get("timestamp", data.get("time", data.get("ts", datetime.now().isoformat()))),
                    source=source,
                    hostname=data.get("hostname", data.get("host", "")),
                    category="json",
                    message=data.get("message", data.get("msg", str(data))),
                    raw=line,
                )
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _raw_event(self, line: str, source: str) -> Event:
        return Event(
            id=None,
            timestamp=datetime.now().isoformat(),
            source=source,
            hostname="",
            category="raw",
            message=line,
            raw=line,
        )

    def parse_lines(self, lines: list[str], source: str = "") -> list[Event]:
        return [self.parse_line(line, source) for line in lines if line.strip()]
