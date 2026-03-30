# HasTools

`HasTools` adds tool-calling capability. Declare tools on the class as a list of `@tool`-decorated functions or `BaseTool` instances.

## Declaring Tools

```python
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.tools.decorator import tool

@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by ID.

    Args:
        order_id: The order identifier.
    """
    return f"Order {order_id}: shipped on 2026-03-28"

@tool
def cancel_order(order_id: str, reason: str = "customer request") -> str:
    """Cancel an existing order.

    Args:
        order_id: The order to cancel.
        reason: Reason for cancellation.
    """
    return f"Cancelled {order_id}"

class SupportAgent(Agent):
    tools = [lookup_order, cancel_order]
```

## How It Works

1. On first access, `HasTools` builds a `ToolRegistry` from the `tools` list
2. Each tool's JSON schema is extracted (via the `@tool` decorator)
3. Schemas are sent to the provider with every request
4. When the provider returns a `tool_call`, the registry dispatches to the matching function
5. The result is appended as a `{"role": "tool", ...}` message and the loop continues

## Async Tool Execution

Both sync and async dispatch are supported. If your tool function is a coroutine, the registry uses `await`:

```python
@tool
async def fetch_from_api(endpoint: str) -> str:
    """Fetch data from an external API."""
    async with httpx.AsyncClient() as client:
        r = await client.get(endpoint)
        return r.text
```

## Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `tools` | `list` | `[]` | List of `@tool` functions or `BaseTool` instances |
| `max_tool_iterations` | `int` | `10` | Maximum tool-call rounds per `handle()` call |

## Error Handling

If a tool raises an exception during execution, the error message is captured as the tool result and sent back to the model. The model can then decide how to handle it.
