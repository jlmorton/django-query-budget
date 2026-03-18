import time
from unittest.mock import MagicMock
import pytest
from django_query_budget.tracker import BudgetStats, BudgetTracker

def test_sync_worker_starts_and_stops():
    from django_query_budget.sync.worker import SyncWorker
    backend = MagicMock()
    backend.pull.return_value = None
    worker = SyncWorker(backend=backend, interval=0.1, node_id="test")
    worker.start()
    assert worker.is_alive()
    worker.stop()
    assert not worker.is_alive()

def test_sync_worker_pushes_stats():
    from django_query_budget.sync.worker import SyncWorker
    from django_query_budget.resolution import get_tracker, clear_trackers
    clear_trackers()
    backend = MagicMock()
    backend.pull.return_value = None
    tracker = get_tracker("default", window_seconds=300.0)
    tracker.record(duration=1.0, fingerprint="q")
    worker = SyncWorker(backend=backend, interval=0.1, node_id="test")
    worker.add_scope("default", window_seconds=300.0)
    worker.start()
    time.sleep(0.3)
    worker.stop()
    assert backend.push.called

def test_sync_worker_pulls_stats():
    from django_query_budget.sync.worker import SyncWorker
    backend = MagicMock()
    backend.pull.return_value = BudgetStats(total_runtime=50.0, query_count=500, window_start=0, window_end=300.0, node_id="cluster")
    worker = SyncWorker(backend=backend, interval=0.1, node_id="test")
    worker.add_scope("default", window_seconds=300.0)
    worker.start()
    time.sleep(0.3)
    worker.stop()
    assert backend.pull.called
