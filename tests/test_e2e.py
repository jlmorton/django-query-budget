"""End-to-end integration tests with a real Django app."""
import pytest
from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from django_query_budget import QueryBudgetExceeded, query_budget, query_tag
from django_query_budget.resolution import clear_trackers, get_tracker


def _create_test_table():
    vendor = connection.vendor
    with connection.cursor() as cursor:
        if vendor == "postgresql":
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS test_item "
                "(id SERIAL PRIMARY KEY, name TEXT, value INTEGER)"
            )
        elif vendor == "mysql":
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS test_item "
                "(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), value INT)"
            )
        else:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS test_item "
                "(id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )

def _insert_test_data(n=10):
    with connection.cursor() as cursor:
        for i in range(n):
            cursor.execute("INSERT INTO test_item (name, value) VALUES (%s, %s)", [f"item-{i}", i * 10])

def _query_items():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM test_item WHERE value > %s", [0])
        return cursor.fetchall()


@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m", "action": "LOG"},
    "tags": {"reporting": {"total_runtime": "10s", "window": "5m", "action": "REJECT"}},
})
class TestE2EQueryBudget(TestCase):
    def setUp(self):
        clear_trackers()
        _create_test_table()

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_item")

    def test_decorator_tracks_queries(self):
        @query_budget(total_runtime="1h", window="5m", name="e2e-deco")
        def do_work():
            _insert_test_data(5)
            return _query_items()
        results = do_work()
        tracker = get_tracker("named:e2e-deco", window_seconds=300.0)
        assert tracker.query_count >= 6

    def test_context_manager_tracks_queries(self):
        with query_budget(total_runtime="1h", window="5m", name="e2e-cm"):
            _insert_test_data(3)
            results = _query_items()
        tracker = get_tracker("named:e2e-cm", window_seconds=300.0)
        assert tracker.query_count >= 4

    def test_reject_prevents_next_query(self):
        tracker = get_tracker("named:e2e-reject", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="1s", window="5m", action="REJECT", name="e2e-reject"):
                _query_items()

    def test_log_action_logs_warning(self):
        tracker = get_tracker("named:e2e-log", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with self.assertLogs("django.query_budget", level="WARNING") as cm:
            with query_budget(total_runtime="1s", window="5m", action="LOG", name="e2e-log"):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        assert any("budget violated" in msg or "total_runtime" in msg or "Total runtime" in msg for msg in cm.output)

    def test_nesting_decorator_and_context_manager(self):
        @query_budget(total_runtime="1h", window="5m", name="e2e-outer")
        def outer():
            _insert_test_data(2)
            with query_budget(total_runtime="1h", window="5m", name="e2e-inner"):
                _query_items()
            _query_items()
        outer()
        inner_tracker = get_tracker("named:e2e-inner", window_seconds=300.0)
        assert inner_tracker.query_count >= 1

    def test_tag_based_budget_resolution(self):
        tracker = get_tracker("tag:reporting", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="1h", window="5m", name="e2e-tag"):
                with query_tag("reporting"):
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")

    def test_middleware_integration(self):
        from django_query_budget.middleware import QueryBudgetMiddleware
        def view(request):
            _insert_test_data(2)
            return HttpResponse("ok")
        middleware = QueryBudgetMiddleware(lambda req: view(req))
        request = RequestFactory().get("/")
        response = middleware(request)
        assert response.status_code == 200
        tracker = get_tracker("default", window_seconds=300.0)
        assert tracker.query_count >= 2

    def test_custom_action_called(self):
        from django_query_budget import register_action
        calls = []
        def my_action(budget, tracker, violation): calls.append(violation)
        register_action("CUSTOM_E2E", my_action)
        tracker = get_tracker("named:e2e-custom", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with query_budget(total_runtime="1s", window="5m", action="CUSTOM_E2E", name="e2e-custom"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        assert len(calls) >= 1
        assert calls[0].constraint_name == "total_runtime"

    def test_max_queries_enforcement(self):
        tracker = get_tracker("named:e2e-max-q", window_seconds=300.0)
        for _ in range(10):
            tracker.record(duration=0.001, fingerprint="q")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="999h", window="5m", max_queries=5, action="REJECT", name="e2e-max-q"):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
