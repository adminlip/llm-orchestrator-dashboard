#!/usr/bin/env bash
set -euo pipefail

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"
APP_URL="http://127.0.0.1:${APP_PORT}"

echo "=== LLM Orchestrator Dashboard ==="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3 not found. Please install Python 3.10+ first."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

if [ ! -f ".venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo ok > ".venv/.deps_installed"
else
    echo "Dependencies already installed."
fi

echo
echo "Checking runtime mode..."
if [ -f ".env" ] && grep -q "OPENAI_API_KEY=your-openai-compatible-key" ".env"; then
    echo "Mode: Mock mode. Edit .env to enable real model calls."
else
    echo "Mode: Real API mode if valid API keys are configured."
fi

echo
echo "Starting server at ${APP_URL}"
echo "Press Ctrl+C to stop."
echo

uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}" --reload
