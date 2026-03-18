# Django Query Budget

**Database query budget enforcement for Django.**

Django Query Budget lets you define and enforce budgets on database query execution — total runtime, query count, and per-query duration — within configurable time windows. When a budget is exceeded, pluggable actions respond: log a warning, reject the query, or trigger custom behavior.

## Features

- **Budget enforcement** — Set limits on cumulative query runtime, query count, and individual query duration within rolling time windows
- **Multiple application methods** — Apply budgets via Django settings, decorators, or context managers
- **Pluggable actions** — Built-in `LOG` and `REJECT` actions, with a simple interface for custom actions
- **Hook system** — Sync and async hooks for observability (`on_query_executed`, `on_budget_violation`, `on_sync`)
- **Query fingerprinting** — Normalizes SQL queries into stable fingerprints for tracking
- **Cluster-wide sync** — Optional eventual consistency across processes via Redis or database backends
- **Async-safe** — Uses `contextvars.ContextVar` for correct behavior in both WSGI and ASGI deployments

## Quick Example

```python
# settings.py
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
}

MIDDLEWARE = [
    "django_query_budget.middleware.QueryBudgetMiddleware",
    # ...
]
```

```python
# views.py
from django_query_budget import query_budget

@query_budget(total_runtime="10s", window="1m", action="REJECT")
def expensive_report(request):
    return render(request, "report.html", {"data": Report.objects.all()})
```

```{toctree}
:maxdepth: 2
:caption: Contents

getting-started
configuration
usage
actions
hooks
sync
api
changelog
```
