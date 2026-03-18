from __future__ import annotations
import logging
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_query_budget.sync.base import BaseSyncBackend

from django_query_budget.hooks import fire_hooks
from django_query_budget.resolution import get_tracker

logger = logging.getLogger("django.query_budget.sync")

class SyncWorker:
    def __init__(self, backend: BaseSyncBackend, interval: float = 5.0, node_id: str = "default") -> None:
        self._backend = backend
        self._interval = interval
        self._node_id = node_id
        self._scopes: list[tuple[str, float]] = []
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()

    def add_scope(self, scope_key: str, window_seconds: float) -> None:
        self._scopes.append((scope_key, window_seconds))

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stopped.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="query-budget-sync")
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            self._thread = None

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stopped.is_set():
            for scope_key, window_seconds in self._scopes:
                try:
                    self._sync_scope(scope_key, window_seconds)
                except Exception:
                    logger.exception("Error syncing scope %s", scope_key)
            self._stopped.wait(timeout=self._interval)

    def _sync_scope(self, scope_key: str, window_seconds: float) -> None:
        tracker = get_tracker(scope_key, window_seconds=window_seconds)
        local_stats = tracker.to_stats(node_id=self._node_id)
        self._backend.push(scope_key, local_stats)
        cluster_stats = self._backend.pull(scope_key)
        fire_hooks("on_sync", scope_key=scope_key, local_stats=local_stats, cluster_stats=cluster_stats)
