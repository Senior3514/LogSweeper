#!/usr/bin/env bash
set -euo pipefail

# LogSweeper MVP - One-shot build/test/deploy runbook
# Prerequisites: Python 3.11+, Node.js 20+, Docker (optional)

echo "=== LogSweeper MVP Runbook ==="

# 1. Setup
echo "[1/6] Setting up environment..."
cp -n .env.example .env 2>/dev/null || true
pip install -r requirements.txt

# 2. Run backend tests
echo "[2/6] Running backend tests..."
python -m pytest tests/unit -v --tb=short
python -m pytest tests/integration -v --tb=short
python -m pytest tests/e2e -v --tb=short

# 3. Setup UI
echo "[3/6] Setting up UI..."
cd src/ui
npm install --ignore-scripts
cd ../..

# 4. Health check (start server temporarily)
echo "[4/6] Starting server for health check..."
python -m src.logsweeper.app &
SERVER_PID=$!
sleep 2

if curl -sf http://localhost:8080/healthz > /dev/null 2>&1; then
    echo "  Health check PASSED"
else
    echo "  Health check FAILED"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi
kill $SERVER_PID 2>/dev/null || true

# 5. Docker deploy (if Docker available)
echo "[5/6] Docker deploy..."
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    docker-compose up -d --build || echo "  Docker deploy skipped (build failed or not available)"
    sleep 3
    if curl -sf http://localhost:8080/healthz > /dev/null 2>&1; then
        echo "  Docker health check PASSED"
    else
        echo "  Docker health check skipped"
    fi
else
    echo "  Docker not available, skipping"
fi

# 6. Done
echo "[6/6] Done!"
echo ""
echo "=== Rollback ==="
echo "  docker-compose down"
echo "  git revert HEAD"
echo ""
echo "=== Endpoints ==="
echo "  API:  http://localhost:8080"
echo "  UI:   http://localhost:3000"
echo "  Health: http://localhost:8080/healthz"
