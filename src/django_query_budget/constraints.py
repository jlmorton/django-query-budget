from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django_query_budget.budget import Budget
    from django_query_budget.tracker import BudgetTracker

@dataclass(frozen=True)
class Violation:
    constraint_name: str
    current_value: Any
    limit_value: Any
    fingerprint: str | None
    message: str

def check_total_runtime(tracker: BudgetTracker, budget: Budget) -> Violation | None:
    current = tracker.total_runtime
    limit = budget.total_runtime_seconds
    if current > limit:
        return Violation(constraint_name="total_runtime", current_value=current, limit_value=limit, fingerprint=None, message=f"Total runtime {current:.1f}s exceeds limit of {limit:.1f}s")
    return None

def check_max_queries(tracker: BudgetTracker, budget: Budget) -> Violation | None:
    if budget.max_queries is None:
        return None
    current = tracker.query_count
    if current > budget.max_queries:
        return Violation(constraint_name="max_queries", current_value=current, limit_value=budget.max_queries, fingerprint=None, message=f"Query count {current} exceeds limit of {budget.max_queries}")
    return None

def check_max_single_query(tracker: BudgetTracker, budget: Budget) -> Violation | None:
    if budget.max_single_query is None:
        return None
    limit = budget.max_single_query.total_seconds()
    entry = tracker.last_query_entry
    if entry is None:
        return None
    if entry.duration > limit:
        return Violation(constraint_name="max_single_query", current_value=entry.duration, limit_value=limit, fingerprint=entry.fingerprint, message=f"Single query {entry.duration:.3f}s exceeds limit of {limit:.1f}s")
    return None

def check_constraints(tracker: BudgetTracker, budget: Budget, *, skip_single_query: bool = False) -> Violation | None:
    violation = check_total_runtime(tracker, budget)
    if violation:
        return violation
    violation = check_max_queries(tracker, budget)
    if violation:
        return violation
    if not skip_single_query:
        violation = check_max_single_query(tracker, budget)
        if violation:
            return violation
    for custom in budget.constraints:
        violation = custom(tracker, budget)
        if violation:
            return violation
    return None
