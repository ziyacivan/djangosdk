from __future__ import annotations

from django_ai_sdk.providers.cache import PromptCacheMiddleware
from django_ai_sdk.agents.request import AgentRequest


def _req(model: str, messages: list, enable_cache: bool = True) -> AgentRequest:
    return AgentRequest(
        messages=messages,
        model=model,
        provider="anthropic",
        system_prompt="",
        temperature=0.7,
        max_tokens=512,
        tools=[],
        output_schema=None,
        reasoning=None,
        enable_cache=enable_cache,
    )


def test_cache_disabled_returns_messages_unchanged():
    mw = PromptCacheMiddleware()
    msgs = [{"role": "user", "content": "Hello"}]
    result = mw.apply(_req("claude-3-5-sonnet", msgs, enable_cache=False))
    assert result == msgs


def test_anthropic_cache_applied_to_long_messages():
    mw = PromptCacheMiddleware()
    long_content = "x" * 1025
    msgs = [{"role": "user", "content": long_content}]
    result = mw.apply(_req("claude-3-5-sonnet", msgs, enable_cache=True))
    # Long content should be wrapped with cache_control
    assert isinstance(result[0]["content"], list)
    assert result[0]["content"][0]["cache_control"]["type"] == "ephemeral"


def test_short_messages_not_cached():
    mw = PromptCacheMiddleware()
    msgs = [{"role": "user", "content": "short"}]
    result = mw.apply(_req("claude-3-5-sonnet", msgs, enable_cache=True))
    # Short content passes through as string
    assert isinstance(result[0]["content"], str)


def test_non_anthropic_model_no_cache_markers():
    mw = PromptCacheMiddleware()
    msgs = [{"role": "user", "content": "x" * 2000}]
    result = mw.apply(_req("gpt-4o", msgs, enable_cache=True))
    # GPT-4o uses automatic caching, no explicit markers needed
    assert isinstance(result[0]["content"], str)


def test_build_system_with_cache_anthropic():
    mw = PromptCacheMiddleware()
    system = mw.build_system_with_cache("You are helpful.", "claude-3-5-sonnet")
    assert isinstance(system, list)
    assert system[0]["cache_control"]["type"] == "ephemeral"
    assert system[0]["text"] == "You are helpful."


def test_build_system_with_cache_gpt_returns_string():
    mw = PromptCacheMiddleware()
    system = mw.build_system_with_cache("You are helpful.", "gpt-4o")
    assert system == "You are helpful."


def test_build_system_empty_prompt():
    mw = PromptCacheMiddleware()
    result = mw.build_system_with_cache("", "claude-3-5-sonnet")
    assert result == ""
