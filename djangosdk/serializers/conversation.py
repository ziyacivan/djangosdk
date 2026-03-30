from __future__ import annotations

try:
    from rest_framework import serializers

    from djangosdk.models.conversation import Conversation

    class ConversationSerializer(serializers.ModelSerializer):
        class Meta:
            model = Conversation
            fields = [
                "id",
                "agent_class",
                "provider",
                "model",
                "metadata",
                "total_tokens",
                "total_cost_usd",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["id", "created_at", "updated_at"]

except ImportError:
    pass  # DRF is optional
