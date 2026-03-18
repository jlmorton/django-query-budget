import pytest
from datetime import timedelta


def test_parse_duration_seconds():
    from django_query_budget.budget import parse_duration
    assert parse_duration("30s") == timedelta(seconds=30)

def test_parse_duration_minutes():
    from django_query_budget.budget import parse_duration
    assert parse_duration("5m") == timedelta(minutes=5)

def test_parse_duration_hours():
    from django_query_budget.budget import parse_duration
    assert parse_duration("1h") == timedelta(hours=1)

def test_parse_duration_combined():
    from django_query_budget.budget import parse_duration
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)

def test_parse_duration_timedelta_passthrough():
    from django_query_budget.budget import parse_duration
    td = timedelta(seconds=42)
    assert parse_duration(td) is td

def test_parse_duration_invalid():
    from django_query_budget.budget import parse_duration
    with pytest.raises(ValueError, match="Invalid duration"):
        parse_duration("abc")

def test_parse_duration_integer_seconds():
    from django_query_budget.budget import parse_duration
    assert parse_duration(60) == timedelta(seconds=60)


def test_budget_with_strings():
    from django_query_budget.budget import Budget
    b = Budget(total_runtime="1h", window="5m")
    assert b.total_runtime == timedelta(hours=1)
    assert b.window == timedelta(minutes=5)
    assert b.action == "LOG"
    assert b.max_queries is None
    assert b.max_single_query is None
    assert b.constraints == []

def test_budget_with_timedeltas():
    from django_query_budget.budget import Budget
    b = Budget(total_runtime=timedelta(hours=1), window=timedelta(minutes=5))
    assert b.total_runtime == timedelta(hours=1)

def test_budget_all_fields():
    from django_query_budget.budget import Budget
    b = Budget(
        total_runtime="30m", window="5m", max_queries=1000,
        max_single_query="10s", action="REJECT", name="my-budget",
    )
    assert b.total_runtime == timedelta(minutes=30)
    assert b.max_queries == 1000
    assert b.max_single_query == timedelta(seconds=10)
    assert b.action == "REJECT"
    assert b.name == "my-budget"

def test_budget_total_runtime_seconds():
    from django_query_budget.budget import Budget
    b = Budget(total_runtime="1h30m", window="5m")
    assert b.total_runtime_seconds == 5400.0

def test_budget_window_seconds():
    from django_query_budget.budget import Budget
    b = Budget(total_runtime="1h", window="5m")
    assert b.window_seconds == 300.0

def test_budget_from_dict():
    from django_query_budget.budget import Budget
    b = Budget.from_dict({
        "total_runtime": "1h", "window": "5m",
        "action": "REJECT", "max_queries": 500,
    })
    assert b.total_runtime == timedelta(hours=1)
    assert b.action == "REJECT"
    assert b.max_queries == 500
