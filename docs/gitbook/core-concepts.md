# Architecture

## Layered Design

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

## Key Design Principles

### 1. Mixin Composition Over Inheritance

Capabilities are added à la carte via mixins. The base `Agent` class composes all of them:

```python
class Agent(Promptable, ReasoningMixin, HasTools, HasStructuredOutput, Conversational):
    ...
```

You build agents by subclassing `Agent` and declaring class attributes — no `__init__` wiring required.

### 2. litellm as the Routing Layer

`django-ai-sdk` never calls provider SDKs directly. Every request goes through `LiteLLMProvider`, which translates the unified `AgentRequest` into the correct litellm call. This means:

- Provider switching is a one-line change
- New providers are automatically supported when litellm adds them
- Failover between providers works transparently

### 3. Django-Native

The SDK integrates with Django the way Django developers expect:

- Configuration via `settings.AI_SDK`
- ORM models for conversation persistence
- Django signals for lifecycle events
- `AppConfig` for startup initialization
- Management commands for diagnostics and publishing

### 4. Reasoning-Aware

Different reasoning models use different API parameters. `LiteLLMProvider` automatically injects the correct parameters based on `ReasoningConfig`:

| Model | Parameter injected |
|---|---|
| o3, o4-mini | `reasoning_effort` |
| Claude 3.7 Sonnet | `thinking.type = "enabled"`, `thinking.budget_tokens` |
| DeepSeek R1 | `budget_tokens` |

### 5. Async-First

Every synchronous method has an async counterpart:

| Sync | Async |
|---|---|
| `agent.handle(prompt)` | `await agent.ahandle(prompt)` |
| `agent.stream(prompt)` | `async for chunk in agent.astream(prompt)` |

Django ORM calls inside async views use `sync_to_async` internally.

## Request Lifecycle

1. `agent.handle(prompt)` is called
2. `agent_started` signal is fired
3. `Promptable._build_request()` assembles an `AgentRequest` from agent config, conversation history, tool schemas, and output schema
4. `ProviderRegistry.get(provider_name)` returns the `LiteLLMProvider`
5. The provider calls litellm, which routes to the correct provider API
6. If the response contains `tool_calls`, `HasTools._execute_tool_calls()` runs each tool
7. Tool results are appended to the message history and the loop repeats (up to `max_tool_iterations`)
8. When no more tool calls are returned, `AgentResponse` is built
9. If `output_schema` is set, the response text is validated against the Pydantic model
10. Messages are persisted to the database (if `Conversational` and `PERSIST=True`)
11. `agent_completed` signal is fired
12. `AgentResponse` is returned to the caller

## Package Layout

| Module | Purpose |
|---|---|
| `agents/base.py` | `Agent` class composing all mixins |
| `agents/mixins/` | `promptable.py`, `conversational.py`, `has_tools.py`, `has_structured_output.py`, `reasoning.py` |
| `agents/request.py` | `AgentRequest` dataclass |
| `agents/response.py` | `AgentResponse`, `UsageInfo`, `ThinkingBlock`, `StreamChunk` dataclasses |
| `providers/base.py` | `AbstractProvider` ABC |
| `providers/litellm_provider.py` | Default provider wrapping litellm |
| `providers/registry.py` | `ProviderRegistry` singleton |
| `providers/cache.py` | `PromptCacheMiddleware` |
| `providers/schemas.py` | `ProviderConfig`, `ModelConfig`, `ReasoningConfig` |
| `tools/decorator.py` | `@tool` decorator |
| `tools/registry.py` | `ToolRegistry` |
| `models/` | `Conversation` + `Message` ORM models |
| `serializers/` | DRF serializers |
| `views/` | `ChatAPIView`, `StreamingChatAPIView` |
| `streaming/sse.py` | `SyncSSEResponse` |
| `streaming/async_sse.py` | `AsyncSSEResponse` |
| `structured/output.py` | `StructuredOutput`, JSON schema extraction |
| `testing/fakes.py` | `FakeProvider`, `FakeAgent` |
| `testing/assertions.py` | `assert_prompt_sent()`, `assert_tool_called()` |
| `signals.py` | Django signals |
| `conf.py` | `ai_settings` accessor |
| `apps.py` | `AiSdkConfig` |
