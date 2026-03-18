from datetime import timedelta
import pytest

def test_violation_fields():
    from django_query_budget.constraints import Violation
    v = Violation(constraint_name="total_runtime", current_value=3600.0, limit_value=1800.0, fingerprint=None, message="Total runtime 3600.0s exceeds limit of 1800.0s")
    assert v.constraint_name == "total_runtime"
    assert v.current_value == 3600.0

def test_total_runtime_constraint_no_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_total_runtime
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=10.0, fingerprint="q")
    assert check_total_runtime(tracker, budget) is None

def test_total_runtime_constraint_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_total_runtime
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="10s", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=11.0, fingerprint="q")
    violation = check_total_runtime(tracker, budget)
    assert violation is not None
    assert violation.constraint_name == "total_runtime"

def test_max_queries_constraint_no_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_queries
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m", max_queries=100)
    tracker = BudgetTracker(window_seconds=300.0)
    for _ in range(50):
        tracker.record(duration=0.01, fingerprint="q")
    assert check_max_queries(tracker, budget) is None

def test_max_queries_constraint_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_queries
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m", max_queries=10)
    tracker = BudgetTracker(window_seconds=300.0)
    for _ in range(11):
        tracker.record(duration=0.01, fingerprint="q")
    violation = check_max_queries(tracker, budget)
    assert violation is not None
    assert violation.constraint_name == "max_queries"

def test_max_queries_constraint_none_skipped():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_queries
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    for _ in range(1000):
        tracker.record(duration=0.01, fingerprint="q")
    assert check_max_queries(tracker, budget) is None

def test_max_single_query_constraint_no_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_single_query
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m", max_single_query="30s")
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=5.0, fingerprint="q")
    assert check_max_single_query(tracker, budget) is None

def test_max_single_query_constraint_violation():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_single_query
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m", max_single_query="1s")
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=2.0, fingerprint="slow-q")
    violation = check_max_single_query(tracker, budget)
    assert violation is not None
    assert violation.constraint_name == "max_single_query"
    assert violation.fingerprint == "slow-q"

def test_max_single_query_none_skipped():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_max_single_query
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1h", window="5m")
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=999.0, fingerprint="q")
    assert check_max_single_query(tracker, budget) is None

def test_check_all_constraints_first_violation_wins():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import check_constraints
    from django_query_budget.tracker import BudgetTracker
    budget = Budget(total_runtime="1s", window="5m", max_queries=5)
    tracker = BudgetTracker(window_seconds=300.0)
    for _ in range(10):
        tracker.record(duration=1.0, fingerprint="q")
    violation = check_constraints(tracker, budget)
    assert violation is not None
    assert violation.constraint_name == "total_runtime"

def test_custom_constraint():
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation, check_constraints
    from django_query_budget.tracker import BudgetTracker
    def always_fail(tracker, budget):
        return Violation(constraint_name="custom", current_value=0, limit_value=0, fingerprint=None, message="always fails")
    budget = Budget(total_runtime="999h", window="5m", constraints=[always_fail])
    tracker = BudgetTracker(window_seconds=300.0)
    tracker.record(duration=0.001, fingerprint="q")
    violation = check_constraints(tracker, budget)
    assert violation is not None
    assert violation.constraint_name == "custom"
