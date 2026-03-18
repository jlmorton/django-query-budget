from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation
    from django_query_budget.tracker import BudgetTracker

logger = logging.getLogger("django.query_budget")
ActionCallable = Callable[["Budget", "BudgetTracker", "Violation"], None]
_registry: dict[str, ActionCallable] = {}

class QueryBudgetExceeded(Exception):
    def __init__(self, violation: Violation) -> None:
        self.violation = violation
        super().__init__(violation.message)

def register_action(name: str, action: ActionCallable) -> None:
    _registry[name] = action

def get_action(name: str) -> ActionCallable:
    if name not in _registry:
        raise KeyError(f"Unknown action: {name!r}. Registered: {list(_registry.keys())}")
    return _registry[name]

def log_action(budget: Budget, tracker: BudgetTracker, violation: Violation) -> None:
    logger.warning("Query budget violated: %s [scope=%s, action=%s]", violation.message, budget.name or "default", budget.action)

def reject_action(budget: Budget, tracker: BudgetTracker, violation: Violation) -> None:
    raise QueryBudgetExceeded(violation)

register_action("LOG", log_action)
register_action("REJECT", reject_action)
