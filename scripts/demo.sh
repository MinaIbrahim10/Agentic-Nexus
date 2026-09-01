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

PORT="${PORT:-8000}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"

echo "=== Agentic-Nexus 5-minute demo ==="

echo
echo "1. Health"

curl -fsS \
    "${BASE_URL}/health"

echo
echo


echo "2. Seed reproducible demo data"

./scripts/seed_demo.sh


echo
echo "3. Authenticate"

LOGIN_JSON="$(
    curl -fsS \
        -X POST \
        "${BASE_URL}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
          "email":"demo@example.com",
          "password":"DemoPass123!"
        }'
)"

TOKEN="$(
    printf '%s' "$LOGIN_JSON" |
    python -c \
        'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

test -n "$TOKEN"

echo "Authentication: PASS"


echo
echo "4. Protected API + persistent query record"

curl -fsS \
    -X POST \
    "${BASE_URL}/api/v1/queries" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "query":"Explain Corrective RAG"
    }'

echo
echo


echo "5. Background ingestion job"

INGEST_JSON="$(
    curl -fsS \
        -X POST \
        "${BASE_URL}/api/v1/ingest" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
          "title":"Demo Background Job",
          "content":"This document demonstrates authenticated persistent background ingestion in Agentic-Nexus."
        }'
)"

printf '%s\n' "$INGEST_JSON"

JOB_ID="$(
    printf '%s' "$INGEST_JSON" |
    python -c \
        'import json,sys; print(json.load(sys.stdin)["id"])'
)"

sleep 1

echo
echo "Job status:"

curl -fsS \
    "${BASE_URL}/api/v1/jobs/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}"

echo
echo


echo "6. Real local Ollama LLM call"

curl -fsS \
    -X POST \
    "${BASE_URL}/api/v1/ai/answer" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "prompt":"In one short sentence, explain Retrieval-Augmented Generation."
    }'

echo
echo


echo "7. Persisted local-AI usage log"

curl -fsS \
    "${BASE_URL}/api/v1/usage" \
    -H "Authorization: Bearer ${TOKEN}"

echo
echo
echo "5-MINUTE DEMO: PASS"
