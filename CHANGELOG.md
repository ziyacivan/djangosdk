# Changelog

All notable changes to `django-ai-sdk` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Performance benchmark suite (planned)
- Full API reference documentation (planned)

---

## [0.1.0] — 2026-03-30

### Added

**Phase 1 — MVP**
- `Agent` base class with mixin composition (`Promptable`, `HasTools`, `HasStructuredOutput`, `Conversational`, `ReasoningMixin`)
- `LiteLLMProvider` — unified provider abstraction over 12+ AI providers via litellm 1.82.6
- `ProviderRegistry` — singleton built from `AI_SDK` settings; supports provider failover
- `PromptCacheMiddleware` — automatic Anthropic and OpenAI prompt cache prefix injection
- `ReasoningConfig` — native parameter injection for o3/o4 (`reasoning_effort`), Claude 3.7 (`extended_thinking` + `thinking_budget`), DeepSeek R1 (`budget_tokens`)
- `@tool` decorator — converts type-annotated functions into JSON schema tool definitions
- `ToolRegistry` — per-agent tool registry with sync and async dispatch
- `Conversation` and `Message` Django ORM models with UUID primary keys
- `migrations/0001_initial.py` — initial database schema
- DRF serializers: `ConversationSerializer`, `MessageSerializer`
- DRF views: `ChatAPIView`, `StreamingChatAPIView`
- `SyncSSEResponse` and `AsyncSSEResponse` — SSE streaming for WSGI and ASGI
- `StructuredOutput` — Pydantic v2 schema extraction and validation
- `FakeProvider` and `FakeAgent` — test utilities (never call real APIs)
- `assert_prompt_sent()`, `assert_tool_called()`, `assert_model_used()`, `assert_system_prompt_contains()` — test assertion helpers
- `agent_started`, `agent_completed`, `agent_failed`, `agent_failed_over`, `cache_hit`, `cache_miss` Django signals
- `ai_settings` lazy accessor with deep-merge defaults
- `AiSdkConfig` — initializes `ProviderRegistry` on Django startup
- `ai_sdk_publish` management command — prints `AI_SDK` settings skeleton
- `ai_sdk_check` management command — sends a test request to each configured provider
- `pyproject.toml` with hatchling build backend; optional `drf` and `dev` extras
- `README.md` with quickstart guide

**Phase 2 — Enrichment**
- `MCPClient` — connects to external MCP servers (STDIO, HTTP, SSE transports)
- `MCPServer` / `MCPServerView` — exposes Django `@tool` functions as an MCP server
- `@mcp_tool`, `@mcp_resource` decorators
- `EpisodicMemory` — DB-backed agent memory with search and recency retrieval
- `OpenTelemetryObserver`, `LangSmithObserver`, `LangfuseObserver` — observability backends
- `tools/builtins/web_search.py`, `tools/builtins/web_fetch.py` — built-in web tools
- `tools/builtins/rag.py` — pgvector RAG integration
- `embeddings/embed.py` — text embedding via litellm
- `ratelimit/` — token-based rate limiting with Django cache backend
- `analytics/cost.py` — per-message cost tracking (`Message.cost_usd`)
- Provider failover with `agent_failed_over` signal
- `ConversationAdmin`, `MessageAdmin` — Django Admin integration

**Phase 3 — Advanced**
- `orchestration/patterns.py` — `handoff`, `pipeline`, `parallel` agentic patterns
- `orchestration/evaluator.py` — Evaluator-Optimizer pattern
- `memory/semantic.py` — vector store-backed semantic memory
- `images/generate.py` — image generation (DALL-E 3, Gemini Imagen 3, xAI Aurora)
- `audio/transcribe.py` — Whisper transcription
- `audio/synthesize.py` — TTS synthesis
- `AUTO_SUMMARIZE` — automatic conversation summarization when `MAX_HISTORY` is exceeded

---

[Unreleased]: https://github.com/ziyacivan/django-ai-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ziyacivan/django-ai-sdk/releases/tag/v0.1.0
