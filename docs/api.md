# API Reference

## Public API

The following are importable from `django_query_budget`:

### query_budget

```python
from django_query_budget import query_budget
```

Decorator and context manager for applying query budgets.

**As a decorator:**

```python
@query_budget(total_runtime="10s", window="1m", action="REJECT", name="my-view")
def my_view(request):
    ...
```

**As a context manager:**

```python
with query_budget(total_runtime="10s", window="1m"):
    MyModel.objects.all()
```

**Parameters:**

- `total_runtime` (str | timedelta) — Required. Max cumulative query time in the window.
- `window` (str | timedelta) — Required. Rolling time window.
- `action` (str) — Action on violation. Default: `"LOG"`.
- `max_queries` (int) — Max query count in the window. Optional.
- `max_single_query` (str | timedelta) — Max single query duration. Optional.
- `name` (str) — Explicit scope name. Auto-generated from function name if omitted.
- `constraints` (list[Callable]) — Custom constraint callables. Optional.

---

### query_tag

```python
from django_query_budget import query_tag
```

Context manager for tagging queries:

```python
with query_tag("reporting"):
    Report.objects.all()
```

Tags are looked up in `QUERY_BUDGET["tags"]` for per-query budget overrides.

---

### QueryBudgetExceeded

```python
from django_query_budget import QueryBudgetExceeded
```

Exception raised by the `REJECT` action. Subclass of `Exception` (not `DatabaseError`).

**Attributes:**

- `violation` — The `Violation` dataclass with details about the breach.

---

### register_action

```python
from django_query_budget import register_action

register_action("MY_ACTION", my_action_callable)
```

Register a custom action by name.

---

### register_hook

```python
from django_query_budget import register_hook, ExecutionMode

register_hook("on_query_executed", my_callback, mode=ExecutionMode.ASYNC)
```

Register a hook for an event. See [Hooks](hooks.md) for details.

---

### ExecutionMode

```python
from django_query_budget import ExecutionMode

ExecutionMode.SYNC   # Execute inline
ExecutionMode.ASYNC  # Execute on background thread (default)
```

`HookMode` is available as a backwards-compatible alias for `ExecutionMode`.

---

### BaseHook

```python
from django_query_budget import BaseHook, ExecutionMode

class MyHook(BaseHook):
    mode = ExecutionMode.ASYNC

    def __call__(self, **kwargs):
        ...
```

Base class for class-based hooks.

---

## Internal modules

These are not part of the public API but are documented for advanced use cases.

### django_query_budget.budget

`Budget` dataclass and `parse_duration()` utility.

### django_query_budget.tracker

`BudgetTracker` (in-memory accumulator) and `BudgetStats` (sync snapshot).

### django_query_budget.constraints

`Violation` dataclass, `check_total_runtime()`, `check_max_queries()`, `check_max_single_query()`, `check_constraints()`.

### django_query_budget.fingerprint

`fingerprint_sql(sql, *, lowercase=True)` — Normalize SQL into a stable fingerprint.

### django_query_budget.resolution

`push_budget()`, `pop_budget()`, `current_budget()`, `push_tag()`, `pop_tag()`, `current_tag()`, `get_tracker()`, `clear_trackers()`.

### django_query_budget.middleware

`QueryBudgetMiddleware` — Django middleware class.

### django_query_budget.wrapper

`query_budget_wrapper()` — The execute wrapper installed on database connections.

### django_query_budget.sync

`BaseSyncBackend`, `RedisSyncBackend`, `DatabaseSyncBackend`, `SyncWorker`.
