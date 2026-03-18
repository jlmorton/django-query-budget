from django.db import models

class BudgetSnapshot(models.Model):
    scope_key = models.CharField(max_length=255, db_index=True)
    node_id = models.CharField(max_length=255)
    stats_json = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "query_budget"
        unique_together = [("scope_key", "node_id")]

    def __str__(self):
        return f"BudgetSnapshot({self.scope_key}, {self.node_id})"
