# Tool-Calling Agent

**Source:** [`examples/02-tool-calling/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/02-tool-calling)

A customer support bot that uses the `@tool` decorator to give the agent real capabilities — order lookup, cancellation, and weather checks.

## What it demonstrates

- The `HasTools` mixin and `@tool` decorator
- Multi-tool dispatch: the model picks the right tool automatically
- Accessing `response.tool_calls` to see which tools were invoked
- Calling tool methods directly (outside the agent loop)

## Setup

```bash
cd examples/02-tool-calling
pip install djangosdk python-decouple
cp .env.example .env   # set ANTHROPIC_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools
from djangosdk.tools import tool

class SupportAgent(Agent, HasTools):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are a customer support agent."
    temperature = 0.3

    @tool
    def lookup_order(self, order_id: str) -> dict:
        """Retrieves order details by order ID (e.g. ORD-001)."""
        order = Order.objects.get(pk=order_id)
        return {"id": order.id, "status": order.status}

    @tool
    def cancel_order(self, order_id: str, reason: str) -> dict:
        """Cancels an order that hasn't been shipped yet."""
        ...
```

## How the Tool Loop Works

1. User message + tool JSON schemas → provider
2. Model returns `tool_calls` → SDK executes each matching method
3. Tool results are appended to the message history
4. Model generates the final answer with full context
5. `response.tool_calls` lists every tool that was called

djangosdk handles steps 2–4 automatically. You only write the tool functions.

## Try These Prompts

- `"Where is my order ORD-001?"`
- `"Cancel order ORD-002, I changed my mind"`
- `"Will stormy weather in London delay order ORD-001?"`
