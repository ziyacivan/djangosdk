# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a **pre-implementation** project. The full specification lives in `docs/PRD.md`. No implementation code exists yet. All architecture decisions should follow the PRD.

## Architecture Overview

`django-ai-sdk` is a Django-native AI SDK inspired by the Laravel AI SDK. The design is **agent-centric with mixin composition**.

### Layered Architecture

```
Developer Code (class MyAgent(Agent): ...)
        ↓
Agent Layer: Agent + Promptable + HasTools + HasStructuredOutput + Conversational + ReasoningMixin
        ↓
Provider Abstraction: AbstractProvider → LiteLLMProvider + ProviderRegistry + PromptCacheMiddleware
        ↓
litellm ≥1.82.6  (OpenAI / Anthropic / Gemini / Groq / DeepSeek / Mistral / xAI / Ollama / ...)
        ↓
Django Integration: ORM Models | DRF Views | AppConfig | Settings | Signals | Admin
        ↓
Observability: OpenTelemetry | LangSmith | Langfuse
```

### Key Design Principles

1. **Mixin composition over inheritance** — capabilities (`Promptable`, `HasTools`, `HasStructuredOutput`, `Conversational`, `ReasoningMixin`) are added à la carte
2. **litellm as the routing layer** — never call provider SDKs directly; always go through `LiteLLMProvider`
3. **Django-native** — use `AppConfig`, `settings.AI_SDK`, Django ORM, Django signals, management commands
4. **Reasoning-aware** — o3/o4-mini use `reasoning_effort`, Claude 3.7 uses `extended_thinking` + `thinking_budget`, DeepSeek R1 uses `budget_tokens` — `LiteLLMProvider` injects these automatically from `ReasoningConfig`
5. **Async-first** — every sync method (`handle`, `stream`) has an async counterpart (`ahandle`, `astream`); Django ORM calls inside async views use `sync_to_async`

### Package Layout (`django_ai_sdk/`)

| Module | Purpose |
|---|---|
| `agents/base.py` | `Agent` class composing all mixins |
| `agents/mixins/` | `promptable.py`, `conversational.py`, `has_tools.py`, `has_structured_output.py`, `reasoning.py` |
| `agents/request.py` / `response.py` | `AgentRequest`, `AgentResponse`, `UsageInfo`, `ThinkingBlock` dataclasses |
| `providers/base.py` | `AbstractProvider` ABC with `complete/acomplete/stream/astream` |
| `providers/litellm_provider.py` | Default provider wrapping litellm |
| `providers/registry.py` | `ProviderRegistry` singleton built from `AI_SDK` settings |
| `providers/cache.py` | `PromptCacheMiddleware` — adds Anthropic/OpenAI cache prefixes |
| `providers/schemas.py` | `ProviderConfig`, `ModelConfig`, `ReasoningConfig` |
| `tools/decorator.py` | `@tool` decorator — docstring → description, type hints → JSON schema |
| `tools/registry.py` | `ToolRegistry` per-agent; drives the dispatch loop |
| `models/` | `Conversation` + `Message` ORM models |
| `serializers/` | DRF serializers for `Conversation` and `Message` |
| `views/chat.py` | `ChatAPIView` (DRF) |
| `views/streaming.py` | `StreamingChatAPIView` (DRF) |
| `streaming/sse.py` | `format_sse_chunk()`, `SyncSSEResponse` |
| `streaming/async_sse.py` | `AsyncSSEResponse` |
| `structured/output.py` | `StructuredOutput`, JSON schema extraction from Pydantic v2 |
| `testing/fakes.py` | `FakeProvider`, `FakeAgent` |
| `testing/assertions.py` | `assert_prompt_sent()`, `assert_tool_called()` |
| `signals.py` | `agent_started`, `agent_completed`, `agent_failed`, `cache_hit`, `cache_miss` |
| `conf.py` | `ai_settings` accessor wrapping `settings.AI_SDK` |
| `apps.py` | `AiSdkConfig` — initializes `ProviderRegistry` on startup |

### Tool Dispatch Loop

1. Prompt + tool schemas → provider
2. Provider returns `tool_calls` → execute each tool
3. Append tool results to message history
4. Repeat until no `tool_calls` (capped at `max_tool_iterations`, default 10)
5. Return final `AgentResponse`

### Structured Output

- OpenAI GPT-4o+: `response_format: {type: "json_schema", ...}`
- Anthropic: tools trick or tool-use API
- Gemini: `response_schema` parameter
- Fallback: parse response text via `model_validate_json()`
- Access via `response.structured` (Pydantic instance) or `response.thinking` (reasoning content)

## Dependencies

- Python ≥ 3.11, Django ≥ 4.2
- `litellm ≥ 1.82.6` — **pin this version**; there was a supply chain incident in March 2026, so verify package integrity before upgrading
- `pydantic ≥ 2.0`
- `djangorestframework` (optional, for DRF views/serializers)

## Settings Schema

```python
AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
        "anthropic": {"api_key": env("ANTHROPIC_API_KEY")},
        # ... other providers
    },
}
```

## Testing

- Use `FakeProvider` for unit tests — never call real APIs in tests
- Use `assert_prompt_sent()` and `assert_tool_called()` from `django_ai_sdk.testing.assertions`
- Target: 90% test coverage
- Run tests: `pytest` (once `pyproject.toml` and test infrastructure are set up)

## Management Commands

- `python manage.py ai_sdk_check` — sends a test request to each configured provider
- `python manage.py ai_sdk_publish` — writes the `AI_SDK` settings block to stdout

## Phase Scope

- **Phase 1 (MVP):** Everything in `agents/`, `providers/`, `tools/`, `streaming/`, `structured/`, `models/`, `serializers/`, `views/`, `testing/`, `signals.py`, `conf.py`, `apps.py`, management commands
- **Phase 2:** `mcp/`, `memory/episodic.py`, `observability/`, `tools/builtins/web_*.py`, embeddings + pgvector RAG, token-based rate limiting
- **Phase 3:** `memory/semantic.py`, multi-agent orchestration, image/audio generation, Django Admin integration
