from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory

pytestmark = pytest.mark.django_db

factory = APIRequestFactory()


def _make_view_and_agent():
    from djangosdk.agents.base import Agent
    from djangosdk.views.chat import ChatAPIView

    class EchoAgent(Agent):
        provider = "fake"
        model = "fake-model"

    class EchoChatView(ChatAPIView):
        agent_class = EchoAgent

    return EchoChatView, EchoAgent


def test_chat_view_returns_200_with_text():
    from djangosdk.testing import FakeProvider, override_ai_provider

    EchoChatView, _ = _make_view_and_agent()
    fake = FakeProvider(text="Hello from view!")

    request = factory.post("/chat/", {"prompt": "Hi"}, format="json")

    with override_ai_provider(fake):
        response = EchoChatView.as_view()(request)

    assert response.status_code == 200
    assert response.data["text"] == "Hello from view!"


def test_chat_view_returns_400_without_prompt():
    EchoChatView, _ = _make_view_and_agent()

    request = factory.post("/chat/", {}, format="json")
    response = EchoChatView.as_view()(request)

    assert response.status_code == 400
    assert "error" in response.data


def test_chat_view_returns_500_on_provider_error():
    from djangosdk.testing import FakeProvider, override_ai_provider
    from djangosdk.exceptions import ProviderError

    EchoChatView, _ = _make_view_and_agent()
    bad = FakeProvider()
    bad.complete = lambda r: (_ for _ in ()).throw(ProviderError("API down"))

    request = factory.post("/chat/", {"prompt": "fail"}, format="json")

    with override_ai_provider(bad):
        response = EchoChatView.as_view()(request)

    assert response.status_code == 500
    assert "error" in response.data


def test_chat_view_includes_usage_in_response():
    from djangosdk.agents.response import UsageInfo
    from djangosdk.testing import FakeProvider, override_ai_provider

    EchoChatView, _ = _make_view_and_agent()
    usage = UsageInfo(prompt_tokens=20, completion_tokens=10, total_tokens=30)
    fake = FakeProvider(text="OK", usage=usage)

    request = factory.post("/chat/", {"prompt": "tokens?"}, format="json")

    with override_ai_provider(fake):
        response = EchoChatView.as_view()(request)

    assert response.data["usage"]["prompt_tokens"] == 20
    assert response.data["usage"]["total_tokens"] == 30


def test_chat_view_no_agent_class_raises():
    from djangosdk.views.chat import ChatAPIView

    class EmptyView(ChatAPIView):
        pass  # agent_class not set

    request = factory.post("/chat/", {"prompt": "test"}, format="json")

    with pytest.raises(NotImplementedError):
        EmptyView().get_agent(request)
