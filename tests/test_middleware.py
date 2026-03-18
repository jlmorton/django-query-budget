import pytest
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings


def simple_view(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok")


@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m", "action": "LOG"},
})
class TestQueryBudgetMiddleware(TestCase):
    def test_middleware_processes_request(self):
        from django_query_budget.middleware import QueryBudgetMiddleware
        middleware = QueryBudgetMiddleware(lambda req: simple_view(req))
        request = RequestFactory().get("/")
        response = middleware(request)
        assert response.status_code == 200

    def test_middleware_installs_wrapper(self):
        from django_query_budget.middleware import QueryBudgetMiddleware
        from django_query_budget.resolution import get_tracker
        middleware = QueryBudgetMiddleware(lambda req: simple_view(req))
        request = RequestFactory().get("/")
        middleware(request)
        tracker = get_tracker("default", window_seconds=300.0)
        assert tracker.query_count >= 1

    def test_middleware_cleans_up_on_exception(self):
        from django_query_budget.middleware import QueryBudgetMiddleware
        from django_query_budget.resolution import current_budget
        def error_view(request): raise ValueError("boom")
        middleware = QueryBudgetMiddleware(lambda req: error_view(req))
        request = RequestFactory().get("/")
        with pytest.raises(ValueError, match="boom"):
            middleware(request)
        assert current_budget() is None


@override_settings(QUERY_BUDGET={})
class TestMiddlewareNoBudget(TestCase):
    def test_middleware_no_default_passes_through(self):
        from django_query_budget.middleware import QueryBudgetMiddleware
        middleware = QueryBudgetMiddleware(lambda req: simple_view(req))
        request = RequestFactory().get("/")
        response = middleware(request)
        assert response.status_code == 200


@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "0s", "window": "5m", "action": "REJECT"},
})
class TestMiddlewareReject(TestCase):
    def test_middleware_reject(self):
        from django_query_budget.actions import QueryBudgetExceeded
        from django_query_budget.middleware import QueryBudgetMiddleware
        from django_query_budget.resolution import get_tracker
        tracker = get_tracker("default", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        middleware = QueryBudgetMiddleware(lambda req: simple_view(req))
        request = RequestFactory().get("/")
        with pytest.raises(QueryBudgetExceeded):
            middleware(request)
