"""Tests for LiteLLMProvider using MockLiteLLMCompletion."""
from __future__ import annotations

import pytest
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.providers.litellm_provider import LiteLLMProvider
from django_ai_sdk.providers.schemas import ProviderConfig
from django_ai_sdk.testing.mock_litellm import (
    MockLiteLLMCompletion,
)


def _req(**kwargs) -> AgentRequest:
    defaults = dict(
        messages=[{"role": "user", "content": "hello"}],
        model="gpt-4o",
        provider="openai",
        system_prompt="",
        temperature=0.7,
        max_tokens=512,
        tools=[],
        output_schema=None,
        reasoning=None,
        enable_cache=False,
    )
    defaults.update(kwargs)
    return AgentRequest(**defaults)


# --- complete() ---

def test_complete_returns_text():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(text="Hello there!"):
        resp = provider.complete(req)
    assert resp.text == "Hello there!"
    assert resp.model == "gpt-4o"


def test_complete_captures_usage():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(prompt_tokens=20, completion_tokens=10):
        resp = provider.complete(req)
    assert resp.usage.prompt_tokens == 20
    assert resp.usage.completion_tokens == 10
    assert resp.usage.total_tokens == 30


def test_complete_captures_thinking():
    provider = LiteLLMProvider()
    req = _req(model="claude-3-7-sonnet-20250219")
    with MockLiteLLMCompletion(text="Answer", thinking="Let me think..."):
        resp = provider.complete(req)
    assert resp.thinking is not None
    assert resp.thinking.content == "Let me think..."


def test_complete_captures_tool_calls():
    provider = LiteLLMProvider()
    req = _req(
        tools=[{"type": "function", "function": {"name": "lookup"}}]
    )
    with MockLiteLLMCompletion(
        tool_calls=[{"id": "call_1", "name": "lookup", "arguments": {"id": "42"}}]
    ):
        resp = provider.complete(req)
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "lookup"
    assert resp.tool_calls[0]["arguments"] == {"id": "42"}


def test_complete_with_cache_tokens():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(cached_tokens=500):
        resp = provider.complete(req)
    assert resp.usage.cache_read_tokens == 500


def test_complete_raises_provider_error_on_litellm_exception():
    from unittest.mock import patch
    from django_ai_sdk.exceptions import ProviderError

    provider = LiteLLMProvider()
    req = _req()
    with patch("litellm.completion", side_effect=Exception("rate limited")):
        with pytest.raises(ProviderError, match="rate limited"):
            provider.complete(req)


# --- acomplete() ---

@pytest.mark.asyncio
async def test_acomplete_returns_text():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(text="Async hello!"):
        resp = await provider.acomplete(req)
    assert resp.text == "Async hello!"


@pytest.mark.asyncio
async def test_acomplete_captures_tool_calls():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(
        tool_calls=[{"id": "c1", "name": "my_tool", "arguments": {"x": 1}}]
    ):
        resp = await provider.acomplete(req)
    assert resp.tool_calls[0]["name"] == "my_tool"


# --- stream() ---

def test_stream_yields_text_chunks():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(stream_texts=["Hello", " World"]):
        chunks = list(provider.stream(req))
    text_chunks = [c for c in chunks if c.type == "text_delta"]
    done_chunks = [c for c in chunks if c.type == "done"]
    assert len(text_chunks) == 2
    assert text_chunks[0].text == "Hello"
    assert text_chunks[1].text == " World"
    assert len(done_chunks) == 1


def test_stream_yields_thinking_chunks():
    provider = LiteLLMProvider()
    req = _req(model="claude-3-7-sonnet-20250219")

    from django_ai_sdk.testing.mock_litellm import make_stream_chunks
    chunks = make_stream_chunks(["Answer"], thinking_prefix="My thought")

    from unittest.mock import MagicMock, patch
    stream_obj = MagicMock()
    stream_obj.__iter__ = lambda s: iter(chunks)
    stream_obj.usage = None

    with patch("litellm.completion", return_value=stream_obj):
        result = list(provider.stream(req))

    thinking = [c for c in result if c.type == "thinking_delta"]
    assert len(thinking) == 1
    assert thinking[0].text == "My thought"


# --- astream() ---

@pytest.mark.asyncio
async def test_astream_yields_chunks():
    provider = LiteLLMProvider()
    req = _req()
    with MockLiteLLMCompletion(stream_texts=["A", "B"]):
        chunks = [c async for c in provider.astream(req)]
    text_chunks = [c for c in chunks if c.type == "text_delta"]
    assert len(text_chunks) == 2


# --- provider_config injection ---

def test_complete_passes_api_key_from_config():
    config = ProviderConfig(name="openai", api_key="sk-test-key")
    provider = LiteLLMProvider(provider_config=config)
    req = _req()

    with MockLiteLLMCompletion() as mock:
        provider.complete(req)

    call_kwargs = mock.completion.call_args[1]
    assert call_kwargs.get("api_key") == "sk-test-key"


# --- End-to-end through Agent ---

class LiteLLMAgent(Agent):
    provider = "openai"
    model = "gpt-4o"
    system_prompt = "You are helpful."


def test_agent_uses_litellm_via_registry(settings):
    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "openai",
        "DEFAULT_MODEL": "gpt-4o",
        "PROVIDERS": {"openai": {"api_key": "sk-test"}},
        "CONVERSATION": {"PERSIST": False},
    }
    from django_ai_sdk.conf import ai_settings
    ai_settings.reload()
    from django_ai_sdk.apps import AiSdkConfig
    AiSdkConfig("django_ai_sdk", __import__("django_ai_sdk")).ready()

    with MockLiteLLMCompletion(text="I'm a real LLM response"):
        agent = LiteLLMAgent()
        response = agent.handle("Hello!")

    assert response.text == "I'm a real LLM response"

    settings.AI_SDK = {
        "DEFAULT_PROVIDER": "fake",
        "DEFAULT_MODEL": "fake-model",
        "PROVIDERS": {},
        "CONVERSATION": {"PERSIST": False},
    }
    ai_settings.reload()
