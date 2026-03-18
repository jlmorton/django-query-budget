from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_query_budget.tracker import BudgetStats

class BaseSyncBackend(ABC):
    @abstractmethod
    def push(self, scope_key: str, stats: BudgetStats) -> None: ...
    @abstractmethod
    def pull(self, scope_key: str) -> BudgetStats | None: ...
    @abstractmethod
    def clear(self, scope_key: str) -> None: ...
