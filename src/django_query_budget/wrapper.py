from __future__ import annotations

import contextvars
import time
from typing import Any, Callable

from django_query_budget.actions import get_action
from django_query_budget.constraints import check_constraints
from django_query_budget.fingerprint import fingerprint_sql
from django_query_budget.hooks import HookMode, fire_hooks, _get_worker
from django_query_budget.resolution import current_budget, current_tag, get_tracker


def _invoke_action(action_callable, mode, budget, tracker, violation):
    """Invoke an action either synchronously or via the async hook queue."""
    if mode == HookMode.SYNC:
        action_callable(budget, tracker, violation)
    else:
        _get_worker().enqueue(
            lambda **kw: action_callable(kw["budget"], kw["tracker"], kw["violation"]),
            {"budget": budget, "tracker": tracker, "violation": violation},
        )

_wrapper_active: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "query_budget_wrapper_active", default=False
)


def _scope_key_for_budget(budget) -> str:
    if budget.name:
        return f"named:{budget.name}"
    return "default"


def query_budget_wrapper(execute: Callable, sql: str, params: Any, many: bool, context: dict) -> Any:
    if _wrapper_active.get(False):
        return execute(sql, params, many, context)

    budget = current_budget()

    tag = current_tag()
    if tag:
        from django_query_budget.settings import get_config
        config = get_config()
        tag_budget = config.tags.get(tag)
        if tag_budget:
            budget = tag_budget

    if budget is None:
        return execute(sql, params, many, context)

    scope_key = _scope_key_for_budget(budget)
    if tag and budget is not current_budget():
        scope_key = f"tag:{tag}"

    tracker = get_tracker(scope_key, window_seconds=budget.window_seconds)

    # Pre-execution check
    violation = check_constraints(tracker, budget, skip_single_query=True)
    if violation:
        action_callable, action_mode = get_action(budget.action)
        fire_hooks("on_budget_violation", budget=budget, tracker=tracker, violation=violation)
        _invoke_action(action_callable, action_mode, budget, tracker, violation)

    # Execute with re-entrancy guard
    token = _wrapper_active.set(True)
    try:
        start = time.monotonic()
        result = execute(sql, params, many, context)
        duration = time.monotonic() - start
    finally:
        _wrapper_active.reset(token)

    fp = fingerprint_sql(sql)
    tracker.record(duration=duration, fingerprint=fp)
    fire_hooks("on_query_executed", fingerprint=fp, duration=duration, tracker=tracker)

    # Post-execution check
    violation = check_constraints(tracker, budget)
    if violation:
        action_callable, action_mode = get_action(budget.action)
        fire_hooks("on_budget_violation", budget=budget, tracker=tracker, violation=violation)
        _invoke_action(action_callable, action_mode, budget, tracker, violation)

    return result
