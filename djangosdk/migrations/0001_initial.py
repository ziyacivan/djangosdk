from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("agent_class", models.CharField(max_length=255)),
                ("provider", models.CharField(blank=True, max_length=100)),
                ("model", models.CharField(blank=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("total_tokens", models.IntegerField(default=0)),
                ("total_cost_usd", models.DecimalField(decimal_places=8, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "app_label": "djangosdk",
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["agent_class", "-created_at"], name="django_ai_s_agent_c_idx")],
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("conversation", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="messages",
                    to="djangosdk.conversation",
                )),
                ("role", models.CharField(
                    choices=[
                        ("system", "System"),
                        ("user", "User"),
                        ("assistant", "Assistant"),
                        ("tool", "Tool"),
                        ("thinking", "Thinking"),
                    ],
                    max_length=20,
                )),
                ("content", models.TextField(blank=True)),
                ("tool_calls", models.JSONField(blank=True, null=True)),
                ("tool_call_id", models.CharField(blank=True, max_length=255, null=True)),
                ("thinking_content", models.TextField(blank=True)),
                ("prompt_tokens", models.IntegerField(blank=True, null=True)),
                ("completion_tokens", models.IntegerField(blank=True, null=True)),
                ("cache_read_tokens", models.IntegerField(blank=True, null=True)),
                ("cache_write_tokens", models.IntegerField(blank=True, null=True)),
                ("cost_usd", models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "djangosdk",
                "ordering": ["created_at"],
            },
        ),
    ]
