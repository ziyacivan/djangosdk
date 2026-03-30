import pytest
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.testing import FakeProvider, assert_prompt_sent, override_ai_provider


class EchoAgent(Agent):
    model = "fake-model"
    provider = "fake"


def test_basic_handle():
    fake = FakeProvider(text="Hello from fake!")
    with override_ai_provider(fake):
        agent = EchoAgent()
        response = agent.handle("Hi!")
    assert response.text == "Hello from fake!"
    assert len(fake.calls) == 1


def test_prompt_is_included():
    fake = FakeProvider(text="Got it.")
    with override_ai_provider(fake):
        agent = EchoAgent()
        agent.handle("Find order #123")
    assert_prompt_sent(fake, "Find order #123")


def test_thinking_response():
    fake = FakeProvider(text="The answer is 42.", thinking="Let me think...")
    with override_ai_provider(fake):
        agent = EchoAgent()
        response = agent.handle("What is the meaning of life?")
    assert response.thinking is not None
    assert response.thinking.content == "Let me think..."


def test_usage_info():
    from django_ai_sdk.agents.response import UsageInfo
    usage = UsageInfo(prompt_tokens=20, completion_tokens=10, total_tokens=30)
    fake = FakeProvider(text="OK", usage=usage)
    with override_ai_provider(fake):
        agent = EchoAgent()
        response = agent.handle("Test")
    assert response.usage.prompt_tokens == 20
    assert response.usage.total_tokens == 30
