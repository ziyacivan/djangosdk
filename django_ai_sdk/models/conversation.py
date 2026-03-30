from __future__ import annotations

import uuid

from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_class = models.CharField(max_length=255)
    provider = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    total_tokens = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_ai_sdk"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["agent_class", "-created_at"])]

    def __str__(self) -> str:
        return f"Conversation({self.id}, {self.agent_class})"
