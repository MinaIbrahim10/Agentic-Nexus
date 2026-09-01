#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3.13}"

echo "=== Agentic-Nexus setup ==="

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python 3.13 is required."
    echo "Install Python 3.13 and rerun this script."
    exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
    echo "ERROR: Ollama is required."
    echo "Install Ollama, start it, and rerun this script."
    exit 1
fi

echo "Python:"
"$PYTHON_BIN" --version

if [ ! -d .venv ]; then
    echo "Creating .venv..."
    "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f .env ]; then
    echo "Creating local .env..."

    SECRET="$(
        python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
    )"

    cat > .env <<EOF
NEXUS_DB_PATH=data/agentic_nexus.duckdb
NEXUS_JWT_SECRET=${SECRET}
NEXUS_LLM_MODEL=gemma4:e4b-it
PORT=8000
EOF

    chmod 600 .env
fi

if ! curl -fsS \
    http://localhost:11434/api/tags \
    >/dev/null 2>&1
then
    echo
    echo "ERROR: Ollama is installed but its server is not running."
    echo "Start it with:"
    echo "  ollama serve"
    echo
    echo "Then rerun ./scripts/setup.sh"
    exit 1
fi

ensure_model() {
    local model="$1"

    if ollama show "$model" >/dev/null 2>&1; then
        echo "Ollama model present: $model"
    else
        echo "Downloading required Ollama model: $model"
        ollama pull "$model"
    fi
}

ensure_model "bge-m3:latest"
ensure_model "gemma4:e4b-it"

mkdir -p data

echo
echo "SETUP: PASS"
echo
echo "Next command:"
echo "  ./scripts/run_api.sh"
