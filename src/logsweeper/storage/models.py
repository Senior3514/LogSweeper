"""Data models for LogSweeper events."""

from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Event:
    """A parsed log event."""
    id: int | None
    timestamp: str
    source: str
    hostname: str
    category: str
    message: str
    raw: str
    created_at: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["id"] is None:
            del d["id"]
        return d
