"""Unit tests for file ingestion with security checks."""

import os
import tempfile

import pytest

from src.logsweeper.ingest.file_ingest import read_file, tail_file, set_allowed_paths


@pytest.fixture(autouse=True)
def _allow_tmp():
    """Allow reading from temp dir for tests."""
    set_allowed_paths([tempfile.gettempdir()])
    yield
    set_allowed_paths(["/var/log"])


def test_read_file():
    fd, path = tempfile.mkstemp(suffix=".log")
    os.write(fd, b"line1\nline2\nline3\n")
    os.close(fd)

    lines = read_file(path)
    assert len(lines) == 3
    assert "line1\n" in lines
    os.unlink(path)


def test_read_file_not_found():
    lines = read_file("/tmp/nonexistent_log_file.log")
    assert lines == []


def test_tail_file():
    fd, path = tempfile.mkstemp(suffix=".log")
    content = "".join(f"line{i}\n" for i in range(200))
    os.write(fd, content.encode())
    os.close(fd)

    lines = tail_file(path, num_lines=10)
    assert len(lines) == 10
    assert "line199\n" in lines
    os.unlink(path)


def test_path_traversal_blocked():
    """Attempting to read /etc/passwd should be blocked."""
    set_allowed_paths(["/var/log"])
    with pytest.raises(PermissionError, match="not within allowed directories"):
        read_file("/etc/passwd")


def test_path_traversal_relative_blocked():
    """Relative path traversal like ../../../etc/passwd should be blocked."""
    set_allowed_paths(["/var/log"])
    with pytest.raises(PermissionError, match="not within allowed directories"):
        read_file("/var/log/../../../etc/passwd")


def test_tail_file_traversal_blocked():
    """Tail should also enforce path restrictions."""
    set_allowed_paths(["/var/log"])
    with pytest.raises(PermissionError, match="not within allowed directories"):
        tail_file("/etc/shadow")


def test_allowed_paths_configurable():
    """set_allowed_paths should update the allowed list."""
    fd, path = tempfile.mkstemp(suffix=".log")
    os.write(fd, b"test\n")
    os.close(fd)

    set_allowed_paths([tempfile.gettempdir()])
    lines = read_file(path)
    assert len(lines) == 1
    os.unlink(path)
