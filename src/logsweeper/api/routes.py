"""API routes for LogSweeper."""

import logging
import time
from collections import defaultdict

from flask import Flask, request, jsonify

from ..storage.db import Database
from ..parse.engine import ParseEngine
from ..ingest.file_ingest import read_file
from ..ingest.http_pull import pull_logs

logger = logging.getLogger(__name__)

# Fields that should never appear in log output
REDACTED_FIELDS = {"password", "secret", "token", "api_key", "authorization"}

# Input limits
MAX_LINES_PER_REQUEST = 10_000
MAX_LINE_LENGTH = 65_536
MAX_SOURCE_LENGTH = 256

# Rate limiting: requests per window
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120  # requests per window
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _redact(data: dict) -> dict:
    """Redact sensitive fields from data before logging."""
    return {k: "***REDACTED***" if k.lower() in REDACTED_FIELDS else v for k, v in data.items()}


def _get_client_ip() -> str:
    """Get client IP, respecting X-Forwarded-For behind reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _check_rate_limit() -> bool:
    """Return True if request should be rate-limited."""
    client_ip = _get_client_ip()
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_buckets[client_ip] = [t for t in _rate_buckets[client_ip] if t > window_start]
    _rate_buckets[client_ip].append(now)

    return len(_rate_buckets[client_ip]) > RATE_LIMIT_MAX


def _validate_source(source: str) -> str:
    """Validate and sanitize the source field."""
    source = source.strip()[:MAX_SOURCE_LENGTH]
    if not all(c.isalnum() or c in "-_." for c in source):
        return "api"
    return source or "api"


def register_routes(app: Flask):
    """Register all API routes on the Flask app."""

    def _db() -> Database:
        return app.config["db"]

    def _engine() -> ParseEngine:
        return app.config["parse_engine"]

    @app.after_request
    def _security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        return response

    @app.before_request
    def _rate_limiter():
        if _check_rate_limit():
            logger.warning("Rate limit exceeded for %s", _get_client_ip())
            return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    @app.before_request
    def _check_api_key():
        """Optional API key authentication. If LOGSWEEPER_API_KEY is set, require it."""
        api_key = app.config.get("API_KEY")
        if not api_key:
            return  # No API key configured, skip auth

        # Allow health check without auth
        if request.path == "/healthz":
            return

        provided_key = request.headers.get("X-API-Key", "")
        if provided_key != api_key:
            return jsonify({"error": "Invalid or missing API key"}), 401

    @app.route("/healthz", methods=["GET"])
    def healthz():
        db = _db()
        try:
            count = db.count_events()
            return jsonify({"status": "ok", "version": "0.1.0", "events_count": count})
        except Exception:
            return jsonify({"status": "ok", "version": "0.1.0"})

    @app.route("/api/ingest", methods=["POST"])
    def ingest():
        """Ingest log lines. Accepts JSON body with 'lines' array or 'file' path or 'url'."""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({"error": "JSON object body required"}), 400

        logger.info("Ingest request from %s: %s", _get_client_ip(), _redact(data))

        engine = _engine()
        db = _db()
        source = _validate_source(data.get("source", "api"))
        lines = []

        if "lines" in data:
            raw_lines = data["lines"]
            if not isinstance(raw_lines, list):
                return jsonify({"error": "'lines' must be an array"}), 400
            if len(raw_lines) > MAX_LINES_PER_REQUEST:
                return jsonify({"error": f"Too many lines (max {MAX_LINES_PER_REQUEST})"}), 400
            for line in raw_lines:
                if not isinstance(line, str):
                    return jsonify({"error": "Each line must be a string"}), 400
            lines = [line[:MAX_LINE_LENGTH] for line in raw_lines]

        elif "file" in data:
            file_path = data["file"]
            if not isinstance(file_path, str) or len(file_path) > 1024:
                return jsonify({"error": "Invalid file path"}), 400
            try:
                lines = read_file(file_path)
            except PermissionError as e:
                return jsonify({"error": str(e)}), 403
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        elif "url" in data:
            url = data["url"]
            if not isinstance(url, str) or len(url) > 2048:
                return jsonify({"error": "Invalid URL"}), 400
            try:
                lines = pull_logs(url)
            except PermissionError as e:
                return jsonify({"error": str(e)}), 403

        else:
            return jsonify({"error": "Provide 'lines', 'file', or 'url'"}), 400

        events = engine.parse_lines(lines, source=source)
        if events:
            db.insert_events(events)

        return jsonify({"status": "ingested", "count": len(events)})

    @app.route("/api/events", methods=["GET"])
    def events():
        """Query events with optional filters."""
        db = _db()
        source = request.args.get("source", "")[:MAX_SOURCE_LENGTH] or None
        category = request.args.get("category", "")[:MAX_SOURCE_LENGTH] or None
        search = request.args.get("search", "")[:512] or None

        try:
            limit = max(1, min(int(request.args.get("limit", 100)), 1000))
        except (ValueError, TypeError):
            limit = 100

        try:
            offset = max(0, int(request.args.get("offset", 0)))
        except (ValueError, TypeError):
            offset = 0

        rows = db.query_events(source=source, category=category, search=search, limit=limit, offset=offset)
        total = db.count_events(source=source, category=category, search=search)

        return jsonify({"events": rows, "total": total, "limit": limit, "offset": offset})

    @app.route("/api/events/<int:event_id>", methods=["GET"])
    def event_detail(event_id: int):
        """Get a single event by ID."""
        if event_id < 1:
            return jsonify({"error": "Invalid event ID"}), 400
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

    @app.route("/api/stats", methods=["GET"])
    def stats():
        """Return aggregated statistics."""
        db = _db()
        total = db.count_events()
        sources = db.get_sources()
        categories = db.get_categories()
        return jsonify({
            "total_events": total,
            "source_count": len(sources),
            "category_count": len(categories),
            "sources": sources,
            "categories": categories,
        })
