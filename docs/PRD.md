# Product Requirements Document: django-ai-sdk

**Version:** 2.0
**Author:** Yusuf Ziya Cıvan
**Date:** March 30, 2026
**Status:** Active Draft

---

## Table of Contents

1. [Overview](#1-overview)
2. [Reference & Competitive Analysis](#2-reference--competitive-analysis)
3. [Target Audience](#3-target-audience)
4. [Goals & Non-Goals](#4-goals--non-goals)
5. [Architecture](#5-architecture)
6. [Package Structure](#6-package-structure)
7. [MVP Features](#7-mvp-features)
8. [Roadmap Features](#8-roadmap-features)
9. [Django Settings Schema](#9-django-settings-schema)
10. [Database Models](#10-database-models)
11. [Developer API Examples](#11-developer-api-examples)
12. [Dependencies & Security](#12-dependencies--security)
13. [Delivery Phases](#13-delivery-phases)
14. [Success Metrics](#14-success-metrics)

---

## 1. Overview

### The Problem

Django is the standard framework for Python web development. Yet as of 2026, there is a significant ecosystem gap when it comes to AI integration.

**Current state:**
- Developers must wire up provider-specific SDKs (`openai`, `anthropic`, `google-generativeai`) individually
- The same streaming, tool calling, conversation history, and structured output boilerplate is rewritten in every project
- No ready-made views or serializers for DRF; no test helpers; switching providers is costly
- Reasoning models (o3, Claude 3.7 Sonnet extended thinking, DeepSeek R1) require different API parameters, and no standard abstraction exists
- MCP (Model Context Protocol) is becoming the enterprise standard in 2026 with no native Django support

**Comparison:**
Laravel released its official AI SDK in February 2026. The PHP community gained a framework-native solution. The Django community remains stuck with a fragmented set of community packages.

### The Solution

`django-ai-sdk` provides:

- **Unified provider abstraction** — 12+ AI providers, one API
- **Agent-centric design** — `Agent` class + mixin composition (inspired by Laravel AI SDK, using Python idioms)
- **Reasoning model support** — Native parameters for o3, Claude 3.7 extended thinking, and DeepSeek R1
- **MCP integration** — Run Django applications as MCP servers or clients
- **Prompt caching** — Automatic use of Anthropic's and OpenAI's native caching APIs
- **Async-first** — SSE streaming with Django 5.x async view support
- **Agent memory layers** — Short-term (context), episodic (DB), semantic (vector store)
- **Observability** — LangSmith, Langfuse, and OpenTelemetry hooks
- **DRF-ready** — Pre-built views, serializers, and streaming endpoints
- **Test utilities** — FakeProvider and assertion helpers

---

## 2. Reference & Competitive Analysis

### 2.1 Laravel AI SDK (Primary Reference)

Laravel AI SDK was released in February 2026 and became stable with Laravel 13 (March 17, 2026).

**Architecture:**
- Provider abstraction built on Prism PHP v0.100.1 (March 20, 2026)
- Agent classes composed with `Promptable`, `HasTools`, `HasStructuredOutput`, and `Conversational` traits
- Five agentic patterns: Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer
- MCP server/client support via the Laravel MCP package (2025-03-26 spec)
- Database-backed conversation history, Eloquent-native vector search
- GitHub: 735 stars, 159 forks (actively maintained as of March 28, 2026)

**Differentiators for `django-ai-sdk`:**

| Topic | Laravel AI SDK | django-ai-sdk |
|---|---|---|
| Reasoning model support | Limited | Native parameters for o3, Claude 3.7, R1 |
| Prompt caching | Not available | Anthropic + OpenAI native caching |
| Async streaming | Via Laravel Echo/Reverb | Django ASGI native, SSE |
| Structured output | Schema array | Pydantic v2 native |
| Observability | Not available | LangSmith / Langfuse hooks |
| Token-based rate limiting | Not available | Token-based, not request-based |

### 2.2 OpenAI Agents SDK (Python)

Python SDK released by OpenAI in January 2025:
- Minimal abstractions: Agent, Handoff, Runner
- Built-in tracing
- **Missing:** No Django/DRF integration, no conversation persistence, no provider abstraction (OpenAI only)

### 2.3 Anthropic Claude Agent SDK

- Built-in tools: file operations, shell, web search, MCP
- Subagent support, automatic context management
- **Missing:** Django-agnostic, provider-locked, no ORM

### 2.4 Existing Django/Python AI Packages (PyPI, March 2026)

| Package | Stars | Status | What's Missing |
|---|---|---|---|
| `django-ai-assistant` | ~800 | Active | Single provider (OpenAI), limited streaming |
| `django-ai-framework` | ~200 | Low activity | LangChain dependency, heavyweight |
| `django-ai-core` | ~50 | Unmaintained | MVP-level only |
| `django-llm` | ~120 | Slow updates | No DRF integration |
| `LangChain` | 95k+ | Active | Django-agnostic, overly complex |
| `LlamaIndex` | 35k+ | Active | Django-agnostic, RAG-focused |
| `litellm` | 20k+ | Active | Django-agnostic, routing only |

**Conclusion:** The Django community needs an official, comprehensive, first-party-quality AI SDK.

### 2.5 AI Model Ecosystem (March 2026 Snapshot)

The following models will be supported and actively tested:

**Reasoning Models (Require Special Parameters)**

| Model | Provider | Feature | Cost (per 1M tokens) |
|---|---|---|---|
| o3 | OpenAI | SOTA reasoning, Codeforces/SWE-bench leader | Variable (by effort) |
| o3-pro | OpenAI | Extended thinking, Pro/Team | High |
| o4-mini | OpenAI | Affordable reasoning | Low |
| Claude 3.7 Sonnet | Anthropic | Hybrid reasoning, visible extended thinking | $3 / $15 |
| DeepSeek R1 | DeepSeek | Math/theorem proving, extremely affordable | $0.14 / $0.28 |
| Gemini 2.5 Flash | Google | Fast reasoning, experimental | Low |

**Standard Models**

| Model | Provider | Feature |
|---|---|---|
| GPT-4.1 | OpenAI | Coding-focused |
| GPT-4.5 | OpenAI | Creative/agentic, research preview |
| Claude 3.5 Haiku | Anthropic | Speed/cost balance |
| Gemini 2.0 Flash | Google | Conversational, multimodal |
| Llama 4 Scout | Meta/Ollama | 17B, 10M context window, local execution |
| Llama 4 Maverick | Meta/Ollama | 128-expert MoE, GPT-4o level |
| Mistral Medium 3.1 | Mistral | $0.40/1M, efficient |
| Grok 3 | xAI | 4 parallel reasoning agents |
| Qwen3 32B | Groq | Fast inference on Groq infrastructure |

---

## 3. Target Audience

### Primary

- **Django backend developers** — Building SaaS chatbots, AI copilots, document Q&A, and code assistants
- **DRF API developers** — Who need streaming and structured output endpoints without boilerplate

### Secondary

- **Django full-stack developers** — Adding AI features with HTMX/Alpine + SSE
- **Startup CTOs** — Who want rapid prototyping and provider flexibility

### Personas

**Alex — Backend Engineer, SaaS company**
Adding an AI chat assistant to an existing Django application. Wants the ability to switch from OpenAI to Anthropic. DRF serializer integration and clean test coverage are critical.

**Priya — Freelance Developer**
Needs AI features in every client project. Reusable patterns, good documentation, and fast setup are the priority.

**Omar — Senior Engineer, AI-first startup**
Needs multi-agent orchestration, RAG, embeddings, and tool calling. Escape hatches and extensibility are non-negotiable.

**Kerem — Django student / junior developer**
Integrating AI for learning purposes. Needs a simple API, clear error messages, and good documentation.

---

## 4. Goals & Non-Goals

### Goals — MVP (Phase 1)

- Unified API for 12+ providers (via litellm)
- Reasoning model support (o3, Claude 3.7 extended thinking, DeepSeek R1)
- `Agent` base class + `Promptable`, `HasTools`, `HasStructuredOutput`, `Conversational` mixins
- SSE streaming (sync WSGI + async ASGI)
- Structured output — Pydantic v2, native JSON schema enforcement
- Tool calling — decorator-based, automatic dispatch loop
- Conversation persistence — Django ORM (Conversation + Message models)
- Prompt caching — Anthropic + OpenAI native caching automation
- DRF `ChatAPIView`, `StreamingChatAPIView`, serializers
- `AI_SDK` settings schema + validation
- `ai_sdk_publish`, `ai_sdk_check` management commands
- `FakeProvider`, test assertion helpers
- `pyproject.toml`, README, initial PyPI release

### Goals — Roadmap (Phase 2–3)

- MCP server and client support (2025-03-26 spec)
- Embeddings + pgvector RAG integration
- Agent memory layers (episodic, semantic)
- Observability hooks (LangSmith, Langfuse, OpenTelemetry)
- Token-based rate limiting and cost tracking
- Image generation (OpenAI DALL-E 3, Gemini Imagen 3, xAI Aurora)
- Audio synthesis and transcription (Whisper, ElevenLabs)
- Multi-agent orchestration (all five agentic patterns)
- Django Admin integration
- Built-in tools: `WebSearchTool`, `WebFetchTool`, `RAGTool`
- Failover mechanism (via Django signals)

### Non-Goals

- Replacing litellm (we build on top of it)
- Supporting Python < 3.11 or Django < 4.2
- Frontend components (HTMX, React, Alpine kept separate)
- LLM training, fine-tuning, or model hosting
- General-purpose Python AI SDK (Django-focused only)

---

## 5. Architecture

### 5.1 Design Philosophy

1. **Convention over configuration** — Minimal setup, sane defaults
2. **Mixin composition** — à la carte capability addition over deep inheritance
3. **Django-native** — ORM, AppConfig, settings, signals, management commands
4. **Reasoning-aware** — Special parameter management for o3, Claude 3.7, and R1 models
5. **Security-first** — litellm version pinning, supply chain verification

### 5.2 Layered Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Developer Code                              │
│           class MyAgent(Agent): ...                                  │
├──────────────────────────────────────────────────────────────────────┤
│                          Agent Layer                                 │
│  Agent + Promptable + HasTools + HasStructuredOutput + Conversational│
│  ReasoningMixin (o3/R1/Claude 3.7 extended thinking support)         │
├──────────────────────────────────────────────────────────────────────┤
│                     Provider Abstraction                             │
│  AbstractProvider → LiteLLMProvider (default)                        │
│  ProviderRegistry — built from AI_SDK settings                       │
│  PromptCacheMiddleware — adds Anthropic/OpenAI cache prefixes        │
├──────────────────────────────────────────────────────────────────────┤
│                          litellm ≥1.82.6                             │
│  OpenAI / Anthropic / Gemini / Groq / DeepSeek / Mistral /          │
│  xAI / Azure / Ollama (Llama 4) / Perplexity / OpenRouter ...       │
├──────────────────────────────────────────────────────────────────────┤
│                      Django Integration                              │
│  ORM Models | DRF Views | AppConfig | Settings | Signals | Admin     │
├──────────────────────────────────────────────────────────────────────┤
│                      Observability Layer                             │
│  OpenTelemetry spans | LangSmith traces | Langfuse events            │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 Provider Abstraction

`AbstractProvider` defines four methods:

```python
class AbstractProvider(ABC):
    def complete(self, request: AgentRequest) -> AgentResponse: ...
    async def acomplete(self, request: AgentRequest) -> AgentResponse: ...
    def stream(self, request: AgentRequest) -> Iterator[StreamChunk]: ...
    async def astream(self, request: AgentRequest) -> AsyncIterator[StreamChunk]: ...
```

`LiteLLMProvider` wraps litellm's `completion()` / `acompletion()` functions. It translates `AgentRequest` into litellm format and converts the response back to `AgentResponse`.

### 5.4 Reasoning Model Support

Reasoning models accept different parameters compared to standard models:

```python
# For o3 / o4-mini
class ReasoningConfig:
    effort: Literal["low", "medium", "high"] = "medium"  # o3/o4-mini
    budget_tokens: int | None = None                        # DeepSeek R1
    extended_thinking: bool = False                         # Claude 3.7
    thinking_budget: int = 10000                            # Claude 3.7 token budget
    stream_thinking: bool = False                           # Stream the thinking process
```

`LiteLLMProvider` automatically adds these parameters based on the model name.

### 5.5 Prompt Caching

Anthropic and OpenAI offer caching APIs for frequently repeated prefixes (Anthropic: 90% cost reduction, 85% latency reduction). The SDK manages this cache automatically:

- System prompt → marked as a cache prefix
- Conversation history → cached with `cache_control: {"type": "ephemeral"}`
- Cache hit rate is tracked via `AgentResponse.usage.cache_read_tokens`

### 5.6 Sync vs Async

| Context | Method | Transport |
|---|---|---|
| Sync view | `agent.handle(prompt)` | Standard HTTP response |
| Async view | `await agent.ahandle(prompt)` | Standard HTTP response |
| Sync streaming | `agent.stream(prompt)` | `StreamingHttpResponse` + SSE |
| Async streaming | `agent.astream(prompt)` | Async `StreamingHttpResponse` + SSE |

Django ORM calls inside async contexts are made via the `sync_to_async` bridge.

### 5.7 MCP (Model Context Protocol) Integration

MCP is the universal tool protocol standardized in 2026 by major AI providers (OpenAI, Anthropic, Google, Microsoft, Amazon).

`django-ai-sdk` offers two-way MCP support:

1. **MCP Client** — Agents consume tools from external MCP servers
2. **MCP Server** — Django application exposes its tools as an MCP server

---

## 6. Package Structure

```
djangosdk/
├── __init__.py                          # Public API: Agent, tool, ai_settings
├── apps.py                              # AiSdkConfig — initializes the provider registry
├── conf.py                              # ai_settings accessor (settings.AI_SDK wrapper)
├── exceptions.py                        # AiSdkError, ProviderError, ToolError,
│                                        # SchemaError, ReasoningError, CacheError
│
├── agents/
│   ├── __init__.py                      # Agent export
│   ├── base.py                          # Agent base class (composes all mixins)
│   ├── request.py                       # AgentRequest dataclass
│   ├── response.py                      # AgentResponse, UsageInfo, ThinkingBlock
│   └── mixins/
│       ├── __init__.py
│       ├── promptable.py                # handle(), ahandle(), stream(), astream()
│       ├── conversational.py            # with_conversation(), start_conversation()
│       ├── has_tools.py                 # @tool decorator, tool dispatch loop
│       ├── has_structured_output.py     # output_schema, Pydantic validation
│       └── reasoning.py                 # Reasoning model parameters (o3/R1/Claude 3.7)
│
├── providers/
│   ├── __init__.py
│   ├── base.py                          # AbstractProvider ABC
│   ├── litellm_provider.py              # LiteLLMProvider (default)
│   ├── registry.py                      # ProviderRegistry singleton
│   ├── cache.py                         # PromptCacheMiddleware
│   └── schemas.py                       # ProviderConfig, ModelConfig, ReasoningConfig
│
├── tools/
│   ├── __init__.py
│   ├── decorator.py                     # @tool decorator
│   ├── base.py                          # BaseTool ABC
│   ├── registry.py                      # ToolRegistry (per-agent)
│   └── builtins/
│       ├── __init__.py
│       ├── web_search.py                # WebSearchTool (Phase 2)
│       ├── web_fetch.py                 # WebFetchTool (Phase 2)
│       └── rag.py                       # RAGTool — pgvector integration (Phase 2)
│
├── mcp/
│   ├── __init__.py
│   ├── client.py                        # MCPClient — connects to external servers (Phase 2)
│   ├── server.py                        # MCPServer — exposes Django tools (Phase 2)
│   ├── decorators.py                    # @mcp_tool, @mcp_resource
│   └── transport.py                     # STDIO, HTTP, SSE transports
│
├── structured/
│   ├── __init__.py
│   └── output.py                        # StructuredOutput, JSON schema extraction
│
├── streaming/
│   ├── __init__.py
│   ├── sse.py                           # format_sse_chunk(), SyncSSEResponse
│   └── async_sse.py                     # AsyncSSEResponse
│
├── memory/
│   ├── __init__.py
│   ├── base.py                          # AbstractMemoryStore
│   ├── episodic.py                      # EpisodicMemory — DB backed (Phase 2)
│   └── semantic.py                      # SemanticMemory — vector store backed (Phase 3)
│
├── models/
│   ├── __init__.py
│   ├── conversation.py                  # Conversation ORM model
│   └── message.py                       # Message ORM model
│
├── serializers/
│   ├── __init__.py
│   ├── conversation.py                  # ConversationSerializer (DRF)
│   └── message.py                       # MessageSerializer (DRF)
│
├── views/
│   ├── __init__.py
│   ├── chat.py                          # ChatAPIView (DRF)
│   └── streaming.py                     # StreamingChatAPIView (DRF)
│
├── urls.py                              # Optional urlpatterns
│
├── observability/
│   ├── __init__.py
│   ├── base.py                          # AbstractObserver
│   ├── opentelemetry.py                 # OTel span hooks (Phase 2)
│   ├── langsmith.py                     # LangSmith trace hooks (Phase 2)
│   └── langfuse.py                      # Langfuse event hooks (Phase 2)
│
├── management/
│   └── commands/
│       ├── ai_sdk_publish.py            # Writes AI_SDK settings block to stdout
│       └── ai_sdk_check.py             # Sends a test request to each provider
│
├── signals.py                           # agent_started, agent_completed,
│                                        # agent_failed, agent_failed_over,
│                                        # cache_hit, cache_miss
│
├── testing/
│   ├── __init__.py
│   ├── fakes.py                         # FakeProvider, FakeAgent
│   └── assertions.py                    # assert_prompt_sent(), assert_tool_called()
│
└── migrations/
    ├── __init__.py
    └── 0001_initial.py                  # Creates Conversation + Message tables
```

---

## 7. MVP Features

### 7.1 Provider Support

12+ providers are supported via litellm. The SDK automatically determines the correct prefix based on the model name.

**Reasoning Models (special parameter management):**

| Provider | Model Examples | Special Parameter |
|---|---|---|
| OpenAI | o3, o3-pro, o4-mini | `reasoning_effort: low/medium/high` |
| Anthropic | Claude 3.7 Sonnet | `thinking: {type: "enabled", budget_tokens: N}` |
| DeepSeek | DeepSeek-R1, DeepSeek-R1-Distill | `reasoning_effort`, `max_tokens` |
| Google | Gemini 2.5 Flash (experimental) | `thinking_config` |

**Standard Models:**

| Provider | Recommended Models (March 2026) |
|---|---|
| OpenAI | gpt-4.1, gpt-4.5-preview |
| Anthropic | claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219 |
| Google | gemini-2.0-flash, gemini-2.5-flash-preview |
| Groq | llama-4-scout-17b-16e-instruct, qwen3-32b |
| Mistral | mistral-medium-3 |
| DeepSeek | deepseek-chat (V3) |
| xAI | grok-3, grok-3-fast |
| Azure | By deployment name |
| Ollama | llama4:scout, llama4:maverick (local) |
| Perplexity | sonar, sonar-pro |
| OpenRouter | Any model (router) |

### 7.2 Agent Base Class

```python
class Agent(Promptable, ReasoningMixin, HasTools, HasStructuredOutput, Conversational):
    provider: str       # default: AI_SDK["DEFAULT_PROVIDER"]
    model: str          # default: AI_SDK["DEFAULT_MODEL"]
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    reasoning: ReasoningConfig | None = None   # For reasoning models
    enable_cache: bool = True                   # Enable/disable prompt caching

    # Sync
    def handle(self, prompt: str, **kwargs) -> AgentResponse: ...
    def stream(self, prompt: str, **kwargs) -> StreamingHttpResponse: ...

    # Async
    async def ahandle(self, prompt: str, **kwargs) -> AgentResponse: ...
    async def astream(self, prompt: str, **kwargs) -> AsyncGenerator: ...
```

### 7.3 Tool Calling

Tools are defined using the `@tool` decorator. The docstring becomes the tool description; type annotations generate the JSON schema.

The dispatch loop runs automatically:
1. Prompt + tool schemas are sent to the provider
2. If the provider returns `tool_calls`, each is executed
3. Tool results are appended to the message history
4. The loop repeats until no new tool calls remain
5. The final text response is returned

The tool loop is capped by `max_tool_iterations` (default: 10).

### 7.4 Structured Output

The provider's native JSON Schema enforcement is used:
- OpenAI GPT-4o+ → `response_format: {type: "json_schema", json_schema: ...}`
- Anthropic Claude → tools trick + validation (or tool use API)
- Gemini → `response_schema` parameter

Fallback: If the provider does not support it, the response text is parsed via `model_validate_json()`.

`response.structured` → returns the validated Pydantic instance.
`response.thinking` → Claude 3.7 / o3 extended thinking content (if available).

### 7.5 Prompt Caching

```python
class AnalysisAgent(Agent):
    system_prompt = "You are a data analyst..."  # → cache prefix
    enable_cache = True

# First call: cache miss (full cost)
# Subsequent calls: cache hit (90% cheaper, 85% faster)
agent = AnalysisAgent()
response = agent.handle("Analyze Q3 sales.")
print(response.usage.cache_read_tokens)   # > 0 means served from cache
print(response.usage.cache_write_tokens)  # > 0 means cache was written
```

### 7.6 Conversation Persistence

```python
# Start a new conversation
conv = agent.start_conversation()

# Continue an existing conversation
r1 = agent.with_conversation(conv.id).handle("Hello!")
r2 = agent.with_conversation(conv.id).handle("My order number is #123.")
# Full history is automatically included (subject to AI_SDK.CONVERSATION.MAX_HISTORY)
```

`Message` records: separate rows for user, assistant, tool call, and tool result.
`Conversation.metadata` → storage for custom business data (user_id, session_id, etc.).

### 7.7 Streaming — SSE

SSE format:

```
data: {"type": "text_delta", "text": "Hello"}\n\n
data: {"type": "text_delta", "text": " world"}\n\n
data: {"type": "thinking_delta", "text": "...", "thinking": true}\n\n
data: {"type": "done", "usage": {"prompt_tokens": 42, "completion_tokens": 67, "cache_read_tokens": 30}}\n\n
```

`thinking_delta` chunks are only emitted when a reasoning model is used with `stream_thinking=True`.

### 7.8 DRF Integration

**`ChatAPIView`** — POST `/chat/`

Request:
```json
{
  "prompt": "Can I cancel my order?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream": false
}
```

Response:
```json
{
  "text": "Yes, you can cancel from the order page...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "thinking": null,
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 67,
    "cache_read_tokens": 30,
    "cache_write_tokens": 0,
    "total_tokens": 109
  }
}
```

**`StreamingChatAPIView`** — Same input, returns `Content-Type: text/event-stream`.

### 7.9 Management Commands

```bash
# Writes the AI_SDK settings block in a copy-paste-ready format
python manage.py ai_sdk_publish

# Sends a test request to each provider and reports results
python manage.py ai_sdk_check

# Example ai_sdk_check output:
# ✓ openai/gpt-4o-mini         →  "Hello!"  (312ms)
# ✓ anthropic/claude-3-haiku   →  "Hello!"  (241ms)
# ✗ gemini/gemini-2.0-flash    →  Missing API key  (0ms)
```

### 7.10 Test Helpers

```python
from djangosdk.testing import FakeProvider, override_ai_provider

class MyTests(TestCase):
    def test_basic_response(self):
        with override_ai_provider(FakeProvider(text="Order found.")):
            agent = SupportAgent()
            response = agent.handle("Find my order.")
        self.assertEqual(response.text, "Order found.")

    def test_tool_was_called(self):
        fake = FakeProvider(
            tool_calls=[{"name": "lookup_order", "args": {"order_id": "123"}}],
            text="Your order is on the way.",
        )
        with override_ai_provider(fake):
            agent = SupportAgent()
            agent.handle("Where is order #123?")
        agent.assert_tool_called("lookup_order", order_id="123")

    def test_reasoning_response(self):
        fake = FakeProvider(
            text="The calculation works as follows...",
            thinking="First calculate A, then B...",
        )
        with override_ai_provider(fake):
            agent = MathAgent()
            response = agent.handle("Why is 0.1 + 0.2 not 0.3?")
        self.assertIsNotNone(response.thinking)
```

---

## 8. Roadmap Features

### Phase 2 — Enrichment

**MCP (Model Context Protocol) Integration**

```python
# Exposing Django functions as MCP tools
from djangosdk.mcp import mcp_tool

@mcp_tool
def search_products(query: str, max_results: int = 5) -> list[dict]:
    """Searches the product catalog."""
    return list(Product.objects.filter(name__icontains=query).values()[:max_results])

# Using an external MCP server from an agent
class ResearchAgent(Agent):
    mcp_servers = [
        {"url": "https://mcp.example.com", "transport": "http"},
        {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]},
    ]
```

**Embeddings & RAG**

```python
from djangosdk.embeddings import embed, similarity_search

# Create an embedding
vector = embed("Django ORM is an excellent tool.", provider="openai")

# Similarity search with pgvector (Django ORM)
results = Product.objects.annotate(
    similarity=CosineDistance("embedding", vector)
).filter(similarity__lt=0.3).order_by("similarity")[:5]
```

**RAG Tool (integrated with Agent)**

```python
from djangosdk.tools.builtins import RAGTool

class DocumentAgent(Agent):
    tools = [RAGTool(model=Document, embedding_field="embedding", text_field="content")]
    system_prompt = "Search the document database and provide an answer."
```

**Observability Hooks**

```python
# settings.py
AI_SDK = {
    "OBSERVABILITY": {
        "BACKEND": "langfuse",  # or "langsmith", "opentelemetry", None
        "LANGFUSE_PUBLIC_KEY": env("LANGFUSE_PUBLIC_KEY"),
        "LANGFUSE_SECRET_KEY": env("LANGFUSE_SECRET_KEY"),
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
    },
}
# Every agent call is automatically traced
```

**Token-Based Rate Limiting**

```python
AI_SDK = {
    "RATE_LIMITING": {
        "ENABLED": True,
        "BACKEND": "django_cache",  # Redis recommended
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}
# View level: @ai_rate_limit(tokens_per_minute=10000)
```

**Cost Tracking**

```python
from djangosdk.analytics import cost_report

# 7-day cost report
report = cost_report(days=7)
# {"openai": {"total_usd": 4.23, "total_tokens": 1_200_000}, ...}

# cost_usd field is added to the Message model
msg = Message.objects.latest("created_at")
print(msg.cost_usd)  # e.g. 0.000042
```

**Failover**

```python
AI_SDK = {
    "FAILOVER": ["openai", "anthropic", "groq"],
}
# The agent_failed_over signal is emitted
from djangosdk.signals import agent_failed_over

@receiver(agent_failed_over)
def log_failover(sender, from_provider, to_provider, reason, **kwargs):
    logger.warning(f"Failover: {from_provider} → {to_provider}: {reason}")
```

### Phase 3 — Advanced

**Multi-Agent Orchestration (Five Agentic Patterns)**

```python
from djangosdk.orchestration import handoff, pipeline, parallel

# Pattern 1: Routing
class RouterAgent(Agent):
    @handoff
    def route(self, intent: str) -> Agent:
        return BillingAgent() if intent == "billing" else SupportAgent()

# Pattern 2: Parallelization
class ResearchAgent(Agent):
    async def handle_parallel(self, topic: str) -> AgentResponse:
        results = await parallel(
            SummaryAgent().ahandle(topic),
            FactCheckAgent().ahandle(topic),
            TranslationAgent().ahandle(topic),
        )
        return self.synthesize(results)

# Pattern 3: Evaluator-Optimizer
class WritingAgent(Agent):
    evaluator = CriticAgent()
    max_iterations = 3
```

**Agent Memory Layers**

```python
from djangosdk.memory import EpisodicMemory, SemanticMemory

class PersonalAssistant(Agent):
    episodic_memory = EpisodicMemory(max_episodes=100)   # DB
    semantic_memory = SemanticMemory(backend="pgvector")  # Vector store

# Memory is automatically loaded and included in the agent's context
```

**Image & Audio**

```python
from djangosdk.images import generate_image
from djangosdk.audio import transcribe, synthesize

img = generate_image("Sunset over mountains", provider="openai", size="1024x1024")
text = transcribe(audio_file, provider="openai")  # Whisper
audio = synthesize("Hello world", voice="alloy", provider="openai")
```

---

## 9. Django Settings Schema

```python
# settings.py
AI_SDK = {
    # Default provider and model
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4o-mini",

    # Provider configurations
    "PROVIDERS": {
        "openai": {
            "api_key": env("OPENAI_API_KEY"),
            "default_model": "gpt-4o-mini",
            "organization": None,
            # Default effort for reasoning models
            "default_reasoning_effort": "medium",
        },
        "anthropic": {
            "api_key": env("ANTHROPIC_API_KEY"),
            "default_model": "claude-3-5-haiku-20241022",
            # Default budget for extended thinking
            "default_thinking_budget": 8000,
        },
        "gemini": {
            "api_key": env("GEMINI_API_KEY"),
            "default_model": "gemini-2.0-flash",
        },
        "groq": {
            "api_key": env("GROQ_API_KEY"),
            "default_model": "llama-4-scout-17b-16e-instruct",
        },
        "deepseek": {
            "api_key": env("DEEPSEEK_API_KEY"),
            "default_model": "deepseek-chat",
            "r1_model": "deepseek-reasoner",
        },
        "mistral": {
            "api_key": env("MISTRAL_API_KEY"),
            "default_model": "mistral-medium-3",
        },
        "xai": {
            "api_key": env("XAI_API_KEY"),
            "default_model": "grok-3-fast",
        },
        "azure": {
            "api_key": env("AZURE_OPENAI_API_KEY"),
            "base_url": env("AZURE_OPENAI_ENDPOINT"),
            "api_version": "2025-01-01-preview",
            "default_model": "gpt-4o",
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "default_model": "llama4:scout",
        },
        "perplexity": {
            "api_key": env("PERPLEXITY_API_KEY"),
            "default_model": "sonar",
        },
        "openrouter": {
            "api_key": env("OPENROUTER_API_KEY"),
            "default_model": "anthropic/claude-3.5-haiku",
        },
    },

    # Provider failover order
    "FAILOVER": [],  # e.g. ["openai", "anthropic"]

    # Conversation persistence
    "CONVERSATION": {
        "PERSIST": True,
        "MAX_HISTORY": 50,
        "AUTO_SUMMARIZE": False,  # Summarize when limit is exceeded (Phase 2)
    },

    # Prompt caching
    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],  # Providers that support caching
    },

    # SSE streaming
    "STREAMING": {
        "CHUNK_SEPARATOR": "\n\n",
        "SSE_RETRY_MS": 3000,
        "STREAM_THINKING": False,  # Stream the reasoning process
    },

    # Observability (Phase 2)
    "OBSERVABILITY": {
        "BACKEND": None,  # None | "langsmith" | "langfuse" | "opentelemetry"
    },

    # Rate limiting (Phase 2)
    "RATE_LIMITING": {
        "ENABLED": False,
        "BACKEND": "django_cache",
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}
```

---

## 10. Database Models

### Conversation

```python
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_class = models.CharField(max_length=255)
    provider = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    total_tokens = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "djangosdk"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["agent_class", "-created_at"])]
```

### Message

```python
class Message(models.Model):
    class Role(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        TOOL = "tool", "Tool"
        THINKING = "thinking", "Thinking"  # Reasoning model thinking process

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField(blank=True)
    tool_calls = models.JSONField(null=True, blank=True)
    tool_call_id = models.CharField(max_length=255, null=True, blank=True)
    thinking_content = models.TextField(blank=True)   # Extended thinking content
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    cache_read_tokens = models.IntegerField(null=True, blank=True)
    cache_write_tokens = models.IntegerField(null=True, blank=True)
    cost_usd = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "djangosdk"
        ordering = ["created_at"]
```

---

## 11. Developer API Examples

### Basic Text Generation

```python
from djangosdk.agents import Agent

agent = Agent()
response = agent.handle("Summarize the Django ORM in 3 bullet points.")
print(response.text)
print(response.usage.total_tokens)
```

### Custom Agent + Tool Calling

```python
from djangosdk.agents import Agent
from djangosdk.tools import tool

class SupportAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are a customer support agent. Ask for the order number."
    temperature = 0.3

    @tool
    def lookup_order(self, order_id: str) -> dict:
        """Retrieves order information by order ID."""
        order = Order.objects.get(pk=order_id)
        return {
            "id": order.id,
            "status": order.status,
            "estimated_delivery": str(order.estimated_delivery),
        }

    @tool
    def cancel_order(self, order_id: str, reason: str) -> bool:
        """Cancels the order and notifies the customer."""
        order = Order.objects.get(pk=order_id)
        order.status = "cancelled"
        order.cancellation_reason = reason
        order.save()
        return True

agent = SupportAgent()
response = agent.handle("My order #ORD-789 still hasn't arrived, can you cancel it?")
print(response.text)
```

### Reasoning Model + Structured Output

```python
from pydantic import BaseModel, Field
from djangosdk.agents import Agent
from djangosdk.providers.schemas import ReasoningConfig

class CodeReview(BaseModel):
    score: int = Field(ge=1, le=10, description="Code quality score")
    issues: list[str] = Field(description="Detected issues")
    suggestions: list[str] = Field(description="Improvement suggestions")
    security_risk: bool = Field(description="Whether a security risk was detected")

class CodeReviewAgent(Agent):
    provider = "openai"
    model = "o4-mini"
    system_prompt = "You are a senior software engineer. Analyze the code in depth."
    output_schema = CodeReview
    reasoning = ReasoningConfig(effort="high")

agent = CodeReviewAgent()
response = agent.handle(f"Review this code:\n\n{code_snippet}")

review: CodeReview = response.structured
print(f"Score: {review.score}/10")
print(f"Issues: {review.issues}")
if review.security_risk:
    print("⚠️ Security risk detected!")
```

### Extended Thinking (Claude 3.7 Sonnet)

```python
from djangosdk.agents import Agent
from djangosdk.providers.schemas import ReasoningConfig

class MathAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    system_prompt = "You are a mathematician. Solve step by step."
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=16000,
        stream_thinking=False,
    )

agent = MathAgent()
response = agent.handle("Is P = NP? Explain your arguments.")

# Both the thinking process and the result are accessible
if response.thinking:
    print("Thinking process:", response.thinking[:200], "...")
print("Result:", response.text)
```

### Async View + Streaming

```python
# views.py
from django.http import StreamingHttpResponse
from djangosdk.agents import Agent

async def stream_view(request):
    agent = Agent()
    prompt = request.GET.get("prompt", "")

    async def event_generator():
        async for chunk in agent.astream(prompt):
            yield chunk

    return StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### DRF View

```python
# views.py
from djangosdk.views import ChatAPIView, StreamingChatAPIView

class SupportView(ChatAPIView):
    agent_class = SupportAgent

class SupportStreamView(StreamingChatAPIView):
    agent_class = SupportAgent

# urls.py
urlpatterns = [
    path("api/chat/", SupportView.as_view()),
    path("api/chat/stream/", SupportStreamView.as_view()),
]
```

### Observing Prompt Cache Savings

```python
agent = AnalysisAgent()

# First call — cache is written
r1 = agent.handle("Analyze March sales.")
print(r1.usage.cache_write_tokens)  # > 0

# Second call — read from cache
r2 = agent.handle("Now analyze April sales.")
print(r2.usage.cache_read_tokens)   # > 0  (system prompt served from cache)
# Cost: 90% lower, latency: 85% lower
```

### Testing

```python
from django.test import TestCase
from djangosdk.testing import FakeProvider, override_ai_provider

class SupportAgentTests(TestCase):
    def test_order_lookup(self):
        fake = FakeProvider(
            tool_calls=[{"name": "lookup_order", "args": {"order_id": "789"}}],
            text="Your order is in transit, arriving tomorrow.",
        )
        with override_ai_provider(fake):
            agent = SupportAgent()
            response = agent.handle("Where is order #789?")

        self.assertIn("transit", response.text)
        agent.assert_tool_called("lookup_order", order_id="789")

    def test_cache_hit_simulation(self):
        fake = FakeProvider(
            text="Analysis complete.",
            usage={"cache_read_tokens": 1500, "completion_tokens": 100},
        )
        with override_ai_provider(fake):
            agent = AnalysisAgent()
            response = agent.handle("Analyze.")

        self.assertEqual(response.usage.cache_read_tokens, 1500)

    def test_reasoning_output(self):
        fake = FakeProvider(
            text="Result: X is true.",
            thinking="First I looked at A, then B...",
        )
        with override_ai_provider(fake):
            agent = MathAgent()
            response = agent.handle("Prove it.")

        self.assertIsNotNone(response.thinking)
        self.assertIn("Result", response.text)
```

---

## 12. Dependencies & Security

### Required Dependencies

| Package | Version | Purpose |
|---|---|---|
| `django` | `>=4.2` | Core framework |
| `litellm` | `>=1.82.6,<1.83` | Provider routing (⚠️ see below) |
| `pydantic` | `>=2.0` | Structured output, settings validation |
| `asgiref` | `>=3.7` | Sync/async bridges (bundled with Django) |

### Optional Extras

```toml
[project.optional-dependencies]
drf = ["djangorestframework>=3.14"]
embeddings = ["numpy>=1.24", "pgvector>=0.3"]
observability = ["langfuse>=2.0", "opentelemetry-sdk>=1.20"]
all = [
    "djangorestframework>=3.14",
    "numpy>=1.24",
    "pgvector>=0.3",
    "langfuse>=2.0",
    "opentelemetry-sdk>=1.20",
]
```

### ⚠️ LiteLLM Security Notice (March 2026)

LiteLLM v1.82.7 and v1.82.8 were quarantined from PyPI on March 22–23, 2026 due to a supply chain security incident. `django-ai-sdk` is pinned to the last known-safe version, **v1.82.6**, and actively monitors release notes for verified safe versions.

Version is pinned explicitly in `pyproject.toml`:
```toml
dependencies = [
    "litellm>=1.82.6,<1.83",
]
```

Security policy: Every major litellm update undergoes dependency chain verification before adoption.

---

## 13. Delivery Phases

### Phase 1 — MVP (Weeks 1–4)

**Infrastructure**
- [ ] `pyproject.toml`, package scaffold, CI (GitHub Actions)
- [ ] `conf.py` — settings accessor + validation
- [ ] `apps.py` — `AiSdkConfig`, provider registry init
- [ ] `exceptions.py` — exception hierarchy

**Provider Layer**
- [ ] `providers/base.py` — `AbstractProvider` ABC
- [ ] `providers/schemas.py` — `AgentRequest`, `AgentResponse`, `ReasoningConfig`, `UsageInfo`
- [ ] `providers/litellm_provider.py` — `LiteLLMProvider`
- [ ] `providers/registry.py` — `ProviderRegistry`
- [ ] `providers/cache.py` — `PromptCacheMiddleware`

**Agent Layer**
- [ ] `agents/mixins/promptable.py` — `handle()`, `ahandle()`, `stream()`, `astream()`
- [ ] `agents/mixins/reasoning.py` — o3/R1/Claude 3.7 parameter management
- [ ] `agents/mixins/has_tools.py` — `@tool` decorator, dispatch loop
- [ ] `agents/mixins/has_structured_output.py` — Pydantic validation
- [ ] `agents/mixins/conversational.py` — DB history management
- [ ] `agents/base.py` — `Agent` class

**Django Integration**
- [ ] `models/conversation.py`, `models/message.py`
- [ ] `migrations/0001_initial.py`
- [ ] `streaming/sse.py`, `streaming/async_sse.py`
- [ ] `serializers/conversation.py`, `serializers/message.py` (DRF)
- [ ] `views/chat.py`, `views/streaming.py` (DRF)
- [ ] `signals.py`
- [ ] `management/commands/ai_sdk_publish.py`
- [ ] `management/commands/ai_sdk_check.py`
- [ ] `testing/fakes.py`, `testing/assertions.py`

**Quality & Release**
- [ ] Test suite (≥90% coverage target)
- [ ] README, Quickstart guide
- [ ] PyPI release: `uv add django-ai-sdk`

---

### Phase 2 — Enrichment (Weeks 5–8)

- [ ] `mcp/client.py`, `mcp/server.py`, `mcp/decorators.py` — MCP support
- [ ] `tools/builtins/web_search.py`, `tools/builtins/web_fetch.py`
- [ ] `tools/builtins/rag.py` — pgvector integration
- [ ] `memory/episodic.py` — DB-backed agent memory
- [ ] Observability backends (LangSmith, Langfuse, OTel)
- [ ] Token-based rate limiting
- [ ] Cost tracking (Message.cost_usd, analytics module)
- [ ] Failover mechanism + `agent_failed_over` signal
- [ ] Django Admin integration (ConversationAdmin, MessageAdmin)
- [ ] Extended documentation + example application repository

---

### Phase 3 — Advanced (Weeks 9–12)

- [ ] `images/` module — DALL-E 3, Gemini Imagen 3, xAI Aurora
- [ ] `audio/` module — Whisper transcription, TTS synthesis
- [ ] `memory/semantic.py` — vector store-backed semantic memory
- [ ] Multi-agent orchestration: `handoff`, `pipeline`, `parallel`
- [ ] Evaluator-Optimizer agentic pattern
- [ ] `AUTO_SUMMARIZE` — conversation summarization (when limit is exceeded)
- [ ] Performance benchmarks
- [ ] Changelog, contributing guide, full API reference

---

## 14. Success Metrics

### Adoption

| Metric | Target | Timeframe |
|---|---|---|
| PyPI downloads | 1,000 | First month |
| PyPI downloads | 10,000 | First 3 months |
| GitHub stars | 500 | First 3 months |
| Listed on Awesome Django | Included | First 2 months |
| External contributions (PRs) | 5+ | First 3 months |

### Quality

| Metric | Target |
|---|---|
| Test coverage | ≥ 90% |
| CI pass rate | 100% (Python 3.11/3.12, Django 4.2/5.0/5.1) |
| Open P0 bugs | 0 |
| Reasoning model tests | o3, Claude 3.7, DeepSeek R1 — smoke test on every release |
| LiteLLM security audit | Before every major update |

### Ecosystem Impact

- 5+ blog posts or tutorials referencing `django-ai-sdk`
- At least 1 popular Django starter kit integrates it
- Community discussion on Django Forum or Discord
- 1 presentation / talk at a Django conference (DjangoCon)

---

*This PRD is a living document. It was prepared based on research conducted as of March 2026. It will be updated as implementation progresses and community feedback is received.*
