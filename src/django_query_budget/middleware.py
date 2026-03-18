from __future__ import annotations
from typing import Callable
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django_query_budget.resolution import pop_budget, push_budget
from django_query_budget.settings import get_config
from django_query_budget.wrapper import query_budget_wrapper


class QueryBudgetMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        config = get_config()
        budget = config.default_budget
        if budget is None:
            return self.get_response(request)
        token = push_budget(budget)
        try:
            with connection.execute_wrapper(query_budget_wrapper):
                response = self.get_response(request)
        finally:
            pop_budget(token)
        return response
