# E-Commerce Concierge

**Source:** [github.com/ziyacivan/ecommerce-concierge](https://github.com/ziyacivan/ecommerce-concierge)

A conversational AI shopping assistant that answers product questions, checks stock, and handles orders — all through natural language.

## What it demonstrates

- `HasTools` + `Conversational` mixin composition
- Tools for product lookup, inventory check, and order management
- Multi-turn conversation with `EpisodicMemory`
- Streaming responses with `astream()` over SSE

## Setup

```bash
git clone https://github.com/ziyacivan/ecommerce-concierge.git
cd ecommerce-concierge
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools, Conversational
from djangosdk.memory.episodic import EpisodicMemory
from djangosdk.tools import tool

class ConciergeAgent(Agent, HasTools, Conversational):
    provider = "openai"
    model = "gpt-4.1"
    memory = EpisodicMemory()
    system_prompt = (
        "You are a helpful e-commerce shopping assistant. "
        "Use the available tools to look up products, check stock, "
        "and assist customers with their orders."
    )

    @tool
    def search_products(self, query: str, category: str | None = None) -> list[dict]:
        """Search products by name or description."""
        qs = Product.objects.filter(name__icontains=query)
        if category:
            qs = qs.filter(category=category)
        return list(qs.values("id", "name", "price", "stock"))

    @tool
    def get_order_status(self, order_id: str) -> dict:
        """Returns the current status of an order."""
        order = Order.objects.get(pk=order_id)
        return {"id": order.id, "status": order.status, "eta": str(order.eta)}
```

## How the Tool Loop Works

1. Customer message + tool schemas → provider
2. Model picks the right tool (e.g. `search_products`)
3. SDK executes the tool and appends the result to the history
4. Model generates a natural-language reply with full context

## Try These Prompts

- `"Do you have wireless headphones under $100?"`
- `"What's the status of order #ORD-4821?"`
- `"Show me your best-selling laptops"`
