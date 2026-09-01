#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    echo "ERROR: .venv does not exist."
    echo "Run ./scripts/setup.sh first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "ERROR: .env does not exist."
    echo "Run ./scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate

set -a
# shellcheck disable=SC1091
source .env
set +a

mkdir -p data

PORT="${PORT:-8000}"

echo "Starting Agentic-Nexus API"
echo "http://127.0.0.1:${PORT}"
echo "Swagger: http://127.0.0.1:${PORT}/docs"

exec uvicorn \
    backend.api:app \
    --host 127.0.0.1 \
    --port "$PORT"
