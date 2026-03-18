# Actions

Actions are triggered when a budget constraint is violated. They determine what happens when a query exceeds the budget.

## Built-in actions

### LOG

Logs a warning via the `django.query_budget` logger:

```
WARNING Query budget violated: Total runtime 35.2s exceeds limit of 30.0s [scope=default, action=LOG]
```

The query proceeds normally. This is the default action.

To capture these in your logging configuration:

```python
LOGGING = {
    "loggers": {
        "django.query_budget": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    },
}
```

### REJECT

Raises `QueryBudgetExceeded` before the next query executes:

```python
from django_query_budget import QueryBudgetExceeded

try:
    MyModel.objects.all()
except QueryBudgetExceeded as e:
    print(e.violation.message)
    print(e.violation.constraint_name)  # "total_runtime", "max_queries", etc.
```

`QueryBudgetExceeded` is a subclass of `Exception` (not `DatabaseError`) to avoid confusing Django's transaction management.

**Important:** REJECT prevents the *next* query after the budget is exceeded. The query that pushed the budget over the limit has already completed. For `max_single_query`, the slow query has already finished — the action fires after the fact.

## Custom actions

Register custom actions with `register_action`:

```python
from django_query_budget import register_action

def slack_alert(budget, tracker, violation):
    """Send a Slack alert when the budget is exceeded."""
    send_slack_message(
        channel="#db-alerts",
        text=f"Query budget exceeded: {violation.message}",
    )

register_action("SLACK_ALERT", slack_alert)
```

Then use it in your configuration:

```python
QUERY_BUDGET = {
    "default": {
        "total_runtime": "30m",
        "window": "5m",
        "action": "SLACK_ALERT",
    },
}
```

### Action signature

```python
def my_action(budget: Budget, tracker: BudgetTracker, violation: Violation) -> None:
    ...
```

Parameters:
- `budget` — The `Budget` that was violated
- `tracker` — The `BudgetTracker` with current stats
- `violation` — A `Violation` dataclass with details:
  - `constraint_name` — `"total_runtime"`, `"max_queries"`, or `"max_single_query"`
  - `current_value` — The measured value
  - `limit_value` — The budget limit
  - `fingerprint` — The query fingerprint (for `max_single_query` violations)
  - `message` — Human-readable description

### Custom constraints

You can add custom constraints that are checked alongside the built-in ones:

```python
from django_query_budget.constraints import Violation

def max_slow_queries(tracker, budget):
    """Fail if more than 3 queries took over 1 second."""
    slow_count = sum(
        1 for entry in tracker._entries
        if entry.duration > 1.0
    )
    if slow_count > 3:
        return Violation(
            constraint_name="max_slow_queries",
            current_value=slow_count,
            limit_value=3,
            fingerprint=None,
            message=f"{slow_count} slow queries (>1s) exceeds limit of 3",
        )
    return None

# Pass constraints when creating a budget
@query_budget(
    total_runtime="1h",
    window="5m",
    constraints=[max_slow_queries],
)
def my_view(request):
    ...
```
