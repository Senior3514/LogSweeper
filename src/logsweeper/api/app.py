"""Flask application factory for LogSweeper."""

import logging
import os
import secrets

from flask import Flask
from flask_cors import CORS

from ..core.config import load_config
from ..storage.db import Database
from ..parse.engine import ParseEngine
from ..ingest.file_ingest import set_allowed_paths


def create_app(config_path: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    config = load_config(config_path)

    logging.basicConfig(
        level=getattr(logging, config.get("log_level", "INFO")),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = Flask(__name__)

    # Secret key: use config value, but warn if it's the insecure default
    secret = config["secret_key"]
    if secret == "change-me-in-production":
        secret = secrets.token_hex(32)
        logging.getLogger(__name__).warning(
            "Using auto-generated secret key. Set LOGSWEEPER_SECRET_KEY for persistence."
        )
    app.config["SECRET_KEY"] = secret

    # Optional API key authentication
    api_key = os.getenv("LOGSWEEPER_API_KEY", "")
    if api_key:
        app.config["API_KEY"] = api_key

    # Max request size: 16 MB
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # CORS - default to localhost only, not wildcard
    security_config = config.get("security", {})
    allowed_origins = security_config.get("allowed_origins", ["http://localhost:3000"])
    CORS(app, origins=allowed_origins)

    # Configure allowed file paths for ingestion
    ingestion_config = config.get("ingestion", {})
    watch_paths = ingestion_config.get("watch_paths", ["/var/log"])
    set_allowed_paths(watch_paths)

    # Initialize database
    db = Database(config["db_path"])
    app.config["db"] = db

    # Initialize parse engine
    parser_dirs = []
    if "parsers" in config:
        custom_dir = config["parsers"].get("custom_dir")
        if custom_dir:
            parser_dirs.append(custom_dir)
    engine = ParseEngine(parser_dirs=parser_dirs)
    app.config["parse_engine"] = engine

    # Register routes
    from .routes import register_routes
    register_routes(app)

    return app
