"""Performance benchmarks for critical hot-path components."""
import time
import pytest
from django.db import connection
from django.test import TestCase
from django_query_budget.fingerprint import fingerprint_sql
from django_query_budget.resolution import clear_trackers
from django_query_budget.tracker import BudgetTracker


def test_fingerprint_performance():
    large_sql = "SELECT " + ", ".join(f'"col_{i}"' for i in range(100)) + " FROM large_table WHERE " + " AND ".join(f'"col_{i}" = {i}' for i in range(50))
    start = time.monotonic()
    for _ in range(10_000):
        fingerprint_sql(large_sql)
    elapsed = time.monotonic() - start
    per_call = elapsed / 10_000
    assert per_call < 0.001, f"Fingerprinting took {per_call*1000:.3f}ms per call (should be <1ms)"


def test_tracker_record_performance():
    tracker = BudgetTracker(window_seconds=300.0)
    start = time.monotonic()
    for i in range(100_000):
        tracker.record(duration=0.001, fingerprint="q")
    elapsed = time.monotonic() - start
    per_call = elapsed / 100_000
    assert per_call < 0.0001, f"Tracker record took {per_call*1e6:.1f}us per call (should be <100us)"


class TestWrapperOverhead(TestCase):
    def setUp(self):
        clear_trackers()

    def test_wrapper_overhead(self):
        from django_query_budget.budget import Budget
        from django_query_budget.resolution import push_budget, pop_budget
        from django_query_budget.wrapper import query_budget_wrapper

        n = 1000
        start = time.monotonic()
        for _ in range(n):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        baseline = time.monotonic() - start

        budget = Budget(total_runtime="999h", window="5m", name="perf-test")
        token = push_budget(budget)
        try:
            start = time.monotonic()
            with connection.execute_wrapper(query_budget_wrapper):
                for _ in range(n):
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
            with_wrapper = time.monotonic() - start
        finally:
            pop_budget(token)

        overhead_per_query = (with_wrapper - baseline) / n
        assert overhead_per_query < 0.0001, (
            f"Wrapper overhead: {overhead_per_query*1e6:.1f}us/query "
            f"(baseline={baseline/n*1e6:.1f}us, wrapped={with_wrapper/n*1e6:.1f}us)"
        )
