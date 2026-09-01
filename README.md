# Agentic-Nexus

Agentic-Nexus is a local-first multi-agent AI backend that combines authenticated
HTTP APIs, persistent application data, background ingestion, local Ollama
inference, Hybrid RAG, Corrective RAG, a knowledge graph, and Cache-Augmented
Generation.

The capstone is intentionally backend-focused. No paid API or credit card is
required.

## Verified 10x Result

A benchmark of 10 repeated identical queries through the real Hybrid RAG path
measured:

| Metric | No cache reuse | CAG enabled |
|---|---:|---:|
| FAISS retrieval calls | 10 | 1 |
| Knowledge-graph lookups | 10 | 1 |
| Cross-Encoder reranking calls | 10 | 1 |
| Total retrieval-path latency | 1785.915 ms | 179.878 ms |

**Expensive retrieval-work reduction: 10.00x**

**Measured wall-clock speedup: 9.93x**

The 10x claim refers specifically to expensive retrieval-pipeline executions,
not to a guaranteed 10x latency improvement.

Recorded evidence:

- `evidence/cache_benchmark.json`
- `evidence/cache_benchmark.md`

## Program Concepts

All counted concepts come from the main program-concept list. No swaps are used.

| Concept | Implementation |
|---|---|
| API endpoints | `backend/api.py` — validated FastAPI routes and HTTP status codes |
| Database | `backend/db.py` — persistent DuckDB users, queries, jobs, documents, and usage |
| Authentication | `backend/auth.py` — JWT login and protected user-scoped routes |
| Background jobs | `backend/jobs.py` — persisted ingestion jobs executed after request acceptance |
| Caching logic | `rag_pipeline/query_cache.py` + `agents/hybrid_rag_agent.py` — bounded normalized query-result cache |
| LLM integration | `backend/ai_service.py` — authenticated local Ollama endpoint with token/cost logging |

## Architecture

The existing agentic pipeline adds:

- LangGraph orchestration;
- Pydantic-structured Manager routing;
- FAISS vector retrieval with Ollama `bge-m3` embeddings;
- NetworkX knowledge-graph retrieval;
- `BAAI/bge-reranker-large` Cross-Encoder scoring;
- Corrective RAG confidence decisions;
- web fallback for weak local retrieval;
- evaluator feedback with a bounded retry;
- CAG cache hits before vector/KG/reranking work.

The FastAPI capstone layer adds authentication, persistent operational data,
background ingestion, and a narrow local-LLM endpoint.

The background-ingestion demo persists submitted documents and job state. The
original Hybrid RAG demo corpus remains a separate built-in retrieval corpus.

## Requirements

A clean machine needs:

- Git
- Python 3.13
- Ollama
- enough local disk/RAM for the selected Ollama and Cross-Encoder models

No LangSmith account is required for the core capstone path.

## Clean Setup

Clone the repository, enter it, then run:

~~~bash
./scripts/setup.sh
~~~

The setup script:

- creates `.venv` with Python 3.13;
- installs `requirements.txt`;
- creates a local ignored `.env` with a random JWT secret;
- verifies Ollama;
- ensures `bge-m3:latest` and `gemma4:e4b-it` are available.

Then start the API with one command:

~~~bash
./scripts/run_api.sh
~~~

The API is available at:

- `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

So after cloning, the documented application setup/start path is two commands:
`./scripts/setup.sh` and `./scripts/run_api.sh`.

## Seed / Demo Data

In another terminal:

~~~bash
./scripts/seed_demo.sh
~~~

This idempotently creates:

- demo user: `demo@example.com`
- demo password: `DemoPass123!`
- one persisted demo knowledge document

These are local demonstration credentials, not production secrets.

## 5-Minute Demo Path

Keep the API running, then execute:

~~~bash
./scripts/demo.sh
~~~

The demo verifies, in order:

1. health endpoint;
2. reproducible seed data;
3. JWT login;
4. authenticated persistent query creation;
5. accepted background ingestion + persisted job status;
6. a real local Ollama response;
7. persisted local-AI usage/cost logging.

Expected final line:

    5-MINUTE DEMO: PASS

## Manual API Examples

Health:

~~~bash
curl http://127.0.0.1:8000/health
~~~

Interactive API documentation:

    http://127.0.0.1:8000/docs

## Testing

Backend and deterministic cache tests:

~~~bash
source .venv/bin/activate
python -m pytest -q
~~~

The LLM unit tests mock model execution for deterministic CI-style testing.
A separate real Ollama smoke test was performed during capstone verification.

## Local Configuration

`.env.example` documents the supported values.

The actual `.env`, local DuckDB files, virtual environments, Python caches, and
logs are ignored by Git.

Core variables:

- `NEXUS_DB_PATH`
- `NEXUS_JWT_SECRET`
- `NEXUS_LLM_MODEL`
- `PORT`

## Scope

This is not a general autonomous-agent platform and does not attempt computer
control, purchasing, large-scale SaaS infrastructure, or a pixel-perfect
frontend.

The capstone focuses on a controlled local AI backend with measurable retrieval
reuse, authentication, persistence, background processing, and local inference.
