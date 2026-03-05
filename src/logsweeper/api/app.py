"""Flask application factory for LogSweeper."""

import logging

from flask import Flask
from flask_cors import CORS

from ..core.config import load_config
from ..storage.db import Database
from ..parse.engine import ParseEngine


def create_app(config_path: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    config = load_config(config_path)

    logging.basicConfig(
        level=getattr(logging, config.get("log_level", "INFO")),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config["secret_key"]

    # CORS
    allowed_origins = config.get("security", {}).get("allowed_origins", ["*"])
    CORS(app, origins=allowed_origins)

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
