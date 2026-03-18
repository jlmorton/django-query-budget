"""Integration tests against a real MySQL database.

Requires: DATABASE_BACKEND=mysql and a running MySQL instance.
Skipped automatically if not configured or unavailable.
"""
import os

import pytest
from django.db import connection
from django.test import TransactionTestCase, override_settings

from django_query_budget import QueryBudgetExceeded, query_budget, query_tag
from django_query_budget.resolution import clear_trackers, get_tracker

pytestmark = pytest.mark.skipif(
    os.environ.get("DATABASE_BACKEND") != "mysql",
    reason="DATABASE_BACKEND != mysql",
)


@override_settings(QUERY_BUDGET={
    "default": {"total_runtime": "1h", "window": "5m", "action": "LOG"},
    "tags": {"reporting": {"total_runtime": "10s", "window": "5m", "action": "REJECT"}},
})
class TestMySQLIntegration(TransactionTestCase):
    def setUp(self):
        clear_trackers()
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS test_mysql_item "
                "(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), value INT)"
            )

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_mysql_item")

    def test_insert_and_query_tracking(self):
        with query_budget(total_runtime="1h", window="5m", name="mysql-tracking"):
            with connection.cursor() as cursor:
                for i in range(5):
                    cursor.execute(
                        "INSERT INTO test_mysql_item (name, value) VALUES (%s, %s)",
                        [f"item-{i}", i * 10],
                    )
                cursor.execute("SELECT * FROM test_mysql_item WHERE value > %s", [0])
                rows = cursor.fetchall()
        tracker = get_tracker("named:mysql-tracking", window_seconds=300.0)
        assert tracker.query_count >= 6
        assert len(rows) >= 4

    def test_reject_on_mysql(self):
        tracker = get_tracker("named:mysql-reject", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="1s", window="5m", action="REJECT", name="mysql-reject"):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")

    def test_fingerprinting_mysql_queries(self):
        """Verify fingerprinting works with MySQL-style queries."""
        from django_query_budget.fingerprint import fingerprint_sql

        sql = "SELECT * FROM test_mysql_item WHERE name = 'alice' AND value = 42"
        fp = fingerprint_sql(sql)
        assert "?" in fp
        assert "alice" not in fp
        assert "42" not in fp

    def test_tag_based_resolution_mysql(self):
        tracker = get_tracker("tag:reporting", window_seconds=300.0)
        tracker.record(duration=100.0, fingerprint="setup")
        with pytest.raises(QueryBudgetExceeded):
            with query_budget(total_runtime="1h", window="5m", name="mysql-tag"):
                with query_tag("reporting"):
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")

    def test_db_sync_backend_on_mysql(self):
        """Verify DatabaseSyncBackend works with MySQL."""
        from django_query_budget.models import BudgetSnapshot
        from django_query_budget.sync.db import DatabaseSyncBackend
        from django_query_budget.tracker import BudgetStats

        backend = DatabaseSyncBackend()
        stats = BudgetStats(
            total_runtime=10.0, query_count=100,
            window_start=0, window_end=300.0, node_id="mysql-node-1",
        )
        backend.push("mysql-scope", stats)
        assert BudgetSnapshot.objects.filter(scope_key="mysql-scope").exists()

        result = backend.pull("mysql-scope")
        assert result is not None
        assert result.total_runtime == pytest.approx(10.0)

        backend.clear("mysql-scope")
        assert not BudgetSnapshot.objects.filter(scope_key="mysql-scope").exists()
