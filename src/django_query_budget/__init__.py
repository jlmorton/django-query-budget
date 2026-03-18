"""Django Query Budget — database query budget enforcement for Django."""

from django_query_budget.actions import (
    QueryBudgetExceeded,
    register_action,
)
from django_query_budget.decorators import query_budget, query_tag
from django_query_budget.hooks import BaseHook, ExecutionMode, HookMode, register_hook

__all__ = [
    "BaseHook",
    "ExecutionMode",
    "HookMode",  # Backwards-compatible alias for ExecutionMode
    "QueryBudgetExceeded",
    "query_budget",
    "query_tag",
    "register_action",
    "register_hook",
]
