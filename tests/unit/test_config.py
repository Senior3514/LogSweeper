"""Unit tests for configuration loading."""

import os
import tempfile

from src.logsweeper.core.config import load_config


def test_default_config():
    config = load_config()
    assert config["port"] == 8093
    assert config["host"] == "0.0.0.0"
    assert config["db_path"] is not None


def test_config_from_yaml():
    content = """
logsweeper:
  host: "127.0.0.1"
  port: 9090
  log_level: DEBUG
"""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.write(fd, content.encode())
    os.close(fd)

    config = load_config(path)
    assert config["port"] == 9090
    assert config["log_level"] == "DEBUG"
    os.unlink(path)


def test_env_override(monkeypatch):
    monkeypatch.setenv("LOGSWEEPER_PORT", "7777")
    config = load_config()
    assert config["port"] == 7777
