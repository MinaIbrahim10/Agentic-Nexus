import torch

from sentence_transformers import (
    CrossEncoder,
)
from langchain_community.tools import (
    DuckDuckGoSearchRun,
)
from langsmith import traceable

from rag_pipeline.data_engine import (
    CAGDataEngine,
)
from rag_pipeline.graph_store import (
    KnowledgeGraphStore,
)


reranker_model = CrossEncoder(
    "BAAI/bge-reranker-large"
)

web_search_tool = (
    DuckDuckGoSearchRun()
)

CRAG_THRESHOLD = 0.4


@traceable(
    run_type="chain",
    name="Hybrid_GraphRAG_CRAG_Agent",
)
def run_hybrid_rag_agent(
    query: str,
    data_engine: CAGDataEngine,
    graph_store: KnowledgeGraphStore,
):
    cached = (
        data_engine
        .get_cached_hybrid_result(
            query
        )
    )

    if cached is not None:
        print(
            "-> [CAG Cache]: HIT - "
            "skipping retrieval and reranking"
        )

        return cached

    print(
        "-> [CAG Cache]: MISS - "
        "executing hybrid retrieval"
    )

    vector_docs = (
        data_engine
        .query_cag_or_retrieve(
            query,
            use_cag=False,
        )
    )

    kg_docs = (
        graph_store
        .query_graph(
            query
        )
    )

    combined_context = (
        vector_docs
        + kg_docs
    )

    if combined_context:
        pairs = [
            [query, doc]
            for doc
            in combined_context
        ]

        raw_scores = (
            reranker_model.predict(
                pairs
            )
        )

        probs = torch.sigmoid(
            torch.tensor(
                raw_scores
            )
        ).numpy()

        best_score = float(
            probs.max()
        )

        print(
            "-> [CRAG Scoring]: "
            f"raw={raw_scores.max():.3f} "
            f"-> normalized={best_score:.3f}"
        )

    else:
        best_score = 0.0

    if (
        best_score
        >= CRAG_THRESHOLD
    ):
        result = {
            "context":
                combined_context,
            "status":
                "VERIFIED",
            "score":
                best_score,
        }

    else:
        try:
            web_results = (
                web_search_tool.run(
                    query
                )
            )

            if not web_results:
                web_results = (
                    "Web search returned "
                    "no results."
                )

        except Exception as exc:
            print(
                "[Web Search Warning]: "
                f"{type(exc).__name__} "
                f"- {exc}"
            )

            web_results = (
                "Web search unavailable. "
                "Falling back on local "
                "context only."
            )

        result = {
            "context":
                combined_context
                + [str(web_results)],
            "status":
                "WEB_FALLBACK",
            "score":
                best_score,
        }

    data_engine.cache_hybrid_result(
        query,
        result,
    )

    return result


@traceable(
    run_type="chain",
    name="Query_Rewriter",
)
def rewrite_query_for_retry(
    original_query: str,
    llm,
) -> str:
    prompt = f"""
The following search query returned weak
retrieval results.

Rewrite it to be broader and use different
key terms, while preserving intent.

Return ONLY the rewritten query,
nothing else.

Original query: {original_query}
"""

    rewritten = (
        llm.invoke(
            prompt
        )
        .content
        .strip()
    )

    return rewritten
