from __future__ import annotations
import contextvars
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_query_budget.budget import Budget
    from django_query_budget.tracker import BudgetTracker

_budget_stack: contextvars.ContextVar[list[Budget]] = contextvars.ContextVar("query_budget_stack", default=None)
_current_tag: contextvars.ContextVar[str | None] = contextvars.ContextVar("query_budget_tag", default=None)
_trackers: dict[str, BudgetTracker] = {}
_trackers_lock = threading.Lock()


def push_budget(budget: Budget) -> contextvars.Token:
    stack = _budget_stack.get(None)
    if stack is None:
        stack = []
    new_stack = [*stack, budget]
    return _budget_stack.set(new_stack)


def pop_budget(token: contextvars.Token) -> None:
    _budget_stack.reset(token)


def current_budget() -> Budget | None:
    stack = _budget_stack.get(None)
    if not stack:
        return None
    return stack[-1]


def push_tag(tag: str) -> contextvars.Token:
    return _current_tag.set(tag)


def pop_tag(token: contextvars.Token) -> None:
    _current_tag.reset(token)


def current_tag() -> str | None:
    return _current_tag.get(None)


def get_tracker(scope_key: str, window_seconds: float) -> BudgetTracker:
    if scope_key not in _trackers:
        with _trackers_lock:
            if scope_key not in _trackers:
                from django_query_budget.tracker import BudgetTracker
                _trackers[scope_key] = BudgetTracker(window_seconds=window_seconds)
    return _trackers[scope_key]


def clear_trackers() -> None:
    with _trackers_lock:
        _trackers.clear()
