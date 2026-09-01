from collections import OrderedDict
from copy import deepcopy
from typing import Any


class QueryResultCache:
    """
    Small process-local LRU cache for complete hybrid retrieval results.

    A cache hit avoids repeating:
    - vector retrieval;
    - knowledge-graph lookup;
    - Cross-Encoder reranking;
    - fallback selection.

    This cache is intentionally bounded and process-local for the capstone.
    """

    def __init__(
        self,
        max_entries: int = 128,
    ):
        if max_entries < 1:
            raise ValueError(
                "max_entries must be >= 1"
            )

        self.max_entries = max_entries
        self._items = OrderedDict()

        self.hits = 0
        self.misses = 0


    @staticmethod
    def normalize_query(
        query: str,
    ) -> str:
        return " ".join(
            query.lower().split()
        )


    def get(
        self,
        query: str,
    ) -> Any | None:
        key = self.normalize_query(
            query
        )

        if key not in self._items:
            self.misses += 1
            return None

        self.hits += 1

        value = self._items.pop(
            key
        )

        self._items[key] = value

        return deepcopy(
            value
        )


    def set(
        self,
        query: str,
        value: Any,
    ) -> None:
        key = self.normalize_query(
            query
        )

        if key in self._items:
            self._items.pop(
                key
            )

        self._items[key] = deepcopy(
            value
        )

        while (
            len(self._items)
            > self.max_entries
        ):
            self._items.popitem(
                last=False
            )


    def clear(
        self,
    ) -> None:
        self._items.clear()

        self.hits = 0
        self.misses = 0


    def stats(
        self,
    ) -> dict:
        total = (
            self.hits
            + self.misses
        )

        hit_rate = (
            self.hits / total
            if total
            else 0.0
        )

        return {
            "entries":
                len(self._items),
            "max_entries":
                self.max_entries,
            "hits":
                self.hits,
            "misses":
                self.misses,
            "hit_rate":
                hit_rate,
        }
