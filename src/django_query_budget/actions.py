from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from django_query_budget.hooks import HookMode

if TYPE_CHECKING:
    from django_query_budget.budget import Budget
    from django_query_budget.constraints import Violation
    from django_query_budget.tracker import BudgetTracker

logger = logging.getLogger("django.query_budget")

ActionCallable = Callable[["Budget", "BudgetTracker", "Violation"], None]

# Registry: name -> (callable, mode)
_registry: dict[str, tuple[ActionCallable, HookMode]] = {}


class QueryBudgetExceeded(Exception):
    """Raised when a query budget is exceeded and the action is REJECT."""

    def __init__(self, violation: Violation) -> None:
        self.violation = violation
        super().__init__(violation.message)


def register_action(
    name: str,
    action: ActionCallable,
    mode: HookMode = HookMode.ASYNC,
) -> None:
    """Register a named action callable.

    Args:
        name: Action name (used in budget config).
        action: Callable invoked on violation.
        mode: SYNC (inline) or ASYNC (enqueued to background thread).
              Custom actions default to ASYNC. REJECT is always SYNC.
    """
    _registry[name] = (action, mode)


def get_action(name: str) -> tuple[ActionCallable, HookMode]:
    """Look up a registered action by name. Returns (callable, mode)."""
    if name not in _registry:
        raise KeyError(f"Unknown action: {name!r}. Registered: {list(_registry.keys())}")
    return _registry[name]


def log_action(budget: Budget, tracker: BudgetTracker, violation: Violation) -> None:
    """Built-in LOG action: logs the violation at WARNING level."""
    logger.warning(
        "Query budget violated: %s [scope=%s, action=%s]",
        violation.message,
        budget.name or "default",
        budget.action,
    )


def reject_action(budget: Budget, tracker: BudgetTracker, violation: Violation) -> None:
    """Built-in REJECT action: raises QueryBudgetExceeded."""
    raise QueryBudgetExceeded(violation)


# Register built-in actions — both are SYNC by default
register_action("LOG", log_action, mode=HookMode.SYNC)
register_action("REJECT", reject_action, mode=HookMode.SYNC)
