import json
from unittest.mock import MagicMock
import pytest
from django_query_budget.tracker import BudgetStats

def test_redis_push():
    from django_query_budget.sync.redis import RedisSyncBackend
    mock_redis = MagicMock()
    backend = RedisSyncBackend(client=mock_redis, window_seconds=300.0)
    stats = BudgetStats(total_runtime=10.5, query_count=100, window_start=1000.0, window_end=1300.0, node_id="node-1")
    backend.push("default", stats)
    mock_redis.hset.assert_called_once()
    call_args = mock_redis.hset.call_args
    assert call_args[0][0].startswith("query_budget:default:")
    assert call_args[0][1] == "node-1"

def test_redis_pull_no_data():
    from django_query_budget.sync.redis import RedisSyncBackend
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {}
    backend = RedisSyncBackend(client=mock_redis, window_seconds=300.0)
    result = backend.pull("default")
    assert result is None

def test_redis_pull_aggregates():
    from django_query_budget.sync.redis import RedisSyncBackend
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "node-1": json.dumps({"total_runtime": 5.0, "query_count": 50}),
        "node-2": json.dumps({"total_runtime": 3.0, "query_count": 30}),
    }
    backend = RedisSyncBackend(client=mock_redis, window_seconds=300.0)
    result = backend.pull("default")
    assert result is not None
    assert result.total_runtime == pytest.approx(8.0)
    assert result.query_count == 80

def test_redis_clear():
    from django_query_budget.sync.redis import RedisSyncBackend
    mock_redis = MagicMock()
    backend = RedisSyncBackend(client=mock_redis, window_seconds=300.0)
    backend.clear("default")
    mock_redis.delete.assert_called_once()

def test_redis_push_sets_ttl():
    from django_query_budget.sync.redis import RedisSyncBackend
    mock_redis = MagicMock()
    backend = RedisSyncBackend(client=mock_redis, window_seconds=300.0)
    stats = BudgetStats(total_runtime=1.0, query_count=1, window_start=0, window_end=300.0, node_id="n1")
    backend.push("scope", stats)
    mock_redis.expire.assert_called_once()
    ttl = mock_redis.expire.call_args[0][1]
    assert ttl >= 300
