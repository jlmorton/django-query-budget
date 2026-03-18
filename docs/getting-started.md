# Getting Started

## Installation

```bash
pip install django-query-budget
```

For Redis-based cluster sync:

```bash
pip install django-query-budget[redis]
```

## Setup

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    "django_query_budget",
]
```

### 2. Add the middleware

```python
MIDDLEWARE = [
    "django_query_budget.middleware.QueryBudgetMiddleware",
    # ... other middleware
]
```

The middleware should be placed early in the middleware stack so it wraps the entire request lifecycle.

### 3. Configure a default budget

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
}
```

This sets a default budget that logs a warning when cumulative query runtime exceeds 30 minutes within any 5-minute window.

## Your first budget

With the above configuration, every request is automatically tracked. You can also apply more specific budgets using decorators:

```python
from django_query_budget import query_budget

@query_budget(total_runtime="5s", window="1m", action="REJECT")
def my_view(request):
    # If queries in this view exceed 5s cumulative runtime
    # within a 1-minute window, the next query will be rejected
    # with a QueryBudgetExceeded exception.
    ...
```

Or context managers:

```python
from django_query_budget import query_budget

def my_view(request):
    with query_budget(total_runtime="5s", window="1m", action="REJECT"):
        # Budget applies only within this block
        result = MyModel.objects.filter(active=True)
    # No budget enforcement here
    ...
```

## What happens when a budget is exceeded?

That depends on the configured `action`:

- **`"LOG"`** — Logs a warning via the `django.query_budget` logger. The query proceeds normally.
- **`"REJECT"`** — Raises `QueryBudgetExceeded` before the next query executes. The violating query that pushed the budget over the limit has already completed; it's the *next* query that gets blocked.

You can also [register custom actions](actions.md#custom-actions).

## Next steps

- [Configuration reference](configuration.md) — All settings options
- [Usage guide](usage.md) — Decorators, context managers, tags
- [Actions](actions.md) — Built-in and custom actions
- [Hooks](hooks.md) — Observability and extensibility
- [Cluster sync](sync.md) — Multi-process/multi-node support
