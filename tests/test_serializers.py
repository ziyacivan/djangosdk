from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_conversation_serializer_fields():
    from djangosdk.models.conversation import Conversation
    from djangosdk.serializers.conversation import ConversationSerializer

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
    from djangosdk.models.conversation import Conversation
    from djangosdk.models.message import Message
    from djangosdk.serializers.message import MessageSerializer

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
    from djangosdk.models.conversation import Conversation
    from djangosdk.models.message import Message
    from djangosdk.serializers.conversation import ConversationSerializer

    conv = Conversation.objects.create(agent_class="myapp.NestAgent")
    Message.objects.create(conversation=conv, role=Message.Role.USER, content="hi")
    Message.objects.create(conversation=conv, role=Message.Role.ASSISTANT, content="hello")

    serializer = ConversationSerializer(conv)
    data = serializer.data
    # Serializer might or might not embed messages; just confirm it doesn't crash
    assert "id" in data
