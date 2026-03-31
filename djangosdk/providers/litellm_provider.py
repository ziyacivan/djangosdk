from __future__ import annotations

import json
from typing import Any, AsyncIterator, Iterator

from djangosdk.agents.request import AgentRequest
from djangosdk.agents.response import AgentResponse, StreamChunk, ThinkingBlock, UsageInfo
from djangosdk.exceptions import ProviderError
from djangosdk.providers.base import AbstractProvider
from djangosdk.providers.cache import PromptCacheMiddleware
from djangosdk.providers.schemas import ProviderConfig

# Reasoning model prefixes
_OPENAI_REASONING_MODELS = ("o1", "o3", "o4")
_DEEPSEEK_REASONING_MODELS = ("deepseek-r1", "deepseek-reasoner")
_ANTHROPIC_THINKING_MODELS = ("claude-3-7",)
_GEMINI_THINKING_MODELS = ("gemini-2.5",)

# djangosdk provider key → litellm model prefix (only where they differ)
_PROVIDER_LITELLM_PREFIX: dict[str, str] = {
    "together": "together_ai",
    "vertex": "vertex_ai",
    "bedrock": "bedrock",
}
# Providers that are litellm's default routing — no prefix needed
_NO_PREFIX_PROVIDERS = {"openai"}


def _resolve_litellm_model(model: str, provider: str) -> str:
    """Add the correct litellm provider prefix to a model string.

    litellm routes requests based on the ``provider/model`` prefix in the
    model name.  Without the prefix, unprefixed ``gemini-*`` strings are
    sent to Vertex AI instead of Google AI Studio, and similar misrouting
    occurs for other providers.  OpenAI is litellm's implicit default and
    does not need a prefix.
    """
    if "/" in model:
        return model  # already prefixed — respect as-is
    if provider in _NO_PREFIX_PROVIDERS:
        return model
    litellm_prefix = _PROVIDER_LITELLM_PREFIX.get(provider, provider)
    return f"{litellm_prefix}/{model}"


def _is_reasoning_model(model: str) -> tuple[bool, str]:
    """Returns (is_reasoning, model_family)."""
    m = model.lower()
    for prefix in _OPENAI_REASONING_MODELS:
        if m.startswith(prefix):
            return True, "openai"
    for prefix in _DEEPSEEK_REASONING_MODELS:
        if prefix in m:
            return True, "deepseek"
    for prefix in _ANTHROPIC_THINKING_MODELS:
        if prefix in m:
            return True, "anthropic"
    for prefix in _GEMINI_THINKING_MODELS:
        if prefix in m:
            return True, "gemini"
    return False, ""


def _build_litellm_params(request: AgentRequest, provider_config: ProviderConfig | None = None) -> dict[str, Any]:
    """Convert AgentRequest to litellm.completion() kwargs."""
    params: dict[str, Any] = {
        "model": _resolve_litellm_model(request.model, request.provider),
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    if provider_config:
        if provider_config.api_key:
            params["api_key"] = provider_config.api_key
        if provider_config.base_url:
            params["base_url"] = provider_config.base_url
        if provider_config.organization:
            params["organization"] = provider_config.organization
        if provider_config.api_version:
            params["api_version"] = provider_config.api_version

    if request.tools:
        params["tools"] = request.tools
        params["tool_choice"] = "auto"

    if request.output_schema:
        model = request.model.lower()
        has_tools = bool(request.tools)
        if any(m in model for m in ("gpt-4o", "gpt-4.1", "gpt-4-turbo")):
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": request.output_schema,
                    "strict": True,
                },
            }
        elif "gemini" in model and not has_tools:
            # No tools: use response_format so litellm sets response_mime_type=application/json.
            # With tools, Gemini cannot combine tools + response_mime_type; the schema hint
            # is appended to the system prompt in _build_params() where the system message
            # is already available.
            params["response_format"] = {"type": "json_object"}

    _inject_reasoning_params(params, request)

    params.update(request.extra)
    return params


def _inject_reasoning_params(params: dict[str, Any], request: AgentRequest) -> None:
    """Inject reasoning-model-specific parameters."""
    if not request.reasoning:
        return

    model = request.model.lower()
    is_reasoning, family = _is_reasoning_model(model)

    if not is_reasoning:
        return

    rc = request.reasoning

    if family == "openai":
        params["reasoning_effort"] = rc.effort
        # o3/o4-mini don't use temperature
        params.pop("temperature", None)

    elif family == "deepseek":
        if rc.budget_tokens:
            params["max_tokens"] = rc.budget_tokens
        params["reasoning_effort"] = rc.effort

    elif family == "anthropic":
        if rc.extended_thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": rc.thinking_budget,
            }
        params.pop("temperature", None)

    elif family == "gemini":
        params["thinking_config"] = {"thinking_budget": rc.thinking_budget}


def _parse_usage(raw_usage) -> UsageInfo:
    if raw_usage is None:
        return UsageInfo()
    return UsageInfo(
        prompt_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(raw_usage, "total_tokens", 0) or 0,
        cache_read_tokens=getattr(raw_usage, "prompt_tokens_details", None) and
                          getattr(raw_usage.prompt_tokens_details, "cached_tokens", 0) or 0,
        cache_write_tokens=0,
    )


def _parse_thinking(choice) -> ThinkingBlock | None:
    """Extract thinking/reasoning content from a response choice."""
    # Claude extended thinking
    if hasattr(choice, "message") and hasattr(choice.message, "thinking"):
        thinking = choice.message.thinking
        if thinking:
            return ThinkingBlock(content=str(thinking))
    return None


def _parse_tool_calls(choice) -> list[dict[str, Any]]:
    tool_calls = []
    if hasattr(choice, "message") and choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
            except (json.JSONDecodeError, AttributeError):
                args = {}
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": args,
            })
    return tool_calls


class LiteLLMProvider(AbstractProvider):
    """Default provider backed by litellm."""

    def __init__(self, provider_config: ProviderConfig | None = None) -> None:
        self._config = provider_config
        self._cache_middleware = PromptCacheMiddleware()

    def _prepare_messages(self, request: AgentRequest) -> list[dict]:
        return self._cache_middleware.apply(request)

    def _prepare_system(self, request: AgentRequest) -> list[dict] | str:
        return self._cache_middleware.build_system_with_cache(request.system_prompt, request.model)

    def _build_params(self, request: AgentRequest) -> dict[str, Any]:
        params = _build_litellm_params(request, self._config)
        system = self._prepare_system(request)

        # Gemini + tools + output_schema: cannot use response_mime_type alongside tools.
        # Append the JSON schema as an explicit instruction to the system prompt so the
        # model knows the expected output shape; extract_json_from_text handles parsing.
        if (
            request.output_schema
            and request.tools
            and "gemini" in request.model.lower()
        ):
            import json as _json

            schema_hint = _json.dumps(request.output_schema, indent=2)
            schema_instruction = (
                "\n\nYou MUST return your final answer as a valid JSON object "
                f"matching this exact schema (no markdown, no extra text):\n{schema_hint}"
            )
            if isinstance(system, str):
                system = (system or "") + schema_instruction
            elif not system:
                system = schema_instruction.strip()

        if system:
            # Inject system as first message if not already present
            msgs = list(params["messages"])
            if not msgs or msgs[0].get("role") != "system":
                msgs.insert(0, {"role": "system", "content": system})
                params["messages"] = msgs
        return params

    def complete(self, request: AgentRequest) -> AgentResponse:
        try:
            import litellm
        except ImportError as exc:
            raise ProviderError("litellm is not installed. Run: pip install litellm==1.82.6") from exc

        params = self._build_params(request)
        try:
            raw = litellm.completion(**params)
        except Exception as exc:
            raise ProviderError(str(exc), provider=request.provider, model=request.model) from exc

        choice = raw.choices[0]
        text = choice.message.content or ""
        tool_calls = _parse_tool_calls(choice)
        thinking = _parse_thinking(choice)
        usage = _parse_usage(getattr(raw, "usage", None))

        return AgentResponse(
            text=text,
            model=getattr(raw, "model", request.model),
            provider=request.provider,
            usage=usage,
            thinking=thinking,
            tool_calls=tool_calls,
            raw=raw,
        )

    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        try:
            import litellm
        except ImportError as exc:
            raise ProviderError("litellm is not installed.") from exc

        params = self._build_params(request)
        try:
            raw = await litellm.acompletion(**params)
        except Exception as exc:
            raise ProviderError(str(exc), provider=request.provider, model=request.model) from exc

        choice = raw.choices[0]
        text = choice.message.content or ""
        tool_calls = _parse_tool_calls(choice)
        thinking = _parse_thinking(choice)
        usage = _parse_usage(getattr(raw, "usage", None))

        return AgentResponse(
            text=text,
            model=getattr(raw, "model", request.model),
            provider=request.provider,
            usage=usage,
            thinking=thinking,
            tool_calls=tool_calls,
            raw=raw,
        )

    def stream(self, request: AgentRequest) -> Iterator[StreamChunk]:
        try:
            import litellm
        except ImportError as exc:
            raise ProviderError("litellm is not installed.") from exc

        params = self._build_params(request)
        params["stream"] = True
        try:
            response = litellm.completion(**params)
        except Exception as exc:
            raise ProviderError(str(exc), provider=request.provider, model=request.model) from exc

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            thinking_content = getattr(delta, "thinking", None)
            if thinking_content:
                yield StreamChunk(type="thinking_delta", text=str(thinking_content), thinking=True)
                continue

            content = getattr(delta, "content", None)
            if content:
                yield StreamChunk(type="text_delta", text=content)

        usage = getattr(response, "usage", None)
        yield StreamChunk(
            type="done",
            usage=_parse_usage(usage),
        )

    async def astream(self, request: AgentRequest) -> AsyncIterator[StreamChunk]:
        try:
            import litellm
        except ImportError as exc:
            raise ProviderError("litellm is not installed.") from exc

        params = self._build_params(request)
        params["stream"] = True
        try:
            response = await litellm.acompletion(**params)
        except Exception as exc:
            raise ProviderError(str(exc), provider=request.provider, model=request.model) from exc

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            thinking_content = getattr(delta, "thinking", None)
            if thinking_content:
                yield StreamChunk(type="thinking_delta", text=str(thinking_content), thinking=True)
                continue

            content = getattr(delta, "content", None)
            if content:
                yield StreamChunk(type="text_delta", text=content)

        yield StreamChunk(type="done", usage=UsageInfo())
