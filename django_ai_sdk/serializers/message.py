from __future__ import annotations

try:
    from rest_framework import serializers

    from django_ai_sdk.models.message import Message

    class MessageSerializer(serializers.ModelSerializer):
        class Meta:
            model = Message
            fields = [
                "id",
                "conversation",
                "role",
                "content",
                "tool_calls",
                "tool_call_id",
                "thinking_content",
                "prompt_tokens",
                "completion_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
                "cost_usd",
                "created_at",
            ]
            read_only_fields = ["id", "created_at"]

except ImportError:
    pass  # DRF is optional
