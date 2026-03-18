"""Integration tests for RedisSyncBackend against a real Redis instance.

Requires: REDIS_URL env var or Redis running on localhost:6379.
Skipped automatically if Redis is unavailable.
"""
import json
import time

import pytest

from django_query_budget.tracker import BudgetStats

try:
    import redis as redis_lib

    _redis_client = redis_lib.from_url("redis://localhost:6379/0")
    _redis_client.ping()
    _redis_available = True
except Exception:
    _redis_available = False

pytestmark = pytest.mark.skipif(not _redis_available, reason="Redis not available")


@pytest.fixture
def redis_client():
    from django.conf import settings

    client = redis_lib.from_url(getattr(settings, "REDIS_URL", "redis://localhost:6379/0"))
    yield client
    # Clean up test keys
    for key in client.keys("query_budget:test-*"):
        client.delete(key)


@pytest.fixture
def backend(redis_client):
    from django_query_budget.sync.redis import RedisSyncBackend

    return RedisSyncBackend(client=redis_client, window_seconds=300.0)


class TestRealRedisPushPull:
    def test_push_and_pull_roundtrip(self, backend, redis_client):
        stats = BudgetStats(
            total_runtime=10.5,
            query_count=100,
            window_start=1000.0,
            window_end=1300.0,
            node_id="test-node-1",
        )
        backend.push("test-scope", stats)
        result = backend.pull("test-scope")
        assert result is not None
        assert result.total_runtime == pytest.approx(10.5)
        assert result.query_count == 100

    def test_multi_node_aggregation(self, backend, redis_client):
        stats1 = BudgetStats(
            total_runtime=5.0, query_count=50,
            window_start=0, window_end=300.0, node_id="test-node-1",
        )
        stats2 = BudgetStats(
            total_runtime=3.0, query_count=30,
            window_start=0, window_end=300.0, node_id="test-node-2",
        )
        backend.push("test-multi", stats1)
        backend.push("test-multi", stats2)

        result = backend.pull("test-multi")
        assert result is not None
        assert result.total_runtime == pytest.approx(8.0)
        assert result.query_count == 80

    def test_push_updates_existing_node(self, backend, redis_client):
        stats1 = BudgetStats(
            total_runtime=5.0, query_count=50,
            window_start=0, window_end=300.0, node_id="test-node-1",
        )
        stats2 = BudgetStats(
            total_runtime=10.0, query_count=100,
            window_start=0, window_end=300.0, node_id="test-node-1",
        )
        backend.push("test-update", stats1)
        backend.push("test-update", stats2)

        result = backend.pull("test-update")
        assert result is not None
        # Should have the updated values, not the sum of both
        assert result.total_runtime == pytest.approx(10.0)
        assert result.query_count == 100

    def test_clear_removes_data(self, backend, redis_client):
        stats = BudgetStats(
            total_runtime=5.0, query_count=50,
            window_start=0, window_end=300.0, node_id="test-node-1",
        )
        backend.push("test-clear", stats)
        assert backend.pull("test-clear") is not None
        backend.clear("test-clear")
        assert backend.pull("test-clear") is None

    def test_pull_nonexistent_returns_none(self, backend):
        assert backend.pull("test-nonexistent-scope") is None

    def test_ttl_is_set(self, backend, redis_client):
        stats = BudgetStats(
            total_runtime=1.0, query_count=1,
            window_start=0, window_end=300.0, node_id="test-node-1",
        )
        backend.push("test-ttl", stats)
        key = backend._key("test-ttl")
        ttl = redis_client.ttl(key)
        assert ttl > 0
        assert ttl <= 360  # window_seconds (300) + buffer (60)


class TestRealRedisSyncWorker:
    def test_sync_worker_with_real_redis(self, backend, redis_client):
        from django_query_budget.resolution import clear_trackers, get_tracker
        from django_query_budget.sync.worker import SyncWorker

        clear_trackers()
        tracker = get_tracker("test-worker", window_seconds=300.0)
        tracker.record(duration=1.0, fingerprint="q")

        worker = SyncWorker(backend=backend, interval=0.1, node_id="test-worker-node")
        worker.add_scope("test-worker", window_seconds=300.0)
        worker.start()
        time.sleep(0.5)
        worker.stop()

        result = backend.pull("test-worker")
        assert result is not None
        assert result.total_runtime >= 1.0
