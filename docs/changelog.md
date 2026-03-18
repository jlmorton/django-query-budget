# Changelog

## 0.1.0 (Unreleased)

Initial release.

- Budget enforcement with `total_runtime`, `max_queries`, and `max_single_query` constraints
- Rolling time window accumulation with automatic eviction
- `@query_budget` decorator and context manager
- `query_tag` context manager for tag-based budget resolution
- `QueryBudgetMiddleware` for per-request budget enforcement
- Built-in `LOG` and `REJECT` actions
- Custom action registration via `register_action()`
- Hook system with sync and async execution modes
- SQL fingerprinting for query normalization
- `ContextVar`-based budget stack (async-safe)
- `AppConfig.ready()` integration for non-request contexts
- Redis sync backend (`RedisSyncBackend`)
- Database sync backend (`DatabaseSyncBackend`)
- Background sync worker thread
