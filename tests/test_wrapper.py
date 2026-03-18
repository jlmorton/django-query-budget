import pytest
from django.db import connection
from django.test import TestCase, override_settings


@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m"},
})
class TestExecuteWrapper(TestCase):
    def test_wrapper_records_query(self):
        from django_query_budget.budget import Budget
        from django_query_budget.resolution import get_tracker, push_budget, pop_budget
        from django_query_budget.wrapper import query_budget_wrapper

        budget = Budget(total_runtime="1h", window="5m", name="test")
        token = push_budget(budget)
        try:
            with connection.execute_wrapper(query_budget_wrapper):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            tracker = get_tracker("named:test", window_seconds=300.0)
            assert tracker.query_count >= 1
        finally:
            pop_budget(token)

    def test_wrapper_reject_pre_execution(self):
        from django_query_budget.actions import QueryBudgetExceeded
        from django_query_budget.budget import Budget
        from django_query_budget.resolution import get_tracker, push_budget, pop_budget
        from django_query_budget.wrapper import query_budget_wrapper

        budget = Budget(total_runtime="0s", window="5m", action="REJECT", name="reject-test")
        token = push_budget(budget)
        try:
            tracker = get_tracker("named:reject-test", window_seconds=300.0)
            tracker.record(duration=1.0, fingerprint="setup")
            with pytest.raises(QueryBudgetExceeded):
                with connection.execute_wrapper(query_budget_wrapper):
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
        finally:
            pop_budget(token)

    def test_wrapper_no_budget_passthrough(self):
        from django_query_budget.wrapper import query_budget_wrapper
        with connection.execute_wrapper(query_budget_wrapper):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                assert row == (1,)

    def test_wrapper_fires_on_query_executed_hook(self):
        from django_query_budget.budget import Budget
        from django_query_budget.hooks import HookMode, register_hook
        from django_query_budget.resolution import push_budget, pop_budget
        from django_query_budget.wrapper import query_budget_wrapper

        hook_calls = []
        def on_exec(**kwargs): hook_calls.append(kwargs)
        register_hook("on_query_executed", on_exec, mode=HookMode.SYNC)

        budget = Budget(total_runtime="1h", window="5m", name="hook-test")
        token = push_budget(budget)
        try:
            with connection.execute_wrapper(query_budget_wrapper):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            assert len(hook_calls) >= 1
            assert "fingerprint" in hook_calls[0]
            assert "duration" in hook_calls[0]
        finally:
            pop_budget(token)
