# Hooks

Hooks provide extension points for observability and custom logic. They fire at key moments in the query lifecycle without blocking query execution (by default).

## Hook events

### on_query_executed

Fires after every query completes:

```python
from django_query_budget import register_hook

def log_slow_queries(fingerprint, duration, tracker, **kwargs):
    if duration > 1.0:
        print(f"Slow query ({duration:.2f}s): {fingerprint}")

register_hook("on_query_executed", log_slow_queries)
```

Parameters: `fingerprint`, `duration`, `tracker`

### on_budget_violation

Fires when any constraint is breached, before the action:

```python
def send_metrics(budget, tracker, violation, **kwargs):
    statsd.increment("query_budget.violation", tags=[
        f"constraint:{violation.constraint_name}",
        f"scope:{budget.name or 'default'}",
    ])

register_hook("on_budget_violation", send_metrics)
```

Parameters: `budget`, `tracker`, `violation`

### on_sync

Fires after each sync cycle (only relevant with cluster sync):

```python
def log_cluster_stats(scope_key, local_stats, cluster_stats, **kwargs):
    if cluster_stats:
        print(f"Cluster total runtime for {scope_key}: {cluster_stats.total_runtime:.1f}s")

register_hook("on_sync", log_cluster_stats)
```

Parameters: `scope_key`, `local_stats`, `cluster_stats`

## Execution modes

Each hook runs in one of two modes:

### ASYNC (default)

Hooks are enqueued onto a bounded queue and executed by a dedicated background thread. This is the safe default — hooks never add latency to query execution.

```python
from django_query_budget import register_hook

# Async by default
register_hook("on_query_executed", my_callback)
```

If the queue is full (default max: 10,000), new events are dropped. A counter tracks dropped events.

### SYNC

Hooks execute inline on the calling thread. Use this only when the hook must run before the query lifecycle continues:

```python
from django_query_budget import register_hook, HookMode

register_hook("on_query_executed", my_callback, mode=HookMode.SYNC)
```

:::{warning}
Sync hooks add latency to every query. Keep them fast and never do I/O in a sync hook.
:::

## Class-based hooks

For hooks that need initialization or state:

```python
from django_query_budget import BaseHook, HookMode

class MetricsHook(BaseHook):
    mode = HookMode.ASYNC

    def __init__(self, statsd_client):
        self.client = statsd_client

    def __call__(self, fingerprint, duration, tracker, **kwargs):
        self.client.timing("query.duration", duration * 1000)

hook = MetricsHook(statsd_client=my_statsd)
register_hook("on_query_executed", hook)
```

## Error handling

Hook exceptions are caught and logged via the `django.query_budget.hooks` logger. They never propagate to the caller or affect query execution.

```python
LOGGING = {
    "loggers": {
        "django.query_budget.hooks": {
            "level": "ERROR",
            "handlers": ["console"],
        },
    },
}
```
