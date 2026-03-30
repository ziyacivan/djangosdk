# Quickstart

This guide walks through the most common use cases in 5 minutes.

## 1. Basic Agent

```python
# myapp/agents.py
from django_ai_sdk.agents.base import Agent

class HelloAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "You are a helpful assistant."

# Use in a Django view
agent = HelloAgent()
response = agent.handle("What is Django?")
print(response.text)
print(response.usage.total_tokens)
```

## 2. Agent with Tools

```python
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.tools.decorator import tool

@tool
def get_order_status(order_id: str) -> str:
    """Look up the current status of an order.

    Args:
        order_id: The unique order identifier.
    """
    # Your database lookup here
    return f"Order {order_id} is shipped."

@tool
def cancel_order(order_id: str, reason: str = "customer request") -> str:
    """Cancel an order.

    Args:
        order_id: The order to cancel.
        reason: Reason for cancellation.
    """
    return f"Order {order_id} cancelled. Reason: {reason}"

class SupportAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "You are a customer support agent."
    tools = [get_order_status, cancel_order]

agent = SupportAgent()
response = agent.handle("Cancel order #ABC123 because the customer changed their mind.")
print(response.text)
```

## 3. Structured Output

```python
from pydantic import BaseModel
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.agents.mixins.has_structured_output import HasStructuredOutput

class Sentiment(BaseModel):
    label: str       # "positive" | "negative" | "neutral"
    confidence: float
    reason: str

class SentimentAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "Analyze the sentiment of the given text."
    output_schema = Sentiment

agent = SentimentAgent()
response = agent.handle("I absolutely love this product!")
result: Sentiment = response.structured
print(result.label, result.confidence)
```

## 4. Conversation Persistence

```python
from django_ai_sdk.agents.base import Agent

class ChatAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "You are a friendly assistant."

agent = ChatAgent()
conv = agent.start_conversation()          # Creates a Conversation record

r1 = agent.with_conversation(conv.id).handle("My name is Alice.")
r2 = agent.with_conversation(conv.id).handle("What is my name?")
print(r2.text)  # "Your name is Alice."
```

## 5. Streaming (DRF View)

```python
# myapp/views.py
from django.urls import path
from django_ai_sdk.agents.base import Agent

class AssistantAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are a helpful assistant."

def stream_view(request):
    agent = AssistantAgent()
    prompt = request.GET.get("prompt", "Say hello.")
    return agent.stream(prompt)  # Returns a StreamingHttpResponse

urlpatterns = [
    path("stream/", stream_view),
]
```

## 6. Reasoning Models

```python
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.providers.schemas import ReasoningConfig

class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    system_prompt = "Solve the problem step by step."
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=15000,
    )

agent = ThinkingAgent()
response = agent.handle("Prove that sqrt(2) is irrational.")
print(response.thinking.content)  # The reasoning trace
print(response.text)              # The final answer
```

## 7. Async View

```python
# myapp/views.py
from django.http import JsonResponse
from django_ai_sdk.agents.base import Agent

class AsyncAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"

async def ai_view(request):
    agent = AsyncAgent()
    response = await agent.ahandle(request.GET.get("q", ""))
    return JsonResponse({"text": response.text})
```

## Next Steps

- [Agents in depth](../agents/overview.md)
- [Tools](../tools/decorator.md)
- [Streaming](../streaming/overview.md)
- [Testing](../testing/fake-provider.md)
