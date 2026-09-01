import duckdb
import pandas as pd

from langchain_community.vectorstores import (
    FAISS,
)
from langchain_core.documents import (
    Document,
)

from config import embeddings
from rag_pipeline.query_cache import (
    QueryResultCache,
)


class CAGDataEngine:
    """
    Hybrid data engine containing:

    - DuckDB structured records;
    - FAISS vector retrieval;
    - a bounded process-local cache for complete
      hybrid retrieval results.

    The cache itself is checked by the Hybrid RAG
    agent before any retrieval work starts.
    """

    def __init__(
        self,
        cache_size: int = 128,
    ):
        self.market_data = [
            {
                "id": 1,
                "topic":
                    "Local RAG Optimization",
                "content":
                    "Retrieval-Augmented Generation systems deployed locally using Ollama and FAISS reduce latency by 40% for enterprise apps.",
                "sector":
                    "Inference Optimization",
            },
            {
                "id": 2,
                "topic":
                    "GraphRAG & Knowledge Graphs",
                "content":
                    "Combining NetworkX Knowledge Graphs with Vector Stores improves multi-hop reasoning in complex technical domains.",
                "sector":
                    "Knowledge Architecture",
            },
            {
                "id": 3,
                "topic":
                    "Corrective RAG (CRAG)",
                "content":
                    "CRAG dynamically evaluates retrieval scores using Cross-Encoders, triggering web search fallbacks when local context fails.",
                "sector":
                    "Self-Correction Pipelines",
            },
            {
                "id": 4,
                "topic":
                    "Language Agent Grammars (LAG)",
                "content":
                    "Enforcing strict DFA JSON schemas on agent outputs eliminates parsing errors and ensures deterministic multi-agent communication.",
                "sector":
                    "Agentic Control",
            },
            {
                "id": 5,
                "topic":
                    "Hardware Quantization & Acceleration",
                "content":
                    "Running 4-bit and 8-bit quantized open-weight models via CUDA maximizes VRAM efficiency for local LLM pipelines.",
                "sector":
                    "Hardware & Quantization",
            },
        ]

        self.query_cache = QueryResultCache(
            max_entries=cache_size
        )

        self._init_duckdb()
        self._init_vector_store()


    def _init_duckdb(
        self,
    ):
        df = pd.DataFrame(
            self.market_data
        )

        self.duck_con = duckdb.connect(
            database=":memory:"
        )

        self.duck_con.execute(
            """
            CREATE TABLE ai_market_research
            AS SELECT * FROM df
            """
        )


    def _init_vector_store(
        self,
    ):
        documents = [
            Document(
                page_content=(
                    f"Topic: {row['topic']} | "
                    f"Sector: {row['sector']} | "
                    f"Content: {row['content']}"
                ),
                metadata={
                    "id": row["id"]
                },
            )
            for row in self.market_data
        ]

        self.vector_store = (
            FAISS.from_documents(
                documents,
                embeddings,
            )
        )

        self.retriever = (
            self.vector_store
            .as_retriever(
                search_kwargs={
                    "k": 2
                }
            )
        )


    def query_cag_or_retrieve(
        self,
        query: str,
        use_cag: bool = False,
    ) -> list[str]:
        """
        Perform real vector retrieval.

        `use_cag` remains in the signature for
        backward compatibility. Complete hybrid
        results are cached outside this method so
        a hit can skip vector search, graph lookup,
        and reranking together.
        """

        docs = self.retriever.invoke(
            query
        )

        return [
            document.page_content
            for document in docs
        ]


    def get_cached_hybrid_result(
        self,
        query: str,
    ):
        return self.query_cache.get(
            query
        )


    def cache_hybrid_result(
        self,
        query: str,
        result: dict,
    ) -> None:
        self.query_cache.set(
            query,
            result,
        )


    def clear_cache(
        self,
    ) -> None:
        self.query_cache.clear()


    def cache_stats(
        self,
    ) -> dict:
        return self.query_cache.stats()
