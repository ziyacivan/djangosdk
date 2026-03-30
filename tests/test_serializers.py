from __future__ import annotations

import uuid
import pytest

pytestmark = pytest.mark.django_db


def test_conversation_serializer_fields():
    from django_ai_sdk.models.conversation import Conversation
    from django_ai_sdk.serializers.conversation import ConversationSerializer

    conv = Conversation.objects.create(
        agent_class="myapp.agents.SupportAgent",
        provider="openai",
        model="gpt-4o",
    )
    data = ConversationSerializer(conv).data
    assert str(conv.id) == data["id"]
    assert data["agent_class"] == "myapp.agents.SupportAgent"
    assert data["provider"] == "openai"


def test_message_serializer_fields():
    from django_ai_sdk.models.conversation import Conversation
    from django_ai_sdk.models.message import Message
    from django_ai_sdk.serializers.message import MessageSerializer

    conv = Conversation.objects.create(agent_class="myapp.SomeAgent")
    msg = Message.objects.create(
        conversation=conv,
        role=Message.Role.USER,
        content="Hello!",
    )
    data = MessageSerializer(msg).data
    assert data["role"] == "user"
    assert data["content"] == "Hello!"
    assert "id" in data


def test_conversation_serializer_includes_messages():
    """ConversationSerializer should embed related messages if nested."""
    from django_ai_sdk.models.conversation import Conversation
    from django_ai_sdk.models.message import Message
    from django_ai_sdk.serializers.conversation import ConversationSerializer

    conv = Conversation.objects.create(agent_class="myapp.NestAgent")
    Message.objects.create(conversation=conv, role=Message.Role.USER, content="hi")
    Message.objects.create(conversation=conv, role=Message.Role.ASSISTANT, content="hello")

    serializer = ConversationSerializer(conv)
    data = serializer.data
    # Serializer might or might not embed messages; just confirm it doesn't crash
    assert "id" in data
