from django.apps import AppConfig


class QueryBudgetConfig(AppConfig):
    name = "django_query_budget"
    label = "query_budget"
    verbose_name = "Query Budget"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.db.backends.signals import connection_created
        from django_query_budget.settings import get_config
        from django_query_budget.wrapper import query_budget_wrapper

        config = get_config()

        if config.default_budget:
            from django_query_budget.resolution import push_budget
            push_budget(config.default_budget)

        def install_wrapper(sender, connection, **kwargs):
            connection.execute_wrappers.append(query_budget_wrapper)

        connection_created.connect(install_wrapper)

        if config.sync_backend:
            self._start_sync_worker(config)

    def _start_sync_worker(self, config) -> None:
        import importlib
        import uuid

        module_path, class_name = config.sync_backend.rsplit(".", 1)
        module = importlib.import_module(module_path)
        backend_cls = getattr(module, class_name)

        if class_name == "RedisSyncBackend":
            import redis
            from django.conf import settings as django_settings
            redis_url = getattr(django_settings, "QUERY_BUDGET", {}).get("sync", {}).get("url", "redis://localhost:6379/0")
            client = redis.from_url(redis_url)
            window = config.default_budget.window_seconds if config.default_budget else 300.0
            backend = backend_cls(client=client, window_seconds=window)
        elif class_name == "DatabaseSyncBackend":
            backend = backend_cls()
        else:
            backend = backend_cls()

        from django_query_budget.sync.worker import SyncWorker

        worker = SyncWorker(
            backend=backend,
            interval=config.sync_interval,
            node_id=str(uuid.uuid4())[:8],
        )
        if config.default_budget:
            worker.add_scope("default", config.default_budget.window_seconds)
        for tag_name, tag_budget in config.tags.items():
            worker.add_scope(f"tag:{tag_name}", tag_budget.window_seconds)
        worker.start()
