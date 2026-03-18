import pytest
from django.db import connection
from django.test import TestCase


class TestQueryBudgetContextManager(TestCase):
    def test_context_manager_pushes_and_pops(self):
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import current_budget
        assert current_budget() is None
        with query_budget(total_runtime="1h", window="5m"):
            b = current_budget()
            assert b is not None
            assert b.total_runtime_seconds == 3600.0
        assert current_budget() is None

    def test_context_manager_nesting(self):
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import current_budget
        with query_budget(total_runtime="1h", window="5m", name="outer"):
            assert current_budget().name == "outer"
            with query_budget(total_runtime="10s", window="1m", name="inner"):
                assert current_budget().name == "inner"
            assert current_budget().name == "outer"
        assert current_budget() is None

    def test_context_manager_installs_wrapper(self):
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import get_tracker
        with query_budget(total_runtime="1h", window="5m", name="wrapper-test"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        tracker = get_tracker("named:wrapper-test", window_seconds=300.0)
        assert tracker.query_count >= 1

    def test_context_manager_reject(self):
        from django_query_budget.actions import QueryBudgetExceeded
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import get_tracker
        tracker = get_tracker("named:reject-cm", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="1s", window="5m", action="REJECT", name="reject-cm"):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")


class TestQueryBudgetDecorator(TestCase):
    def test_decorator_applies_budget(self):
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import current_budget
        @query_budget(total_runtime="1h", window="5m", name="deco-test")
        def my_func():
            return current_budget()
        result = my_func()
        assert result is not None
        assert result.name == "deco-test"
        assert current_budget() is None

    def test_decorator_auto_name_from_function(self):
        from django_query_budget.decorators import query_budget
        from django_query_budget.resolution import current_budget
        @query_budget(total_runtime="1h", window="5m")
        def my_named_func():
            return current_budget()
        result = my_named_func()
        assert "my_named_func" in result.name


class TestQueryTag(TestCase):
    def test_query_tag_context_manager(self):
        from django_query_budget.decorators import query_tag
        from django_query_budget.resolution import current_tag
        assert current_tag() is None
        with query_tag("reporting"):
            assert current_tag() == "reporting"
        assert current_tag() is None

    def test_query_tag_nesting(self):
        from django_query_budget.decorators import query_tag
        from django_query_budget.resolution import current_tag
        with query_tag("outer"):
            assert current_tag() == "outer"
            with query_tag("inner"):
                assert current_tag() == "inner"
            assert current_tag() == "outer"
        assert current_tag() is None
