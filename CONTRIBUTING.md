# Contributing

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Docker and Docker Compose (for database integration tests)

## Setup

```bash
git clone https://github.com/jlmorton/django-query-budget.git
cd django-query-budget
uv sync --extra dev
```

## Running tests

### SQLite (default, no Docker needed)

```bash
make test
```

This runs the full test suite (unit + integration) against an in-memory SQLite database. This is all you need for most development work.

### PostgreSQL

```bash
make test-postgres
```

Starts a Postgres 16 container via Docker Compose, installs `psycopg2-binary`, and runs all tests against it.

### MySQL

```bash
make test-mysql
```

Starts a MySQL 8.0 container, installs `mysqlclient`, and runs all tests.

### Redis

```bash
make test-redis
```

Starts a Redis 7 container and runs all tests, including the real Redis sync backend integration tests (which are skipped when Redis is unavailable).

### All backends

```bash
make test-all
```

Runs the full suite against SQLite, PostgreSQL, MySQL, and Redis sequentially. Requires Docker.

### Teardown

```bash
make clean
```

Stops and removes all Docker containers and volumes.

## Docker services

The `docker-compose.yml` provides:

| Service    | Image       | Port |
|------------|-------------|------|
| PostgreSQL | postgres:16 | 5432 |
| MySQL      | mysql:8.0   | 3306 |
| Redis      | redis:7     | 6379 |

You can start them manually with `docker compose up -d` and manage them independently of the Makefile.

## Project structure

```
src/django_query_budget/   # Library source
tests/                     # Test suite
  conftest.py              # Shared fixtures (registry cleanup, tracker cleanup)
  test_budget.py           # Budget dataclass and parse_duration
  test_fingerprint.py      # SQL fingerprinting
  test_tracker.py          # BudgetTracker
  test_constraints.py      # Constraint checkers
  test_actions.py          # Action registry
  test_hooks.py            # Hook system
  test_resolution.py       # Budget stack
  test_settings.py         # Settings parser
  test_wrapper.py          # Execute wrapper
  test_decorator.py        # Decorator / context manager
  test_middleware.py       # Middleware
  test_sync_redis.py       # Redis backend (mocked)
  test_sync_db.py          # Database backend (SQLite)
  test_sync_worker.py      # Sync worker
  test_e2e.py              # End-to-end integration
  test_performance.py      # Benchmarks
  test_integration_postgres.py  # PostgreSQL integration (skipped if unavailable)
  test_integration_mysql.py     # MySQL integration (skipped if unavailable)
  test_integration_redis.py     # Redis integration (skipped if unavailable)
```

## CI

GitHub Actions runs automatically on push and PR:

- **8 SQLite jobs** — Python 3.12/3.13 x Django 5.0/5.1/5.2/6.0
- **2 PostgreSQL jobs** — Django 5.2/6.0 with Postgres 16
- **2 MySQL jobs** — Django 5.2/6.0 with MySQL 8.0
- **1 Redis job** — Django 6.0 with Redis 7

## Building docs

```bash
uv run sphinx-build -b html docs docs/_build/html
open docs/_build/html/index.html
```
