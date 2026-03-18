import json
import pytest
from django.test import TestCase
from django_query_budget.tracker import BudgetStats

class TestDatabaseSyncBackend(TestCase):
    def setUp(self):
        from django_query_budget.models import BudgetSnapshot
        BudgetSnapshot.objects.all().delete()

    def test_push_creates_snapshot(self):
        from django_query_budget.models import BudgetSnapshot
        from django_query_budget.sync.db import DatabaseSyncBackend
        backend = DatabaseSyncBackend()
        stats = BudgetStats(total_runtime=10.0, query_count=100, window_start=0, window_end=300.0, node_id="node-1")
        backend.push("default", stats)
        assert BudgetSnapshot.objects.filter(scope_key="default", node_id="node-1").exists()

    def test_push_updates_existing(self):
        from django_query_budget.models import BudgetSnapshot
        from django_query_budget.sync.db import DatabaseSyncBackend
        backend = DatabaseSyncBackend()
        stats1 = BudgetStats(total_runtime=5.0, query_count=50, window_start=0, window_end=300.0, node_id="node-1")
        stats2 = BudgetStats(total_runtime=10.0, query_count=100, window_start=0, window_end=300.0, node_id="node-1")
        backend.push("default", stats1)
        backend.push("default", stats2)
        assert BudgetSnapshot.objects.filter(scope_key="default").count() == 1
        snap = BudgetSnapshot.objects.get(scope_key="default", node_id="node-1")
        data = json.loads(snap.stats_json)
        assert data["total_runtime"] == 10.0

    def test_pull_no_data(self):
        from django_query_budget.sync.db import DatabaseSyncBackend
        backend = DatabaseSyncBackend()
        assert backend.pull("nonexistent") is None

    def test_pull_aggregates(self):
        from django_query_budget.models import BudgetSnapshot
        from django_query_budget.sync.db import DatabaseSyncBackend
        BudgetSnapshot.objects.create(scope_key="default", node_id="node-1", stats_json=json.dumps({"total_runtime": 5.0, "query_count": 50}))
        BudgetSnapshot.objects.create(scope_key="default", node_id="node-2", stats_json=json.dumps({"total_runtime": 3.0, "query_count": 30}))
        backend = DatabaseSyncBackend()
        result = backend.pull("default")
        assert result is not None
        assert result.total_runtime == pytest.approx(8.0)
        assert result.query_count == 80

    def test_clear(self):
        from django_query_budget.models import BudgetSnapshot
        from django_query_budget.sync.db import DatabaseSyncBackend
        BudgetSnapshot.objects.create(scope_key="default", node_id="node-1", stats_json=json.dumps({"total_runtime": 5.0, "query_count": 50}))
        backend = DatabaseSyncBackend()
        backend.clear("default")
        assert not BudgetSnapshot.objects.filter(scope_key="default").exists()
