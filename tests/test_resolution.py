import contextvars
import pytest

def test_push_pop_budget():
    from django_query_budget.budget import Budget
    from django_query_budget.resolution import current_budget, pop_budget, push_budget
    b1 = Budget(total_runtime="1h", window="5m")
    b2 = Budget(total_runtime="10s", window="1m")
    token1 = push_budget(b1)
    assert current_budget() is b1
    token2 = push_budget(b2)
    assert current_budget() is b2
    pop_budget(token2)
    assert current_budget() is b1
    pop_budget(token1)
    assert current_budget() is None

def test_current_budget_empty():
    from django_query_budget.resolution import current_budget
    ctx = contextvars.copy_context()
    result = ctx.run(current_budget)
    assert result is None

def test_nesting_restores_correctly():
    from django_query_budget.budget import Budget
    from django_query_budget.resolution import current_budget, pop_budget, push_budget
    default = Budget(total_runtime="1h", window="5m", name="default")
    inner = Budget(total_runtime="10s", window="1m", name="inner")
    innermost = Budget(total_runtime="1s", window="10s", name="innermost")
    ctx = contextvars.copy_context()
    def run():
        t1 = push_budget(default)
        assert current_budget().name == "default"
        t2 = push_budget(inner)
        assert current_budget().name == "inner"
        t3 = push_budget(innermost)
        assert current_budget().name == "innermost"
        pop_budget(t3)
        assert current_budget().name == "inner"
        pop_budget(t2)
        assert current_budget().name == "default"
        pop_budget(t1)
        assert current_budget() is None
    ctx.run(run)

def test_get_tracker_returns_same_for_scope():
    from django_query_budget.resolution import get_tracker
    t1 = get_tracker("default", window_seconds=300.0)
    t2 = get_tracker("default", window_seconds=300.0)
    assert t1 is t2

def test_get_tracker_different_scopes():
    from django_query_budget.resolution import get_tracker
    t1 = get_tracker("scope-a", window_seconds=300.0)
    t2 = get_tracker("scope-b", window_seconds=300.0)
    assert t1 is not t2

def test_current_tag():
    from django_query_budget.resolution import current_tag, pop_tag, push_tag
    ctx = contextvars.copy_context()
    def run():
        assert current_tag() is None
        token = push_tag("reporting")
        assert current_tag() == "reporting"
        pop_tag(token)
        assert current_tag() is None
    ctx.run(run)
