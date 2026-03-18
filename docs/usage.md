# Usage

## Middleware

The `QueryBudgetMiddleware` applies the default budget to every request:

```python
MIDDLEWARE = [
    "django_query_budget.middleware.QueryBudgetMiddleware",
    # ...
]
```

When a request comes in, the middleware:
1. Reads the default budget from `QUERY_BUDGET["default"]`
2. Pushes it onto the budget stack
3. Installs the query execution wrapper
4. On request exit, pops the budget and cleans up

If no default budget is configured, the middleware passes through with no overhead.

## Decorator

Apply a budget to a specific view or function:

```python
from django_query_budget import query_budget

@query_budget(total_runtime="10s", window="1m", action="REJECT")
def expensive_view(request):
    ...
```

The decorator accepts the same options as a budget in settings: `total_runtime`, `window`, `action`, `max_queries`, `max_single_query`, and `name`.

### Automatic naming

When no `name` is provided, the decorator auto-generates one from the function's module and qualified name:

```python
@query_budget(total_runtime="10s", window="1m")
def myapp.views.my_view(request):
    # scope key: "named:myapp.views.my_view"
    ...
```

You can provide an explicit name:

```python
@query_budget(total_runtime="10s", window="1m", name="user-api")
def my_view(request):
    # scope key: "named:user-api"
    ...
```

## Context manager

Apply a budget to a block of code:

```python
from django_query_budget import query_budget

def my_view(request):
    with query_budget(total_runtime="5s", window="1m", action="REJECT"):
        # Budget enforced here
        results = MyModel.objects.filter(active=True)

    # No budget enforcement here
    other = OtherModel.objects.all()
```

## Nesting

Budgets nest properly. The innermost budget is always the active one:

```python
@query_budget(total_runtime="1h", window="5m", name="outer")
def my_view(request):
    # "outer" budget is active
    MyModel.objects.all()

    with query_budget(total_runtime="10s", window="1m", name="inner"):
        # "inner" budget is active
        ExpensiveModel.objects.all()

    # "outer" budget is active again
    MyModel.objects.count()
```

Each scope has its own tracker, so queries inside the inner block accumulate against the inner budget, not the outer one.

## Tagging queries

Tags let you apply different budgets to different categories of queries:

```python
from django_query_budget import query_tag

with query_tag("reporting"):
    # All queries here carry the "reporting" tag
    Report.objects.all()
```

When a tagged query executes, the wrapper looks up the tag in `QUERY_BUDGET["tags"]`. If a budget is defined for that tag, it's used for that query. If not, the current stack budget applies.

Tags do **not** push/pop the budget stack — they're per-query overrides resolved inside the execute wrapper.

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "LOG",
    },
    "tags": {
        "reporting": {
            "total_runtime": "2h",
            "window": "10m",
            "action": "REJECT",
        },
    },
}
```

## Budget resolution order

The active budget for a query is determined by:

1. **Default** — from `QUERY_BUDGET["default"]` (base of stack)
2. **Decorator/context manager** — pushes onto the stack; innermost wins
3. **Tag** — if the query has a tag with a defined budget, it overrides for that individual query

There is no merging. The active budget is the sole authority for all constraints.

## Non-request contexts

The library also works outside HTTP requests (Celery tasks, management commands). `AppConfig.ready()` installs the execute wrapper via Django's `connection_created` signal, so queries are tracked anywhere a database connection is used.

For non-request contexts, the default budget is applied automatically. You can override it with a context manager:

```python
from django_query_budget import query_budget

@app.task
def my_celery_task():
    with query_budget(total_runtime="5m", window="1m", action="LOG"):
        # Task-specific budget
        ...
```
