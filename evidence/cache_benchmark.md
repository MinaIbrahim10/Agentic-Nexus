# Agentic-Nexus CAG Benchmark

## Method

The same query was executed 10 times through the real
Hybrid RAG retrieval path.

The uncached scenario cleared the CAG cache before every query.

The cached scenario cleared the cache once, so the first request
performed the real retrieval pipeline and the following nine
requests reused the cached hybrid result.

Model initialization and warm-up were excluded.

Web fallback was not allowed.

## Retrieval stack

- Ollama bge-m3 embeddings
- FAISS vector retrieval
- NetworkX knowledge graph
- BAAI/bge-reranker-large CrossEncoder
- CRAG evaluation

## Results

Uncached expensive pipeline calls:

- Vector retrieval: 10
- Knowledge graph lookup: 10
- CrossEncoder reranking: 10

Cached expensive pipeline calls:

- Vector retrieval: 1
- Knowledge graph lookup: 1
- CrossEncoder reranking: 1

Retrieval-work reduction:

**10.00x**

Total uncached latency:

**1785.915 ms**

Total cached latency:

**179.878 ms**

Measured end-to-end retrieval latency speedup:

**9.93x**

## 10x claim

**ACHIEVED**

The 10x claim refers specifically to expensive retrieval-work
executions for repeated identical queries, not to a guaranteed
10x wall-clock latency improvement.
