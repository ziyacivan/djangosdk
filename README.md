[![PyPI version](https://badge.fury.io/py/djangosdk.svg)](https://pypi.org/project/djangosdk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/djangosdk.svg)](https://pypi.org/project/djangosdk/)

# djangosdk

A Django-native AI SDK. One `Agent` class, 12+ providers, no boilerplate.

`djangosdk` gives Django developers a consistent API for building AI agents — tool calling, streaming, structured output, conversation persistence, reasoning models — without wiring up provider SDKs or rewriting the same patterns in every project.

```python
from djangosdk import Agent, tool

@tool
def get_order(order_id: str) -> str:
    """Fetch the current status of an order.

    Args:
        order_id: The order identifier.
    """
    return Order.objects.get(pk=order_id).status

class SupportAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are a helpful customer support agent."
    tools = [get_order]

response = SupportAgent().handle("Where is my order #1234?")
print(response.text)
```

Switching providers is a one-line change. The tool dispatch loop, prompt caching, conversation history, and streaming responses are handled for you regardless of which model you use.

## Getting started

```bash
pip install djangosdk
```

```python
# settings.py
INSTALLED_APPS = ["djangosdk", ...]

AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4o-mini",
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
        "anthropic": {"api_key": env("ANTHROPIC_API_KEY")},
    },
}
```

## Structured output

```python
from pydantic import BaseModel
from djangosdk import Agent

class Sentiment(BaseModel):
    label: str
    score: float

class SentimentAgent(Agent):
    model = "gpt-4o-mini"
    output_schema = Sentiment

response = SentimentAgent().handle("I love this product but the shipping was slow.")
print(response.structured)  # Sentiment(label='mixed', score=0.6)
```

## Streaming

```python
from djangosdk.streaming.async_sse import AsyncSSEResponse

async def chat_view(request):
    return AsyncSSEResponse(SupportAgent().astream(request.POST["message"]))
```

## Reasoning models

```python
from djangosdk import Agent
from djangosdk.providers.schemas import ReasoningConfig

class AnalysisAgent(Agent):
    provider = "openai"
    model = "o3"
    reasoning = ReasoningConfig(effort="high")
```

`ReasoningConfig` maps to the right parameter for each provider — `reasoning_effort` for o3/o4-mini, `extended_thinking` for Claude 3.7, `budget_tokens` for DeepSeek R1.

## Testing

```python
from djangosdk.testing.fakes import FakeProvider
from djangosdk.testing.assertions import assert_tool_called

def test_support_agent(settings):
    settings.AI_SDK = {"DEFAULT_PROVIDER": "fake", "PROVIDERS": {"fake": {}}}
    FakeProvider.set_response("Your order is shipped.")

    response = SupportAgent().handle("Where is order #1234?")

    assert_tool_called(SupportAgent, "get_order", order_id="1234")
    assert "shipped" in response.text
```

`FakeProvider` never calls a real API. `assert_tool_called` and `assert_prompt_sent` let you make assertions on what the agent actually did.

## Philosophy

Django projects tend to share the same AI patterns: a provider client, a prompt template, a tool dispatch loop, a table for conversation history, a streaming endpoint. Every team writes their own version. `djangosdk` is the version that doesn't need to be written again.

The design follows Django's own conventions. Agents are classes. Capabilities are mixins — add `HasTools`, `HasStructuredOutput`, or `Conversational` to the base `Agent` class and get exactly what you need, nothing more. Configuration lives in `AI_SDK` in `settings.py`. The ORM, signals, management commands, and DRF integration all work the way Django developers expect them to.

The provider layer is built on litellm. We don't call provider SDKs directly and neither should you. The abstraction is thin on purpose — if litellm supports a model, `djangosdk` supports it.

## Why djangosdk

- **Provider independence.** Swap `provider = "openai"` for `provider = "anthropic"` and nothing else changes. The same tools, the same structured output schema, the same streaming response.
- **Reasoning models work out of the box.** o3, Claude 3.7 extended thinking, and DeepSeek R1 each require different API parameters. `djangosdk` handles the translation.
- **The tool loop is not your problem.** Define `@tool` functions, attach them to an agent, and the SDK handles calling them, feeding results back, and repeating until the model is done — up to a configurable limit.
- **Django-native persistence.** Conversation history is stored in `Conversation` and `Message` ORM models. Episodic and semantic memory layers are available for more complex agents.
- **Test helpers that are actually useful.** `FakeProvider` gives you deterministic responses. The assertion helpers let you verify prompts and tool calls without mocking internals.
- **MCP support.** Run Django applications as MCP servers or connect to external MCP servers from your agents.

## How it compares

|  | djangosdk | django-ai-assistant | LangChain |
| --- | --- | --- | --- |
| Provider support | 12+ via litellm | OpenAI only | Many |
| Django-native | Yes | Partial | No |
| Reasoning model support | Yes | No | Partial |
| Prompt caching | Yes (Anthropic + OpenAI) | No | No |
| DRF views + serializers | Yes | No | No |
| Test utilities | Yes | No | No |
| MCP | Yes | No | No |

## Documentation

[djangosdk.ai](https://djangosdk.ai)

## License

[MIT](LICENSE)
