#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ] || [ ! -f .env ]; then
    echo "ERROR: run ./scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate

set -a
# shellcheck disable=SC1091
source .env
set +a

python scripts/seed_demo.py
