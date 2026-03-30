---
name: review-against-prd
description: >
  Reviews an implemented module or agent against the PRD spec to identify gaps,
  deviations, or missing requirements. Invoke when the user says "review this
  against the PRD", "check this implementation against the spec", "does this match
  the PRD", "audit this module", "is this compliant with the spec", "what am I
  missing from the spec", "review my implementation", "PRD compliance check", or
  "spec review". Also triggers on "does this match CLAUDE.md".
triggers:
  - review against the PRD
  - check against the spec
  - does this match the PRD
  - audit this module
  - is this compliant with the spec
  - what am I missing from the spec
  - review my implementation
  - PRD compliance check
  - spec review
  - does this match CLAUDE.md
---

# Review Implementation Against PRD Spec

You are auditing an implementation of `django-ai-sdk` against its PRD specification.

## Step 1 — Re-Read the Spec

Always re-read these files before auditing (do not rely on memory):
1. `docs/PRD.md` — Architecture, MVP Features, Package Structure sections
2. `CLAUDE.md` — Key Design Principles and Package Layout

## Step 2 — Run the Full Checklist

Evaluate every item as PASS, FAIL, or N/A (not applicable to this module):

### Architecture Compliance

- [ ] **Mixin composition** — `Agent` subclasses from exactly five mixins in MRO order: `Promptable, ReasoningMixin, HasTools, HasStructuredOutput, Conversational`
- [ ] **litellm-only provider calls** — No `import openai`, `import anthropic`, or `import google.generativeai` anywhere. Only `import litellm`.
- [ ] **Django-native** — Initialization in `AppConfig.ready()`, settings read via `ai_settings` from `conf.py`, ORM for persistence, Django signals used.
- [ ] **Reasoning-aware** — `LiteLLMProvider` injects reasoning params automatically from model name: `o3`/`o4-mini` → `reasoning_effort`; `claude-3-7` → `thinking` dict; `deepseek-r1` → `budget_tokens`.
- [ ] **Async-first** — Every sync method (`handle`, `stream`, `complete`) has an async counterpart (`ahandle`, `astream`, `acomplete`). ORM inside async uses `sync_to_async`.

### Agent Layer

- [ ] `Agent` has class-level attributes: `provider`, `model`, `system_prompt`, `temperature`, `max_tokens`, `reasoning`, `enable_cache`, `enable_conversation`
- [ ] Tool dispatch loop is capped at `max_tool_iterations` (default: 10)
- [ ] Tool results are appended to message history before the next provider call
- [ ] `AgentResponse` contains: `text`, `structured`, `thinking`, `usage` (UsageInfo), `tool_calls`
- [ ] `UsageInfo` contains: `prompt_tokens`, `completion_tokens`, `total_tokens`, `cache_read_tokens`, `cache_write_tokens`
- [ ] `ThinkingBlock` has: `type`, `thinking` (text content)

### Provider Layer

- [ ] `AbstractProvider` ABC defines exactly four abstract methods: `complete`, `acomplete`, `stream`, `astream`
- [ ] `LiteLLMProvider.complete()` translates `AgentRequest` to litellm kwargs and `litellm.ModelResponse` back to `AgentResponse`
- [ ] `ProviderRegistry` is a singleton, built from `AI_SDK` settings in `AiSdkConfig.ready()`
- [ ] `PromptCacheMiddleware` marks system prompt and long conversation turns with Anthropic/OpenAI cache control prefixes
- [ ] `ProviderConfig` and `ModelConfig` dataclasses validate settings schema

### Tools Layer

- [ ] `@tool` reads `fn.__doc__` for description
- [ ] `@tool` builds JSON schema from type hints: str, int, float, bool, list, dict, Literal, Optional, Pydantic BaseModel
- [ ] `ToolRegistry` is per-agent instance (not class-level singleton)
- [ ] Tool return values serialized to strings before being appended as tool results
- [ ] `ToolError` exception type defined and caught by dispatch loop

### Streaming Layer

- [ ] `format_sse_chunk()` outputs correct SSE format: `"data: {text}\n\n"` with optional `"event: {name}\n"` prefix
- [ ] `SyncSSEResponse` sets `content_type="text/event-stream"` and `X-Accel-Buffering: no` header
- [ ] `AsyncSSEResponse` is compatible with Django ASGI (returns async generator)

### Structured Output

- [ ] OpenAI path uses `response_format: {type: "json_schema", json_schema: ...}`
- [ ] Anthropic path uses tools trick or tool-use API
- [ ] Gemini path uses `response_schema` parameter
- [ ] Fallback path uses `model.model_validate_json()` on raw response text
- [ ] `response.structured` returns a Pydantic model instance or `None`

### ORM Models

- [ ] `Conversation` model has fields: `id`, `created_at`, `updated_at`, `metadata` (JSONField)
- [ ] `Message` model has fields: `id`, `conversation` (FK to Conversation), `role` (choices: user/assistant/system/tool), `content`, `tool_calls` (JSONField, nullable), `created_at`
- [ ] Both models have `__str__` methods
- [ ] DRF serializers cover both models

### Testing Utilities

- [ ] `FakeProvider` implements all four `AbstractProvider` methods
- [ ] `FakeProvider.call_log` records all `AgentRequest` objects (list, in order)
- [ ] `FakeProvider.set_response(text, tool_calls=None)` supports chaining (queue multiple responses)
- [ ] `assert_prompt_sent(provider, substring)` checks `call_log` message content
- [ ] `assert_tool_called(provider, tool_name)` checks `call_log` for tool by name
- [ ] Both assertion functions raise `AssertionError` with a clear message on failure

### Settings and App Config

- [ ] `ai_settings` from `conf.py` is a lazy accessor (does not access `settings` at import time)
- [ ] `ImproperlyConfigured` raised on startup if required keys are missing from `AI_SDK`
- [ ] `AiSdkConfig.ready()` calls `ProviderRegistry.build_from_settings()` then imports signals
- [ ] Management command `ai_sdk_check` tests connectivity for each configured provider
- [ ] Management command `ai_sdk_publish` writes the `AI_SDK` block to stdout

### Signals

- [ ] `agent_started` fires before `provider.complete()` (kwargs: `request`)
- [ ] `agent_completed` fires after successful response (kwargs: `response`)
- [ ] `agent_failed` fires when provider raises an exception (kwargs: `exception`)
- [ ] `cache_hit` fires when `usage.cache_read_tokens > 0`
- [ ] `cache_miss` fires when `usage.cache_read_tokens == 0`
- [ ] All signals use `django.dispatch.Signal()` (not `providing_args` which is deprecated)

### DRF Views

- [ ] `ChatAPIView` accepts `POST /chat/` with `{"message": "...", "conversation_id": "..."}` body
- [ ] `StreamingChatAPIView` returns `SyncSSEResponse` or `AsyncSSEResponse`
- [ ] Both views use DRF authentication/permission classes (configurable)

## Step 3 — Report Format

```
## PRD Compliance Report — [module path]

### PASS (N items)
- [item]: [brief explanation of how it satisfies the requirement]

### FAIL (N items)
- [item]: [what is missing or wrong]
  → Fix: [specific code change needed]

### N/A (N items)
- [item]: [why not applicable to this module]

### Recommended Next Steps
1. [highest priority fix — blocking other modules]
2. [second priority fix]
3. ...
```

## Step 4 — Concrete Fixes Required

For every FAIL item, provide the minimal code change as a diff or code snippet — not just a description. Show exactly what line(s) need to change to achieve compliance.

Example:
```
FAIL: async counterpart missing for `complete()`

Fix — add to providers/litellm_provider.py:

    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        response = await litellm.acompletion(**self._build_kwargs(request))
        return self._translate_response(response)
```
