from __future__ import annotations

import functools
from typing import Any, Callable

from django.db import connection

from django_query_budget.budget import Budget
from django_query_budget.resolution import pop_budget, pop_tag, push_budget, push_tag
from django_query_budget.wrapper import query_budget_wrapper


class query_budget:
    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._name = kwargs.get("name")

    def _make_budget(self, func: Callable | None = None) -> Budget:
        kwargs = dict(self._kwargs)
        if "name" not in kwargs and func is not None:
            kwargs["name"] = f"{func.__module__}.{func.__qualname__}"
        return Budget(**kwargs)

    def __call__(self, func: Callable) -> Callable:
        budget = self._make_budget(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            token = push_budget(budget)
            try:
                with connection.execute_wrapper(query_budget_wrapper):
                    return func(*args, **kwargs)
            finally:
                pop_budget(token)

        return wrapper

    def __enter__(self) -> query_budget:
        self._budget = self._make_budget()
        self._token = push_budget(self._budget)
        self._wrapper_ctx = connection.execute_wrapper(query_budget_wrapper)
        self._wrapper_ctx.__enter__()
        return self

    def __exit__(self, *exc: Any) -> None:
        self._wrapper_ctx.__exit__(*exc)
        pop_budget(self._token)


class query_tag:
    def __init__(self, tag: str) -> None:
        self._tag = tag

    def __enter__(self) -> query_tag:
        self._token = push_tag(self._tag)
        return self

    def __exit__(self, *exc: Any) -> None:
        pop_tag(self._token)
