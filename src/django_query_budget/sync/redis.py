from __future__ import annotations
import json
import time
from typing import Any
from django_query_budget.sync.base import BaseSyncBackend
from django_query_budget.tracker import BudgetStats

class RedisSyncBackend(BaseSyncBackend):
    def __init__(self, client: Any, window_seconds: float, ttl_buffer: int = 60) -> None:
        self._client = client
        self._window_seconds = window_seconds
        self._ttl_buffer = ttl_buffer

    def _key(self, scope_key: str) -> str:
        bucket = int(time.time() / self._window_seconds)
        return f"query_budget:{scope_key}:{bucket}"

    def push(self, scope_key: str, stats: BudgetStats) -> None:
        key = self._key(scope_key)
        value = json.dumps({"total_runtime": stats.total_runtime, "query_count": stats.query_count})
        self._client.hset(key, stats.node_id, value)
        ttl = int(self._window_seconds) + self._ttl_buffer
        self._client.expire(key, ttl)

    def pull(self, scope_key: str) -> BudgetStats | None:
        key = self._key(scope_key)
        data = self._client.hgetall(key)
        if not data:
            return None
        total_runtime = 0.0
        query_count = 0
        for node_data in data.values():
            if isinstance(node_data, bytes):
                node_data = node_data.decode()
            parsed = json.loads(node_data)
            total_runtime += parsed["total_runtime"]
            query_count += parsed["query_count"]
        now = time.time()
        return BudgetStats(total_runtime=total_runtime, query_count=query_count, window_start=now - self._window_seconds, window_end=now, node_id="cluster")

    def clear(self, scope_key: str) -> None:
        key = self._key(scope_key)
        self._client.delete(key)
