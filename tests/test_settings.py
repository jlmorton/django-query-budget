import pytest
from django.test import override_settings

def test_get_config_default():
    from django_query_budget.settings import get_config
    config = get_config()
    assert config.default_budget is None
    assert config.tags == {}
    assert config.sync_backend is None

@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "30m", "window": "5m", "action": "LOG"},
})
def test_get_config_with_default_budget():
    from django_query_budget.settings import get_config
    config = get_config()
    assert config.default_budget is not None
    assert config.default_budget.total_runtime_seconds == 1800.0
    assert config.default_budget.action == "LOG"

@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m"},
    "tags": {
        "reporting": {"total_runtime": "2h", "window": "10m", "max_queries": 5000, "action": "REJECT"},
    },
})
def test_get_config_with_tags():
    from django_query_budget.settings import get_config
    config = get_config()
    assert "reporting" in config.tags
    assert config.tags["reporting"].max_queries == 5000
    assert config.tags["reporting"].action == "REJECT"

@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m"},
    "sync": {"backend": "django_query_budget.sync.RedisSyncBackend", "interval": 10},
})
def test_get_config_with_sync():
    from django_query_budget.settings import get_config
    config = get_config()
    assert config.sync_backend == "django_query_budget.sync.RedisSyncBackend"
    assert config.sync_interval == 10

def test_get_config_no_setting():
    from django_query_budget.settings import get_config
    config = get_config()
    assert config.default_budget is None
