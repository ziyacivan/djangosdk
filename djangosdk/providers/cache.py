from __future__ import annotations

from typing import Any

from djangosdk.agents.request import AgentRequest
from djangosdk.conf import ai_settings


_ANTHROPIC_CACHE_CONTROL = {"type": "ephemeral"}

# Models that support prompt caching
_ANTHROPIC_MODELS = ("claude",)
_OPENAI_MODELS = ("gpt-4o", "gpt-4.1", "gpt-4-turbo")


def _is_anthropic_model(model: str) -> bool:
    return any(m in model.lower() for m in _ANTHROPIC_MODELS)


def _is_openai_cached_model(model: str) -> bool:
    return any(m in model.lower() for m in _OPENAI_MODELS)


class PromptCacheMiddleware:
    """
    Adds provider-specific cache control markers to messages.

    Anthropic: adds cache_control to system prompt and long conversation turns.
    OpenAI: GPT-4o+ supports automatic prompt caching; no explicit markers needed.
    """

    def apply(self, request: AgentRequest) -> list[dict[str, Any]]:
        """Return messages with cache annotations applied."""
        if not request.enable_cache:
            return request.messages

        cache_setting = ai_settings.get("CACHE", {})
        if not cache_setting.get("ENABLED", True):
            return request.messages

        allowed_providers = cache_setting.get("PROVIDERS", ["anthropic", "openai"])

        if _is_anthropic_model(request.model) and "anthropic" in allowed_providers:
            return self._apply_anthropic_cache(request.messages)

        return request.messages

    def _apply_anthropic_cache(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add Anthropic cache_control markers to eligible messages."""
        result = []
        for i, msg in enumerate(messages):
            msg = dict(msg)
            content = msg.get("content", "")
            # Cache the last few large user messages (typically the system + conversation)
            if isinstance(content, str) and len(content) > 1024:
                msg["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": _ANTHROPIC_CACHE_CONTROL,
                    }
                ]
            result.append(msg)
        return result

    def build_system_with_cache(self, system_prompt: str, model: str) -> list[dict] | str:
        """Return system prompt in cached format if supported."""
        if not system_prompt:
            return system_prompt

        cache_setting = ai_settings.get("CACHE", {})
        if not cache_setting.get("ENABLED", True):
            return system_prompt

        allowed_providers = cache_setting.get("PROVIDERS", ["anthropic", "openai"])

        if _is_anthropic_model(model) and "anthropic" in allowed_providers:
            return [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": _ANTHROPIC_CACHE_CONTROL,
                }
            ]

        return system_prompt
