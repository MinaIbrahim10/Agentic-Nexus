from pathlib import Path

from rag_pipeline.query_cache import (
    QueryResultCache,
)


def test_cache_miss_then_hit():
    cache = QueryResultCache(
        max_entries=4
    )

    assert (
        cache.get(
            "Explain CRAG"
        )
        is None
    )

    cache.set(
        "Explain CRAG",
        {
            "context": ["doc"],
            "status": "VERIFIED",
            "score": 0.9,
        },
    )

    result = cache.get(
        "Explain CRAG"
    )

    assert result[
        "status"
    ] == "VERIFIED"

    stats = cache.stats()

    assert stats["misses"] == 1
    assert stats["hits"] == 1
    assert stats["entries"] == 1


def test_normalized_repeat_is_hit():
    cache = QueryResultCache()

    cache.set(
        "Explain CRAG",
        {"value": 1},
    )

    result = cache.get(
        "  explain   crag  "
    )

    assert result == {
        "value": 1
    }

    assert (
        cache.stats()["hits"]
        == 1
    )


def test_cached_value_is_defensively_copied():
    cache = QueryResultCache()

    original = {
        "context": ["safe"]
    }

    cache.set(
        "query",
        original,
    )

    received = cache.get(
        "query"
    )

    received[
        "context"
    ].append(
        "mutated"
    )

    second = cache.get(
        "query"
    )

    assert second == {
        "context": ["safe"]
    }


def test_lru_cache_is_bounded():
    cache = QueryResultCache(
        max_entries=2
    )

    cache.set(
        "first",
        {"id": 1},
    )

    cache.set(
        "second",
        {"id": 2},
    )

    assert (
        cache.get("first")
        is not None
    )

    cache.set(
        "third",
        {"id": 3},
    )

    assert (
        cache.get("second")
        is None
    )

    assert (
        cache.get("first")
        is not None
    )

    assert (
        cache.get("third")
        is not None
    )

    assert (
        cache.stats()["entries"]
        == 2
    )


def test_hybrid_agent_checks_cache_before_retrieval():
    source = Path(
        "agents/hybrid_rag_agent.py"
    ).read_text()

    cache_check = source.index(
        "get_cached_hybrid_result"
    )

    vector_retrieval = (
        source.index(
            "query_cag_or_retrieve"
        )
    )

    graph_retrieval = (
        source.index(
            "query_graph"
        )
    )

    assert (
        cache_check
        < vector_retrieval
    )

    assert (
        cache_check
        < graph_retrieval
    )

    assert (
        "cache_hybrid_result"
        in source
    )
