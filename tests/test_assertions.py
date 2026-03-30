from __future__ import annotations

import pytest

from djangosdk.testing import FakeProvider, override_ai_provider, assert_prompt_sent
from djangosdk.testing.assertions import (
    assert_tool_called,
    assert_model_used,
    assert_system_prompt_contains,
)
from djangosdk.agents.base import Agent


class TestAgent(Agent):
    provider = "fake"
    model = "fake-model"
    system_prompt = "You are a test assistant."


def test_assert_prompt_sent_passes():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Find order #999")
    assert_prompt_sent(fake, "Find order #999")


def test_assert_prompt_sent_fails_on_mismatch():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Hello")
    with pytest.raises(AssertionError, match="order #999"):
        assert_prompt_sent(fake, "order #999")


def test_assert_model_used_passes():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Test")
    assert_model_used(fake, "fake-model")


def test_assert_model_used_fails_on_wrong_model():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Test")
    with pytest.raises(AssertionError, match="gpt-4o"):
        assert_model_used(fake, "gpt-4o")


def test_assert_system_prompt_contains_passes():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Hello")
    assert_system_prompt_contains(fake, "test assistant")


def test_assert_system_prompt_contains_fails():
    fake = FakeProvider(text="OK")
    with override_ai_provider(fake):
        TestAgent().handle("Hello")
    with pytest.raises(AssertionError):
        assert_system_prompt_contains(fake, "something not in system prompt")


def test_assert_tool_called_passes():
    from djangosdk.agents.request import AgentRequest

    fake = FakeProvider(
        text="OK",
        tool_calls=[{"name": "lookup_order", "arguments": {"order_id": "123"}}],
    )
    # Simulate a request having been made so fake.calls is non-empty
    dummy_req = AgentRequest(
        messages=[{"role": "user", "content": "test"}],
        model="fake-model",
        provider="fake",
        system_prompt="",
        temperature=0.7,
        max_tokens=512,
    )
    fake.calls.append(dummy_req)
    assert_tool_called(fake, "lookup_order", order_id="123")


def test_assert_tool_called_fails_on_wrong_name():
    from djangosdk.agents.request import AgentRequest

    fake = FakeProvider(
        text="OK",
        tool_calls=[{"name": "cancel_order", "arguments": {}}],
    )
    dummy_req = AgentRequest(
        messages=[{"role": "user", "content": "test"}],
        model="fake-model",
        provider="fake",
        system_prompt="",
        temperature=0.7,
        max_tokens=512,
    )
    fake.calls.append(dummy_req)
    with pytest.raises(AssertionError):
        assert_tool_called(fake, "lookup_order")
