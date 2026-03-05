"""API routes for LogSweeper."""

import logging

from flask import Flask, request, jsonify

from ..storage.db import Database
from ..parse.engine import ParseEngine
from ..ingest.file_ingest import read_file
from ..ingest.http_pull import pull_logs

logger = logging.getLogger(__name__)

# Fields that should never appear in log output
REDACTED_FIELDS = {"password", "secret", "token", "api_key", "authorization"}


def _redact(data: dict) -> dict:
    """Redact sensitive fields from data before logging."""
    return {k: "***REDACTED***" if k.lower() in REDACTED_FIELDS else v for k, v in data.items()}


def register_routes(app: Flask):
    """Register all API routes on the Flask app."""

    def _db() -> Database:
        return app.config["db"]

    def _engine() -> ParseEngine:
        return app.config["parse_engine"]

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return jsonify({"status": "ok", "version": "0.1.0"})

    @app.route("/api/ingest", methods=["POST"])
    def ingest():
        """Ingest log lines. Accepts JSON body with 'lines' array or 'file' path or 'url'."""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        logger.info("Ingest request: %s", _redact(data))

        engine = _engine()
        db = _db()
        source = data.get("source", "api")
        lines = []

        if "lines" in data:
            lines = data["lines"]
        elif "file" in data:
            lines = read_file(data["file"])
        elif "url" in data:
            lines = pull_logs(data["url"])
        else:
            return jsonify({"error": "Provide 'lines', 'file', or 'url'"}), 400

        events = engine.parse_lines(lines, source=source)
        count = 0
        for event in events:
            db.insert_event(event)
            count += 1

        return jsonify({"status": "ingested", "count": count})

    @app.route("/api/events", methods=["GET"])
    def events():
        """Query events with optional filters."""
        db = _db()
        source = request.args.get("source")
        category = request.args.get("category")
        search = request.args.get("search")
        limit = min(int(request.args.get("limit", 100)), 1000)
        offset = int(request.args.get("offset", 0))

        rows = db.query_events(source=source, category=category, search=search, limit=limit, offset=offset)
        total = db.count_events(source=source, category=category, search=search)

        return jsonify({"events": rows, "total": total, "limit": limit, "offset": offset})

    @app.route("/api/events/<int:event_id>", methods=["GET"])
    def event_detail(event_id: int):
        """Get a single event by ID."""
        db = _db()
        event = db.get_event(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404
        return jsonify(event)

    @app.route("/api/sources", methods=["GET"])
    def sources():
        return jsonify({"sources": _db().get_sources()})

    @app.route("/api/categories", methods=["GET"])
    def categories():
        return jsonify({"categories": _db().get_categories()})
