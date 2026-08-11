import duckdb
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import embeddings

class CAGDataEngine:
    """
    Hybrid Data Engine integrating DuckDB for structured queries,
    FAISS for semantic retrieval, and an in-memory Cache-Augmented Generation (CAG) buffer.
    """
    def __init__(self):
        self.market_data = [
            {
                "id": 1,
                "topic": "Local RAG Optimization",
                "content": "Retrieval-Augmented Generation systems deployed locally using Ollama and FAISS reduce latency by 40% for enterprise apps.",
                "sector": "Inference Optimization"
            },
            {
                "id": 2,
                "topic": "GraphRAG & Knowledge Graphs",
                "content": "Combining NetworkX Knowledge Graphs with Vector Stores improves multi-hop reasoning in complex technical domains.",
                "sector": "Knowledge Architecture"
            },
            {
                "id": 3,
                "topic": "Corrective RAG (CRAG)",
                "content": "CRAG dynamically evaluates retrieval scores using Cross-Encoders, triggering web search fallbacks when local context fails.",
                "sector": "Self-Correction Pipelines"
            },
            {
                "id": 4,
                "topic": "Language Agent Grammars (LAG)",
                "content": "Enforcing strict DFA JSON schemas on agent outputs eliminates parsing errors and ensures deterministic multi-agent communication.",
                "sector": "Agentic Control"
            },
            {
                "id": 5,
                "topic": "Hardware Quantization & Acceleration",
                "content": "Running 4-bit and 8-bit quantized open-weight models via CUDA maximizes VRAM efficiency for local LLM pipelines.",
                "sector": "Hardware & Quantization"
            }
        ]

        # CAG Strategy: Pre-build the entire knowledge corpus into memory
        self.preloaded_cag_context = [
            f"Topic: {row['topic']} | Sector: {row['sector']} | Content: {row['content']}"
            for row in self.market_data
        ]

        self._init_duckdb()
        self._init_vector_store()

    def _init_duckdb(self):
        df = pd.DataFrame(self.market_data)
        self.duck_con = duckdb.connect(database=":memory:")
        self.duck_con.execute("CREATE TABLE ai_market_research AS SELECT * FROM df")

    def _init_vector_store(self):
        documents = [
            Document(
                page_content=f"Topic: {row['topic']} | Sector: {row['sector']} | Content: {row['content']}",
                metadata={"id": row["id"]}
            )
            for row in self.market_data
        ]
        self.vector_store = FAISS.from_documents(documents, embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 2})

    def query_cag_or_retrieve(self, query: str, use_cag: bool = True) -> list[str]:
        """
        Main interface method used across the pipeline.

        - If use_cag=True: Serves the full pre-loaded in-memory context (CAG paradigm).
        - If use_cag=False: Bypasses CAG and falls back to FAISS vector search (RAG paradigm).
        """
        if use_cag:
            # Serves pre-loaded in-memory knowledge directly (True CAG)
            return self.preloaded_cag_context

        # Vector Store Fallback (RAG)
        docs = self.retriever.invoke(query)
        return [d.page_content for d in docs]
