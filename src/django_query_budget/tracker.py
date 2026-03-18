from __future__ import annotations
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import NamedTuple

class QueryRecord(NamedTuple):
    timestamp: float
    duration: float
    fingerprint: str

@dataclass(frozen=True)
class BudgetStats:
    total_runtime: float
    query_count: int
    window_start: float
    window_end: float
    node_id: str

class BudgetTracker:
    def __init__(self, window_seconds: float) -> None:
        self._window_seconds = window_seconds
        self._entries: deque[QueryRecord] = deque()
        self._lock = threading.Lock()
        self._total_runtime = 0.0
        self._query_count = 0

    def record(self, duration: float, fingerprint: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._entries.append(QueryRecord(now, duration, fingerprint))
            self._total_runtime += duration
            self._query_count += 1
            self._evict(now)

    def _evict(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._entries and self._entries[0].timestamp < cutoff:
            old = self._entries.popleft()
            self._total_runtime -= old.duration
            self._query_count -= 1

    @property
    def total_runtime(self) -> float:
        with self._lock:
            self._evict(time.monotonic())
            return self._total_runtime

    @property
    def query_count(self) -> int:
        with self._lock:
            self._evict(time.monotonic())
            return self._query_count

    @property
    def last_query_duration(self) -> float | None:
        with self._lock:
            if not self._entries:
                return None
            return self._entries[-1].duration

    @property
    def last_query_entry(self) -> QueryRecord | None:
        with self._lock:
            if not self._entries:
                return None
            return self._entries[-1]

    def to_stats(self, node_id: str) -> BudgetStats:
        now = time.monotonic()
        with self._lock:
            self._evict(now)
            return BudgetStats(
                total_runtime=self._total_runtime, query_count=self._query_count,
                window_start=now - self._window_seconds, window_end=now, node_id=node_id,
            )
