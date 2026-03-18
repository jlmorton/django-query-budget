import logging
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
    assert get_action("TEST_ACTION") is my_action

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
    assert get_action("LOG") is log_action
    assert get_action("REJECT") is reject_action
