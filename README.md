# LogSweeper

Universal log parser and explorer. Ingest logs from files, syslog, or HTTP endpoints. Parse with pluggable YAML/JSON parser definitions. Store in SQLite (MVP) or Postgres. Explore via REST API and React dashboard.

## Architecture

```
src/
  logsweeper/          # Python backend
    api/               # Flask REST API (/healthz, /api/ingest, /api/events)
    core/              # Configuration loader
    ingest/            # File, syslog UDP, and HTTP pull connectors
    parse/             # Pluggable parsing engine (JSON, syslog, custom YAML)
    storage/           # SQLite database layer with models
  ui/                  # React/TypeScript dashboard
config/                # YAML config and parser definitions
tests/                 # Unit, integration, and e2e smoke tests
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (for UI)
- Docker (optional)

### Local Development

```bash
# Backend
cp .env.example .env
pip install -r requirements.txt
python -m src.logsweeper.app

# UI
cd src/ui
npm install
npm run dev
```

### Docker

```bash
docker-compose up -d --build
# API: http://localhost:8080
# UI:  http://localhost:3000
```

### Running Tests

```bash
# All Python tests
python -m pytest tests/ -v

# Unit only
python -m pytest tests/unit -v

# Integration
python -m pytest tests/integration -v

# E2E smoke
python -m pytest tests/e2e -v

# UI tests
cd src/ui && npm test
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| POST | `/api/ingest` | Ingest log lines |
| GET | `/api/events` | Query events (filters: source, category, search) |
| GET | `/api/events/:id` | Event detail |
| GET | `/api/sources` | List distinct sources |
| GET | `/api/categories` | List distinct categories |

### Ingest Examples

```bash
# Ingest raw lines
curl -X POST http://localhost:8080/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"source": "myapp", "lines": ["{\"message\":\"hello\"}", "raw log line"]}'

# Ingest from file
curl -X POST http://localhost:8080/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"source": "syslog", "file": "/var/log/syslog"}'
```

## Security

- Secrets via environment variables only (never in code)
- CORS with configurable allowed origins
- Sensitive fields redacted in API logs
- CSRF and secure cookie scaffolding in config

## License

MIT
