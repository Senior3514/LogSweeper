"""Unit tests for HTTP pull connector with SSRF prevention."""

import pytest

from src.logsweeper.ingest.http_pull import _is_url_safe, pull_logs


def test_blocks_localhost():
    assert _is_url_safe("http://localhost/logs") is False


def test_blocks_127():
    assert _is_url_safe("http://127.0.0.1/logs") is False


def test_blocks_private_10():
    assert _is_url_safe("http://10.0.0.1/logs") is False


def test_blocks_private_172():
    assert _is_url_safe("http://172.16.0.1/logs") is False


def test_blocks_private_192():
    assert _is_url_safe("http://192.168.1.1/logs") is False


def test_blocks_metadata_aws():
    assert _is_url_safe("http://169.254.169.254/latest/meta-data") is False


def test_blocks_metadata_gcp():
    assert _is_url_safe("http://metadata.google.internal/") is False


def test_blocks_ftp_scheme():
    assert _is_url_safe("ftp://example.com/file") is False


def test_blocks_file_scheme():
    assert _is_url_safe("file:///etc/passwd") is False


def test_blocks_empty_url():
    assert _is_url_safe("") is False


def test_pull_logs_ssrf_raises():
    with pytest.raises(PermissionError, match="blocked internal network"):
        pull_logs("http://127.0.0.1:6379/")


def test_pull_logs_localhost_raises():
    with pytest.raises(PermissionError, match="blocked internal network"):
        pull_logs("http://localhost/admin")
