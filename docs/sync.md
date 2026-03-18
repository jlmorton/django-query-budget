# Cluster Sync

By default, Django Query Budget tracks budgets per-process. For multi-process or multi-node deployments, you can enable cluster-wide budget sharing via a sync backend.

## Architecture

The sync system is **local-first**:

1. Each process maintains its own in-memory trackers
2. Enforcement always happens locally (no external calls on the query hot path)
3. A background thread periodically pushes local stats and pulls the cluster-wide view
4. The merged cluster view is used for enforcement

This means budgets are **eventually consistent** across the cluster. A single process could temporarily exceed its share of the budget before sync catches up. This is by design — the library is a budget/circuit-breaker, not a billing system.

## Redis backend

The recommended backend for production use:

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
    "sync": {
        "backend": "django_query_budget.sync.redis.RedisSyncBackend",
        "url": "redis://localhost:6379/0",
        "interval": 5,
    },
}
```

### How it works

- **Push:** Each node writes its stats to a Redis hash using `HSET`. Key format: `query_budget:{scope}:{window_bucket}`. Each node's stats are stored under its `node_id` field.
- **Pull:** `HGETALL` reads all nodes' stats, then sums them for the cluster-wide view.
- **TTL:** Keys expire automatically after the window duration plus a buffer.

No double-counting: each node's contribution is stored separately (not merged into a single counter).

## Database backend

For deployments without Redis:

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
    "sync": {
        "backend": "django_query_budget.sync.db.DatabaseSyncBackend",
        "interval": 10,
    },
}
```

This uses a `BudgetSnapshot` Django model to store stats. Run migrations after enabling:

```bash
python manage.py migrate query_budget
```

### How it works

- **Push:** `update_or_create` per node
- **Pull:** Aggregates across all nodes for each scope
- **Cleanup:** Expired rows should be cleaned up periodically (management command or scheduled task)

:::{note}
The database backend adds database queries for sync operations. Use a longer interval (e.g., 10-30 seconds) to minimize overhead.
:::

## Custom backends

Implement `BaseSyncBackend`:

```python
from django_query_budget.sync.base import BaseSyncBackend
from django_query_budget.tracker import BudgetStats

class MyBackend(BaseSyncBackend):
    def push(self, scope_key: str, stats: BudgetStats) -> None:
        """Write this node's stats to the shared store."""
        ...

    def pull(self, scope_key: str) -> BudgetStats | None:
        """Read the merged cluster-wide stats."""
        ...

    def clear(self, scope_key: str) -> None:
        """Remove stats for a scope."""
        ...
```

Then configure it:

```python
QUERY_BUDGET = {
    "sync": {
        "backend": "myapp.sync.MyBackend",
        "interval": 5,
    },
}
```

## Sync interval

The `interval` setting controls how often the background thread runs (in seconds). Trade-offs:

| Interval | Consistency | Overhead |
|----------|------------|----------|
| 1s | Near-real-time | Higher |
| 5s (default) | Good enough for most cases | Low |
| 30s | Significant lag | Minimal |

## Disabling sync

If `sync` is not configured, everything is process-local. This is the default and is perfectly valid for single-process deployments (e.g., development, small apps).
