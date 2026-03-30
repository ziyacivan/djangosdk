---
name: write-tests
description: >
  Writes pytest tests for django-ai-sdk modules using FakeProvider and the SDK's
  assertion helpers. Invoke when the user says "write tests for", "add tests for",
  "test this agent", "test this module", "write unit tests", "write integration
  tests for the agent", "assert that the agent calls the tool", "verify the prompt
  is sent", or "add test coverage for [module]". Also triggers on "how do I test
  this agent" or "how do I test tool calling".
triggers:
  - write tests for
  - add tests for
  - test this agent
  - test this module
  - write unit tests
  - write integration tests for
  - assert the agent calls
  - verify the prompt is sent
  - add test coverage for
  - how do I test this agent
  - how do I test tool calling
---

# Write Tests with FakeProvider

You are writing pytest tests for `django-ai-sdk` code. The golden rule: **never call real AI APIs in tests**. Always use `FakeProvider`.

## Core Testing Primitives

### `FakeProvider`

```python
from djangosdk.testing.fakes import FakeProvider

provider = FakeProvider()
provider.set_response("Hello, world!")
```

`FakeProvider` implements `AbstractProvider`. It:
- Records every `AgentRequest` in `provider.call_log`
- Returns whatever you primed with `set_response(text, tool_calls=None)`
- Supports chaining: call `set_response()` multiple times to queue responses in order
- Has `acomplete()` and `astream()` async variants

### `assert_prompt_sent`

```python
from djangosdk.testing.assertions import assert_prompt_sent

assert_prompt_sent(provider, "analyze Q3 sales")
# Raises AssertionError if no recorded request contains that substring
```

### `assert_tool_called`

```python
from djangosdk.testing.assertions import assert_tool_called

assert_tool_called(provider, "get_weather")
# Raises AssertionError if no recorded request included a tool named "get_weather"
```

## Test Patterns

### Pattern 1 — Unit Test `handle()`

```python
import pytest
from djangosdk.testing.fakes import FakeProvider
from djangosdk.testing.assertions import assert_prompt_sent
from myapp.agents import SummaryAgent


@pytest.fixture
def fake_provider():
    return FakeProvider()


def test_summary_agent_returns_text(fake_provider):
    fake_provider.set_response("Summary: revenue grew 12% in Q3.")
    agent = SummaryAgent()
    agent._provider = fake_provider

    response = agent.handle("Summarize Q3 results.")

    assert "Q3" in response.text
    assert_prompt_sent(fake_provider, "Summarize Q3 results")


def test_summary_agent_uses_system_prompt(fake_provider):
    fake_provider.set_response("done")
    agent = SummaryAgent()
    agent._provider = fake_provider

    agent.handle("hello")

    assert_prompt_sent(fake_provider, agent.system_prompt)
```

### Pattern 2 — Test Tool Dispatch Loop

```python
from djangosdk.testing.fakes import FakeProvider
from djangosdk.testing.assertions import assert_tool_called
from myapp.agents import WeatherAgent


def test_weather_agent_calls_get_weather_tool(fake_provider):
    # First response: model requests a tool call
    fake_provider.set_response(
        text="",
        tool_calls=[{"name": "get_weather", "arguments": {"city": "Istanbul"}}]
    )
    # Second response: model uses tool result to produce final reply
    fake_provider.set_response("It's 22°C and sunny in Istanbul.")

    agent = WeatherAgent()
    agent._provider = fake_provider

    response = agent.handle("What's the weather in Istanbul?")

    assert "Istanbul" in response.text
    assert_tool_called(fake_provider, "get_weather")
    assert len(fake_provider.call_log) == 2  # one tool call, one final response
```

### Pattern 3 — Test Structured Output

```python
import json
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import SentimentAgent


def test_sentiment_agent_returns_pydantic_model(fake_provider):
    fake_provider.set_response(json.dumps({
        "sentiment": "positive",
        "confidence": 0.95,
        "reasoning": "The text uses enthusiastic language.",
    }))
    agent = SentimentAgent()
    agent._provider = fake_provider

    response = agent.handle("I love this product!")

    assert response.structured is not None
    assert response.structured.sentiment == "positive"
    assert response.structured.confidence > 0.5
```

### Pattern 4 — Test Async Agent

```python
import pytest


@pytest.mark.asyncio
async def test_summary_agent_async(fake_provider):
    fake_provider.set_response("Async summary result.")
    agent = SummaryAgent()
    agent._provider = fake_provider

    response = await agent.ahandle("Summarize this.")

    assert "summary" in response.text.lower()
```

### Pattern 5 — Test Streaming

```python
def test_streaming_yields_chunks(fake_provider):
    fake_provider.set_stream_chunks(["Hello", ", ", "world", "!"])
    agent = SummaryAgent()
    agent._provider = fake_provider

    chunks = list(agent.stream("Say hello."))

    assert "".join(c.text for c in chunks) == "Hello, world!"
```

### Pattern 6 — Test Django Signals

```python
from django.test import TestCase
from djangosdk.signals import agent_completed
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import SummaryAgent


class AgentSignalTest(TestCase):
    def test_agent_completed_signal_fires(self):
        received = []

        def handler(sender, response, **kwargs):
            received.append(response)

        agent_completed.connect(handler)
        try:
            fake = FakeProvider()
            fake.set_response("done")
            agent = SummaryAgent()
            agent._provider = fake
            agent.handle("hello")
        finally:
            agent_completed.disconnect(handler)

        self.assertEqual(len(received), 1)
```

## `conftest.py` Template

Add to your project root `conftest.py`:

```python
import django
from django.conf import settings


def pytest_configure():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "djangosdk",
            ],
            AI_SDK={
                "DEFAULT_PROVIDER": "fake",
                "DEFAULT_MODEL": "fake-model",
                "PROVIDERS": {},
            },
            USE_TZ=True,
        )
```

## Testing Internal SDK Modules

### Testing `@tool` schema generation

```python
from djangosdk.tools.decorator import tool


@tool
def add(a: int, b: int) -> str:
    """Add two integers and return the result."""
    return str(a + b)


def test_tool_schema_is_attached():
    assert add._is_tool is True
    schema = add._tool_schema
    assert schema["function"]["name"] == "add"
    assert schema["function"]["description"] == "Add two integers and return the result."
    props = schema["function"]["parameters"]["properties"]
    assert props["a"]["type"] == "integer"
    assert props["b"]["type"] == "integer"
    assert set(schema["function"]["parameters"]["required"]) == {"a", "b"}
```

### Testing `FakeProvider` itself

```python
from djangosdk.testing.fakes import FakeProvider
from djangosdk.agents.request import AgentRequest


def test_fake_provider_records_requests():
    provider = FakeProvider()
    provider.set_response("hello")

    request = AgentRequest(messages=[{"role": "user", "content": "hi"}])
    provider.complete(request)

    assert len(provider.call_log) == 1
    assert provider.call_log[0] == request
```

## Coverage Target

The project targets **90% test coverage**. Run with:

```bash
pytest --cov=djangosdk --cov-report=term-missing
```

Priority modules to cover first:
1. `agents/base.py` — tool dispatch loop, handle/ahandle paths
2. `providers/litellm_provider.py` — request translation, reasoning model detection
3. `tools/decorator.py` — schema generation for all supported types
4. `streaming/sse.py` — SSE formatting, response headers
5. `testing/fakes.py` and `testing/assertions.py` — the utilities themselves
