# djangosdk

**djangosdk** is a Django-native AI SDK inspired by the Laravel AI SDK. It provides a unified, agent-centric abstraction over 12+ AI providers, built entirely on top of [litellm](https://github.com/BerriAI/litellm).

## Why djangosdk?

Django is the standard framework for Python web development, yet as of 2026 there is a significant ecosystem gap when it comes to AI integration. Developers must wire up provider-specific SDKs individually, rewrite the same streaming, tool-calling, and conversation history boilerplate in every project, and maintain separate code paths for every provider.

`djangosdk` solves this with:

| Feature | Description |
|---|---|
| **Unified provider API** | 12+ providers, one interface. Switch from OpenAI to Anthropic in one line. |
| **Agent-centric design** | Compose agents from mixins: `Promptable`, `HasTools`, `HasStructuredOutput`, `Conversational`, `ReasoningMixin` |
| **Reasoning model support** | Native parameters for o3/o4-mini, Claude 3.7 extended thinking, and DeepSeek R1 |
| **Async-first streaming** | SSE streaming with Django 5.x async view support |
| **Prompt caching** | Automatic Anthropic and OpenAI native caching |
| **Structured output** | Pydantic v2-native JSON schema enforcement |
| **Conversation persistence** | Django ORM-backed history with auto-summarization |
| **DRF-ready** | Pre-built `ChatAPIView`, `StreamingChatAPIView`, and serializers |
| **Test utilities** | `FakeProvider`, `FakeAgent`, and assertion helpers — no real API calls in tests |
| **Observability** | LangSmith, Langfuse, and OpenTelemetry hooks |
| **MCP support** | Run Django apps as MCP servers or clients |

## Quick Example

```python
# myapp/agents.py
from djangosdk.agents.base import Agent
from djangosdk.tools.decorator import tool

@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"Sunny, 22°C in {city}"

class WeatherAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "You are a helpful weather assistant."
    tools = [get_weather]

# In a Django view
agent = WeatherAgent()
response = agent.handle("What is the weather in Istanbul?")
print(response.text)
```

## Supported Providers

All providers are accessed through litellm. The following are actively tested:

**Reasoning models** — o3, o3-pro, o4-mini, Claude 3.7 Sonnet, DeepSeek R1, Gemini 2.5 Flash

**Standard models** — GPT-4.1, GPT-4.5, Claude 3.5 Haiku, Gemini 2.0 Flash, Llama 4, Mistral, Grok, Qwen

## Requirements

- Python ≥ 3.11
- Django ≥ 4.2
- litellm == 1.82.6

## Next Steps

- [Installation](getting-started/installation.md)
- [Configuration](getting-started/configuration.md)
- [Quickstart](getting-started/quickstart.md)
