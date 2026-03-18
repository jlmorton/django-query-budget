import time
from datetime import timedelta
import pytest

def test_budget_stats_fields():
    from django_query_budget.tracker import BudgetStats
    stats = BudgetStats(total_runtime=1.5, query_count=10, window_start=1000.0, window_end=1300.0, node_id="node-1")
    assert stats.total_runtime == 1.5
    assert stats.query_count == 10
    assert stats.node_id == "node-1"

def test_tracker_record_and_stats():
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=0.5, fingerprint="select ?")
    tracker.record(duration=0.3, fingerprint="insert ?")
    assert tracker.total_runtime == pytest.approx(0.8, abs=0.01)
    assert tracker.query_count == 2

def test_tracker_window_eviction():
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=0.1)
    tracker.record(duration=0.5, fingerprint="q1")
    time.sleep(0.15)
    tracker.record(duration=0.1, fingerprint="q2")
    assert tracker.query_count == 1
    assert tracker.total_runtime == pytest.approx(0.1, abs=0.01)

def test_tracker_last_query_duration():
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=0.1, fingerprint="q1")
    tracker.record(duration=0.5, fingerprint="q2")
    assert tracker.last_query_duration == pytest.approx(0.5, abs=0.01)

def test_tracker_last_query_duration_empty():
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=300.0)
    assert tracker.last_query_duration is None

def test_tracker_to_stats():
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=0.5, fingerprint="q1")
    tracker.record(duration=0.3, fingerprint="q1")
    stats = tracker.to_stats(node_id="node-1")
    assert stats.total_runtime == pytest.approx(0.8, abs=0.01)
    assert stats.query_count == 2
    assert stats.node_id == "node-1"

def test_tracker_thread_safety():
    import threading
    from django_query_budget.tracker import BudgetTracker
    tracker = BudgetTracker(window_seconds=300.0)
    errors = []
    def worker():
        try:
            for _ in range(100):
                tracker.record(duration=0.001, fingerprint="q")
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert tracker.query_count == 1000
