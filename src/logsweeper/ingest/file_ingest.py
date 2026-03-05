"""File-based log ingestion for LogSweeper."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_file(path: str) -> list[str]:
    """Read all lines from a log file."""
    p = Path(path)
    if not p.exists():
        logger.error("File not found: %s", path)
        return []
    if not p.is_file():
        logger.error("Not a file: %s", path)
        return []
    with open(p) as f:
        return f.readlines()


def tail_file(path: str, num_lines: int = 100) -> list[str]:
    """Read the last N lines from a file."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        lines = f.readlines()
    return lines[-num_lines:]
