"""Unit tests for file ingestion."""

import os
import tempfile

from src.logsweeper.ingest.file_ingest import read_file, tail_file


def test_read_file():
    fd, path = tempfile.mkstemp()
    os.write(fd, b"line1\nline2\nline3\n")
    os.close(fd)

    lines = read_file(path)
    assert len(lines) == 3
    assert "line1" in lines[0]
    os.unlink(path)


def test_read_file_not_found():
    lines = read_file("/nonexistent/path/file.log")
    assert lines == []


def test_tail_file():
    fd, path = tempfile.mkstemp()
    for i in range(200):
        os.write(fd, f"line {i}\n".encode())
    os.close(fd)

    lines = tail_file(path, num_lines=10)
    assert len(lines) == 10
    assert "190" in lines[0]
    os.unlink(path)
