"""File-based log ingestion for LogSweeper."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Allowed base directories for file ingestion (configurable via set_allowed_paths)
_allowed_paths: list[Path] = [Path("/var/log")]

# Maximum file size to ingest (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def set_allowed_paths(paths: list[str]) -> None:
    """Configure which directories are allowed for file ingestion."""
    global _allowed_paths
    _allowed_paths = [Path(p).resolve() for p in paths]


def _is_path_allowed(path: Path) -> bool:
    """Check if a file path falls within allowed directories."""
    resolved = path.resolve()
    return any(resolved.is_relative_to(allowed) for allowed in _allowed_paths)


def read_file(path: str) -> list[str]:
    """Read all lines from a log file with path traversal protection."""
    p = Path(path).resolve()

    if not _is_path_allowed(p):
        logger.warning("Blocked file access outside allowed paths: %s", path)
        raise PermissionError("File path not within allowed directories")

    if not p.exists():
        logger.error("File not found: %s", path)
        return []
    if not p.is_file():
        logger.error("Not a file: %s", path)
        return []

    if p.stat().st_size > MAX_FILE_SIZE:
        logger.error("File too large (max %d bytes): %s", MAX_FILE_SIZE, path)
        raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE} bytes")

    with open(p) as f:
        return f.readlines()


def tail_file(path: str, num_lines: int = 100) -> list[str]:
    """Read the last N lines from a file with path traversal protection."""
    p = Path(path).resolve()

    if not _is_path_allowed(p):
        logger.warning("Blocked file access outside allowed paths: %s", path)
        raise PermissionError("File path not within allowed directories")

    if not p.exists():
        return []
    with open(p) as f:
        lines = f.readlines()
    return lines[-num_lines:]
