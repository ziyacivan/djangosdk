from __future__ import annotations

import pytest

from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.exceptions import ConfigurationError, ProviderError
from django_ai_sdk.providers.registry import ProviderRegistry
from django_ai_sdk.providers.schemas import ReasoningConfig
from django_ai_sdk.providers.cache import PromptCacheMiddleware
from django_ai_sdk.providers.litellm_provider import (
    LiteLLMProvider,
    _is_reasoning_model,
    _build_litellm_params,
)
from django_ai_sdk.testing import FakeProvider


# --- _is_reasoning_model ---

def test_openai_o3_is_reasoning():
    is_r, family = _is_reasoning_model("o3-mini")
    assert is_r is True
    assert family == "openai"


def test_deepseek_r1_is_reasoning():
    is_r, family = _is_reasoning_model("deepseek-r1")
    assert is_r is True
    assert family == "deepseek"


def test_claude_37_is_reasoning():
    is_r, family = _is_reasoning_model("claude-3-7-sonnet-20250219")
    assert is_r is True
    assert family == "anthropic"


def test_gpt4o_is_not_reasoning():
    is_r, family = _is_reasoning_model("gpt-4o")
    assert is_r is False
    assert family == ""


# --- _build_litellm_params ---

def _make_request(**kwargs) -> AgentRequest:
    defaults = dict(
        messages=[{"role": "user", "content": "hi"}],
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


def test_build_params_basic():
    req = _make_request()
    params = _build_litellm_params(req)
    assert params["model"] == "gpt-4o"
    assert params["temperature"] == 0.7
    assert "tools" not in params  # empty list → not injected


def test_build_params_with_tools():
    schema = [{"type": "function", "function": {"name": "lookup"}}]
    req = _make_request(tools=schema)
    params = _build_litellm_params(req)
    assert params["tools"] == schema
    assert params["tool_choice"] == "auto"


def test_build_params_openai_structured_output():
    req = _make_request(model="gpt-4o", output_schema={"type": "object"})
    params = _build_litellm_params(req)
    assert params["response_format"]["type"] == "json_schema"


def test_build_params_gemini_structured_output():
    req = _make_request(model="gemini-2.0-flash", output_schema={"type": "object"})
    params = _build_litellm_params(req)
    assert "response_schema" in params


def test_inject_openai_reasoning():
    rc = ReasoningConfig(effort="high")
    req = _make_request(model="o3-mini", reasoning=rc)
    params = _build_litellm_params(req)
    assert params["reasoning_effort"] == "high"
    assert "temperature" not in params


def test_inject_anthropic_reasoning():
    rc = ReasoningConfig(extended_thinking=True, thinking_budget=8000)
    req = _make_request(model="claude-3-7-sonnet-20250219", reasoning=rc)
    params = _build_litellm_params(req)
    assert params["thinking"]["type"] == "enabled"
    assert params["thinking"]["budget_tokens"] == 8000


# --- ProviderRegistry ---

def test_registry_configure_and_get():
    reg = ProviderRegistry()
    reg.configure({
        "DEFAULT_PROVIDER": "openai",
        "PROVIDERS": {"openai": {"api_key": "sk-test"}},
    })
    provider = reg.get("openai")
    assert isinstance(provider, LiteLLMProvider)


def test_registry_get_unknown_raises():
    reg = ProviderRegistry()
    reg.configure({"DEFAULT_PROVIDER": "openai", "PROVIDERS": {}})
    with pytest.raises(ConfigurationError):
        reg.get("nonexistent")


def test_registry_default_provider():
    reg = ProviderRegistry()
    reg.configure({"DEFAULT_PROVIDER": "anthropic", "PROVIDERS": {}})
    assert reg.default_provider == "anthropic"


def test_registry_failover_success():
    """Failover chain tries the second provider when the first raises ProviderError."""
    reg = ProviderRegistry()
    reg.configure({
        "DEFAULT_PROVIDER": "openai",
        "FAILOVER": ["openai", "anthropic"],
        "PROVIDERS": {
            "openai": {"api_key": "sk-test"},
            "anthropic": {"api_key": "sk-ant-test"},
        },
    })

    bad_provider = FakeProvider(text="from openai")
    good_provider = FakeProvider(text="from anthropic")

    def _bad_complete(request):
        raise ProviderError("rate limited")

    bad_provider.complete = _bad_complete

    reg._providers["openai"] = bad_provider
    reg._providers["anthropic"] = good_provider

    req = _make_request(provider="openai")
    response = reg.complete_with_failover(req)
    assert response.text == "from anthropic"


def test_registry_failover_all_fail():
    reg = ProviderRegistry()
    reg.configure({
        "DEFAULT_PROVIDER": "openai",
        "FAILOVER": ["openai"],
        "PROVIDERS": {"openai": {"api_key": "sk-test"}},
    })

    bad = FakeProvider()
    bad.complete = lambda r: (_ for _ in ()).throw(ProviderError("dead"))
    reg._providers["openai"] = bad

    req = _make_request(provider="openai")
    with pytest.raises(ProviderError):
        reg.complete_with_failover(req)


# --- PromptCacheMiddleware ---

def test_cache_middleware_apply_noop_for_non_cache_provider():
    mw = PromptCacheMiddleware()
    req = _make_request(model="gpt-4o", provider="openai", enable_cache=False)
    req.messages = [{"role": "user", "content": "Hello"}]
    result = mw.apply(req)
    # Without cache enabled the messages pass through unchanged
    assert result == req.messages
