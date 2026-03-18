from __future__ import annotations
from dataclasses import dataclass, field
from django.conf import settings
from django_query_budget.budget import Budget


@dataclass
class QueryBudgetConfig:
    default_budget: Budget | None = None
    tags: dict[str, Budget] = field(default_factory=dict)
    sync_backend: str | None = None
    sync_interval: int = 5


def get_config() -> QueryBudgetConfig:
    raw = getattr(settings, "QUERY_BUDGET", None)
    if raw is None:
        return QueryBudgetConfig()
    config = QueryBudgetConfig()
    default_raw = raw.get("default")
    if default_raw:
        config.default_budget = Budget.from_dict(default_raw)
    tags_raw = raw.get("tags", {})
    for tag_name, tag_data in tags_raw.items():
        config.tags[tag_name] = Budget.from_dict(tag_data)
    sync_raw = raw.get("sync")
    if sync_raw:
        config.sync_backend = sync_raw.get("backend")
        config.sync_interval = sync_raw.get("interval", 5)
    return config
