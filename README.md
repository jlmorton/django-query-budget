# Django Query Budget

Database query budget enforcement for Django.

Define budgets on cumulative query runtime, query count, and per-query duration within rolling time windows. When a budget is exceeded, pluggable actions respond — log, reject, or custom.

## Features

- Budget enforcement via settings, decorators, or context managers
- Built-in `LOG` and `REJECT` actions with custom action support
- Async-safe hook system for observability
- SQL fingerprinting for query normalization
- Optional cluster-wide sync via Redis or database backends
- Works with Django 5.0+ (WSGI and ASGI)

## Quick start

```bash
pip install django-query-budget
```

```python
# settings.py
INSTALLED_APPS = ["django_query_budget", ...]

MIDDLEWARE = ["django_query_budget.middleware.QueryBudgetMiddleware", ...]

QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
}
```

```python
# views.py
from django_query_budget import query_budget

@query_budget(total_runtime="10s", window="1m", action="REJECT")
def expensive_report(request):
    ...
```

## Documentation

Full documentation at **[django-query-budget.readthedocs.io](https://django-query-budget.readthedocs.io/en/latest/)**.

## License

MIT
