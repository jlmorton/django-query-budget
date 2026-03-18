from __future__ import annotations
import json
import time
from django_query_budget.sync.base import BaseSyncBackend
from django_query_budget.tracker import BudgetStats

class DatabaseSyncBackend(BaseSyncBackend):
    def push(self, scope_key: str, stats: BudgetStats) -> None:
        from django_query_budget.models import BudgetSnapshot
        value = json.dumps({"total_runtime": stats.total_runtime, "query_count": stats.query_count})
        BudgetSnapshot.objects.update_or_create(
            scope_key=scope_key, node_id=stats.node_id, defaults={"stats_json": value},
        )

    def pull(self, scope_key: str) -> BudgetStats | None:
        from django_query_budget.models import BudgetSnapshot
        snapshots = BudgetSnapshot.objects.filter(scope_key=scope_key)
        if not snapshots.exists():
            return None
        total_runtime = 0.0
        query_count = 0
        for snap in snapshots:
            data = json.loads(snap.stats_json)
            total_runtime += data["total_runtime"]
            query_count += data["query_count"]
        now = time.time()
        return BudgetStats(total_runtime=total_runtime, query_count=query_count, window_start=now, window_end=now, node_id="cluster")

    def clear(self, scope_key: str) -> None:
        from django_query_budget.models import BudgetSnapshot
        BudgetSnapshot.objects.filter(scope_key=scope_key).delete()
