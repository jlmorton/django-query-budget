# Configuration

All configuration is done via the `QUERY_BUDGET` dictionary in your Django settings.

## Full example

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
        "max_queries": 10000,
        "max_single_query": "30s",
    },
    "tags": {
        "reporting": {
            "total_runtime": "2h",
            "window": "10m",
            "max_queries": 5000,
            "action": "REJECT",
        },
        "background": {
            "total_runtime": "1h",
            "window": "5m",
            "action": "LOG",
        },
    },
    "sync": {
        "backend": "django_query_budget.sync.RedisSyncBackend",
        "url": "redis://localhost:6379/0",
        "interval": 5,
    },
}
```

## Budget options

Each budget (whether `default` or a tag budget) accepts these options:

`total_runtime`
: **Required.** Maximum cumulative query execution time within the window. Accepts duration strings (`"30s"`, `"5m"`, `"1h"`, `"1h30m"`) or a number of seconds.

`window`
: **Required.** Rolling time window for accumulation. Same format as `total_runtime`.

`action`
: Action to take when the budget is exceeded. Default: `"LOG"`. Built-in options: `"LOG"`, `"REJECT"`. See [Actions](actions.md).

`max_queries`
: Maximum number of queries allowed within the window. Optional — omit to not limit query count.

`max_single_query`
: Maximum duration for any single query. Optional. This is a post-execution check — the slow query has already completed by the time the violation is detected.

## Duration strings

Duration values accept these formats:

| Format | Example | Equivalent |
|--------|---------|------------|
| Seconds | `"30s"` | 30 seconds |
| Minutes | `"5m"` | 5 minutes |
| Hours | `"1h"` | 1 hour |
| Combined | `"1h30m"` | 1 hour 30 minutes |
| Integer | `60` | 60 seconds |

## Tags

Tags let you define separate budgets for different categories of queries. See [Tagging queries](usage.md#tagging-queries) for how to apply tags.

## Sync

The `sync` section configures cluster-wide budget sharing. See [Cluster sync](sync.md) for details.

`backend`
: Dotted path to the sync backend class. Built-in options:
  - `"django_query_budget.sync.redis.RedisSyncBackend"`
  - `"django_query_budget.sync.db.DatabaseSyncBackend"`

`interval`
: Sync interval in seconds. Default: `5`. How often the background thread pushes local stats and pulls the cluster-wide view.

`url`
: Redis URL (only for `RedisSyncBackend`). Default: `"redis://localhost:6379/0"`.

## No configuration

If `QUERY_BUDGET` is not set or is empty, the library is effectively a no-op. No overhead is added to query execution.
