from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _make_agent_class():
    from djangosdk.agents.base import Agent

    class ChatAgent(Agent):
        provider = "fake"
        model = "fake-model"
        system_prompt = "You are helpful."

    return ChatAgent


def test_start_conversation_creates_db_record():
    from djangosdk.models.conversation import Conversation

    ChatAgent = _make_agent_class()
    agent = ChatAgent()
    conv = agent.start_conversation()

    assert Conversation.objects.filter(id=conv.id).exists()
    assert conv.agent_class.endswith("ChatAgent")


def test_with_conversation_binds_id():

    ChatAgent = _make_agent_class()
    agent = ChatAgent()
    conv = agent.start_conversation()

    bound = agent.with_conversation(conv.id)
    assert str(bound._conversation_id) == str(conv.id)
    # Original agent is not mutated
    assert agent._conversation_id != bound._conversation_id or agent is not bound


def test_handle_persists_messages_when_persist_enabled(settings):
    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "fake",
        "DEFAULT_MODEL": "fake-model",
        "PROVIDERS": {},
        "CONVERSATION": {"PERSIST": True},
    }
    from djangosdk.conf import ai_settings
    ai_settings.reload()

    from djangosdk.models.message import Message
    from djangosdk.testing import FakeProvider, override_ai_provider

    ChatAgent = _make_agent_class()
    agent = ChatAgent()
    conv = agent.start_conversation()
    bound = agent.with_conversation(conv.id)

    fake = FakeProvider(text="Persisted response")
    with override_ai_provider(fake):
        bound.handle("Remember this")

    msgs = list(Message.objects.filter(conversation=conv).order_by("created_at"))
    roles = [m.role for m in msgs]
    assert "user" in roles
    assert "assistant" in roles

    # Restore settings
    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "fake",
        "DEFAULT_MODEL": "fake-model",
        "PROVIDERS": {},
        "CONVERSATION": {"PERSIST": False},
    }
    ai_settings.reload()


def test_load_conversation_messages_returns_history(settings):
    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "fake",
        "DEFAULT_MODEL": "fake-model",
        "PROVIDERS": {},
        "CONVERSATION": {"PERSIST": True, "MAX_HISTORY": 50},
    }
    from djangosdk.conf import ai_settings
    ai_settings.reload()

    from djangosdk.testing import FakeProvider, override_ai_provider

    ChatAgent = _make_agent_class()
    agent = ChatAgent()
    conv = agent.start_conversation()
    bound = agent.with_conversation(conv.id)

    fake = FakeProvider(text="Turn 1 reply")
    with override_ai_provider(fake):
        bound.handle("Turn 1")

    # On the second call the history should be included in the request
    fake2 = FakeProvider(text="Turn 2 reply")
    with override_ai_provider(fake2):
        bound.handle("Turn 2")

    # Second request must include prior messages in context
    assert len(fake2.calls) == 1
    all_roles = [m["role"] for m in fake2.calls[0].messages]
    assert "user" in all_roles

    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "fake",
        "DEFAULT_MODEL": "fake-model",
        "PROVIDERS": {},
        "CONVERSATION": {"PERSIST": False},
    }
    ai_settings.reload()
