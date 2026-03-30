# FakeProvider & FakeAgent

`djangosdk` ships with test utilities that let you write unit tests without calling real APIs.

## FakeProvider

`FakeProvider` is an in-memory `AbstractProvider` that returns a pre-configured response. It records every `AgentRequest` it receives in `fake.calls`.

### Basic Usage

```python
from djangosdk.testing.fakes import FakeProvider, override_ai_provider
from myapp.agents import SupportAgent

def test_support_agent():
    fake = FakeProvider(text="Your order has been shipped.")

    with override_ai_provider(fake):
        agent = SupportAgent()
        response = agent.handle("Where is my order?")

    assert response.text == "Your order has been shipped."
    assert len(fake.calls) == 1
```

### Constructor Parameters

```python
FakeProvider(
    text="Fake response.",           # Response text
    thinking="Step 1: ...",          # Thinking/reasoning content (optional)
    tool_calls=[                     # Tool calls to simulate (optional)
        {
            "id": "call_1",
            "name": "lookup_order",
            "arguments": {"order_id": "ABC123"},
        }
    ],
    usage=UsageInfo(                 # Token usage (optional)
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
    ),
    stream_chunks=["Hello", ", world!"],  # Custom stream chunks (optional)
)
```

### Inspecting Calls

```python
fake = FakeProvider(text="Hello!")

with override_ai_provider(fake):
    agent.handle("Say hello")

# Inspect the recorded request
request = fake.calls[0]
print(request.model)         # The model used
print(request.system_prompt) # The system prompt
print(request.messages)      # Full message list
print(request.tools)         # Tool schemas sent
```

## FakeAgent

`FakeAgent` is a pre-wired agent backed by `FakeProvider`. Use it when you need a complete agent without configuring Django settings:

```python
from djangosdk.testing.fakes import FakeAgent

def test_pipeline():
    agent = FakeAgent(text="Order found: shipped.")
    response = agent.handle("Where is my order?")
    assert response.text == "Order found: shipped."
```

## `override_ai_provider` Context Manager

`override_ai_provider` patches `registry.get()` so all agents in the block use the given provider:

```python
from djangosdk.testing.fakes import override_ai_provider, FakeProvider

fake = FakeProvider(text="Test response")
with override_ai_provider(fake):
    # Any agent.handle() call will use `fake`
    response = MyAgent().handle("Hello")
```

## Testing Tool Calls

To simulate an agent that calls tools:

```python
fake = FakeProvider(
    text="The order has been cancelled.",
    tool_calls=[
        {
            "id": "call_abc",
            "name": "cancel_order",
            "arguments": {"order_id": "XYZ"},
        }
    ],
)

with override_ai_provider(fake):
    response = SupportAgent().handle("Cancel order XYZ")
```

## Testing Streaming

```python
fake = FakeProvider(stream_chunks=["Hello", ", ", "world", "!"])

with override_ai_provider(fake):
    chunks = list(SupportAgent().stream_chunks("Say hello"))

assert "".join(c.text for c in chunks if c.type == "text_delta") == "Hello, world!"
```
