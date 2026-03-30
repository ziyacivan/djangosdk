---
name: implement-module
description: >
  Implements a django-ai-sdk module from the PRD spec. Invoke when the user says
  "implement the agents/base.py module", "write the streaming/sse.py file",
  "build the tools/decorator.py", "implement the providers/litellm_provider.py",
  or any phrase like "implement [module path] from the spec" or "scaffold [module]
  per the PRD". Also triggers on "write the [module] module", "create the
  [file path] file for the SDK".
triggers:
  - implement module
  - implement the agents
  - implement the providers
  - implement the tools
  - implement the streaming
  - implement the structured
  - implement the testing
  - write the module
  - scaffold module
  - build the module from spec
  - create the file for the SDK
---

# Implement Module from PRD Spec

You are implementing a module of the `django-ai-sdk` project. The full specification is in `docs/PRD.md` and `CLAUDE.md`.

## Step 1 — Read the Spec First

Before writing any code:
1. Read `docs/PRD.md` — especially the MVP Features and Package Structure sections
2. Read `CLAUDE.md` for design principles and constraints
3. Identify the exact module path inside `django_ai_sdk/` and its role in the architecture

## Step 2 — Understand the Module's Contract

Ask yourself:
- What does this module export? (classes, functions, decorators, constants)
- What does it import from sibling modules?
- What Django/litellm/pydantic primitives does it use?
- Is it sync-only, async-only, or both?

## Step 3 — Apply Core Design Principles

Every module must follow these rules from `CLAUDE.md`:

**Mixin composition:** Capabilities are composed, not inherited deeply. `Agent` mixes in `Promptable`, `HasTools`, `HasStructuredOutput`, `Conversational`, `ReasoningMixin`. No god class.

**litellm as the routing layer:** Never call `openai`, `anthropic`, or `google-generativeai` SDKs directly. All provider calls go through `LiteLLMProvider` which wraps `litellm.completion()` and `litellm.acompletion()`.

**Django-native:** Use `AppConfig`, `settings.AI_SDK` (via `conf.py`'s `ai_settings`), Django ORM, Django signals. Never use `os.environ` directly for API keys — read from `ai_settings`.

**Async-first:** Every sync method (`handle`, `stream`, `complete`) must have an async counterpart (`ahandle`, `astream`, `acomplete`). Use `sync_to_async` for ORM calls inside async methods.

**Reasoning-aware:** `LiteLLMProvider` must inject reasoning parameters automatically. For `o3`/`o4-mini`: `reasoning_effort`. For Claude 3.7 Sonnet: `thinking: {type: "enabled", budget_tokens: N}`. For DeepSeek R1: `budget_tokens`.

## Step 4 — Module-Specific Implementation Notes

### `agents/base.py`
- `Agent` inherits from all five mixins in MRO order: `Promptable, ReasoningMixin, HasTools, HasStructuredOutput, Conversational`
- Class-level attributes with defaults: `provider`, `model`, `system_prompt = ""`, `temperature = 0.7`, `max_tokens = 2048`, `reasoning = None`, `enable_cache = True`
- `handle()` orchestrates: build `AgentRequest` → call provider → check for `tool_calls` → dispatch loop (capped at `max_tool_iterations=10`) → return `AgentResponse`
- `ahandle()` is the async mirror using `await provider.acomplete()`

### `agents/mixins/has_tools.py`
- `HasTools` owns the tool registry per-agent instance: `self._tool_registry = ToolRegistry()`
- `register_tool(fn)` and `get_tool_schemas()` delegate to the registry
- The dispatch loop logic lives in `Agent.handle()`, not in the mixin — the mixin only manages registration and lookup

### `providers/litellm_provider.py`
- `complete()` translates `AgentRequest` → litellm kwargs → calls `litellm.completion()` → translates response to `AgentResponse`
- Detect reasoning model by checking model name: `o3`, `o4-mini` → inject `reasoning_effort`; `claude-3-7` → inject `thinking` dict; `deepseek-r1` → inject `budget_tokens`
- `stream()` calls `litellm.completion(..., stream=True)` and yields `StreamChunk` objects

### `tools/decorator.py`
- `@tool` reads `fn.__doc__` for description
- Uses `inspect.signature()` + type hints → builds JSON schema `{"type": "object", "properties": {...}, "required": [...]}`
- Attaches `fn._tool_schema` and `fn._is_tool = True`
- Support `str`, `int`, `float`, `bool`, `list`, `dict`, `Literal` and Pydantic model types

### `streaming/sse.py`
- `format_sse_chunk(data: str, event: str | None = None) -> str` formats a single SSE frame: `"data: {data}\n\n"` or `"event: {event}\ndata: {data}\n\n"`
- `SyncSSEResponse` subclasses `StreamingHttpResponse` with `content_type="text/event-stream"` and `X-Accel-Buffering: no` header

### `testing/fakes.py`
- `FakeProvider` implements `AbstractProvider`; its `complete()` returns a configurable `AgentResponse`
- `set_response(text, tool_calls=None)` primes the next response (supports chaining for multi-turn)
- `call_log` records all `AgentRequest` objects passed to `complete()`/`acomplete()`

### `testing/assertions.py`
- `assert_prompt_sent(provider, substring)` — checks `provider.call_log` for a request whose messages contain `substring`
- `assert_tool_called(provider, tool_name)` — checks `provider.call_log` for a request whose `tools` list includes `tool_name`

### `conf.py`
- Wraps `django.conf.settings.AI_SDK` with a lazy accessor
- Provides typed defaults: `DEFAULT_PROVIDER = "openai"`, `DEFAULT_MODEL = "gpt-4.1"`
- Raises `ImproperlyConfigured` if required keys are missing

### `apps.py`
- `AiSdkConfig.ready()` calls `ProviderRegistry.build_from_settings(ai_settings)`
- Imports signals to ensure receivers are connected

### `signals.py`
- Define five Django signals: `agent_started`, `agent_completed`, `agent_failed`, `cache_hit`, `cache_miss`
- `agent_started` fires before `provider.complete()` is called (sender=Agent class, kwargs: request)
- `agent_completed` fires after successful response (sender=Agent class, kwargs: response)
- `agent_failed` fires on exception (sender=Agent class, kwargs: exception)
- `cache_hit`/`cache_miss` fire based on `usage.cache_read_tokens > 0`

## Step 5 — Write the File

1. Add the standard module docstring
2. Imports: stdlib → Django → third-party (litellm, pydantic) → internal SDK
3. Type annotations on every function and class attribute
4. Docstrings on every public class and method
5. No `TYPE_CHECKING` hacks — real imports only (this is Python 3.11+)
6. Export all public symbols in `__all__`

## Step 6 — Self-Review Checklist

Before presenting the code:
- [ ] Every sync method has an async counterpart
- [ ] No direct provider SDK imports (only `import litellm`)
- [ ] All public symbols are exported in `__all__`
- [ ] No hardcoded API keys or model names (read from `ai_settings`)
- [ ] `ReasoningConfig` respected in `LiteLLMProvider`
- [ ] Types are fully annotated (mypy-clean intent)
- [ ] Module fits its documented role in `CLAUDE.md`
- [ ] ORM calls inside async methods wrapped with `sync_to_async`
