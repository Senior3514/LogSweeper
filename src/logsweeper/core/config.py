"""Configuration loader for LogSweeper."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config(config_path: str | None = None) -> dict:
    """Load configuration from YAML file with env overrides."""
    defaults = {
        "host": "0.0.0.0",
        "port": 8080,
        "log_level": "INFO",
        "db_path": "logsweeper.db",
        "secret_key": "change-me-in-production",
    }

    config = dict(defaults)

    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        if "logsweeper" in file_config:
            config.update(file_config["logsweeper"])
        if "storage" in file_config:
            config["storage"] = file_config["storage"]
        if "parsers" in file_config:
            config["parsers"] = file_config["parsers"]
        if "security" in file_config:
            config["security"] = file_config["security"]
        if "ingestion" in file_config:
            config["ingestion"] = file_config["ingestion"]

    # Env overrides
    config["host"] = os.getenv("LOGSWEEPER_HOST", config.get("host", defaults["host"]))
    config["port"] = int(os.getenv("LOGSWEEPER_PORT", config.get("port", defaults["port"])))
    config["log_level"] = os.getenv("LOGSWEEPER_LOG_LEVEL", config.get("log_level", defaults["log_level"]))
    config["db_path"] = os.getenv("LOGSWEEPER_DB_PATH", config.get("db_path", defaults["db_path"]))
    config["secret_key"] = os.getenv("LOGSWEEPER_SECRET_KEY", config.get("secret_key", defaults["secret_key"]))

    return config
