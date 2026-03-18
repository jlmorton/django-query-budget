"""Shared test fixtures for django-query-budget."""
import pytest

from django_query_budget.actions import _registry as _action_registry
from django_query_budget.hooks import _registry as _hook_registry
from django_query_budget.resolution import clear_trackers


@pytest.fixture(autouse=True)
def _clean_registries():
    """Snapshot and restore global registries between tests."""
    action_snapshot = dict(_action_registry)
    hook_snapshot = {k: list(v) for k, v in _hook_registry.items()}
    yield
    _action_registry.clear()
    _action_registry.update(action_snapshot)
    _hook_registry.clear()
    _hook_registry.update(hook_snapshot)


@pytest.fixture(autouse=True)
def _clean_trackers():
    """Clear tracker state between tests."""
    clear_trackers()
    yield
    clear_trackers()
