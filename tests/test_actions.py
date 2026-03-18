import logging
import threading

import pytest


def test_query_budget_exceeded_exception():
    from django_query_budget.actions import QueryBudgetExceeded
    from django_query_budget.constraints import Violation
    v = Violation("total_runtime", 100.0, 50.0, None, "exceeded")
    exc = QueryBudgetExceeded(v)
    assert exc.violation is v
    assert "exceeded" in str(exc)
    assert isinstance(exc, Exception)
    assert not isinstance(exc, OSError)


def test_register_and_get_action():
    from django_query_budget.actions import get_action, register_action
    def my_action(budget, tracker, violation): pass
    register_action("TEST_ACTION", my_action)
    action_callable, mode = get_action("TEST_ACTION")
    assert action_callable is my_action


def test_get_unknown_action_raises():
    from django_query_budget.actions import get_action
    with pytest.raises(KeyError, match="NO_SUCH_ACTION"):
        get_action("NO_SUCH_ACTION")


def test_log_action(caplog):
    from django_query_budget.actions import log_action
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    violation = Violation("total_runtime", 3700.0, 3600.0, None, "exceeded")
    with caplog.at_level(logging.WARNING, logger="django.query_budget"):
        log_action(budget, tracker, violation)
    assert "exceeded" in caplog.text


def test_reject_action():
    from django_query_budget.actions import QueryBudgetExceeded, reject_action
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    violation = Violation("total_runtime", 3700.0, 3600.0, None, "exceeded")
    with pytest.raises(QueryBudgetExceeded) as exc_info:
        reject_action(budget, tracker, violation)
    assert exc_info.value.violation is violation


def test_builtin_actions_registered():
    from django_query_budget.actions import get_action, log_action, reject_action
    from django_query_budget.hooks import HookMode
    log_callable, log_mode = get_action("LOG")
    reject_callable, reject_mode = get_action("REJECT")
    assert log_callable is log_action
    assert reject_callable is reject_action
    assert log_mode == HookMode.SYNC
    assert reject_mode == HookMode.SYNC


def test_custom_action_defaults_to_async():
    from django_query_budget.actions import get_action, register_action
    from django_query_budget.hooks import HookMode
    def my_action(budget, tracker, violation): pass
    register_action("ASYNC_TEST", my_action)
    _, mode = get_action("ASYNC_TEST")
    assert mode == HookMode.ASYNC


def test_custom_action_explicit_sync():
    from django_query_budget.actions import get_action, register_action
    from django_query_budget.hooks import HookMode
    def my_action(budget, tracker, violation): pass
    register_action("SYNC_TEST", my_action, mode=HookMode.SYNC)
    _, mode = get_action("SYNC_TEST")
    assert mode == HookMode.SYNC


def test_async_action_fires_on_background_thread():
    from django_query_budget.actions import register_action
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation
    from django_query_budget.hooks import HookMode
    from django_query_budget.wrapper import _invoke_action

    event = threading.Event()
    calls = []

    def async_action(budget, tracker, violation):
        calls.append(threading.current_thread().name)
        event.set()

    register_action("ASYNC_THREAD_TEST", async_action, mode=HookMode.ASYNC)

    budget = Budget(total_runtime="1h", window="5m")
    violation = Violation("test", 0, 0, None, "test")
    _invoke_action(async_action, HookMode.ASYNC, budget, None, violation)

    assert event.wait(timeout=2.0)
    assert calls[0] != threading.current_thread().name  # Ran on a different thread
