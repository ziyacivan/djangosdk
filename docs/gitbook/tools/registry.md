# Tool Registry

`ToolRegistry` manages the tools registered on an agent and handles dispatch when the model calls a tool.

## How It Works

`HasTools._get_tool_registry()` builds and caches a `ToolRegistry` from the `tools` list on the agent class. The registry is created once per agent instance on first access.

## Direct Usage

You rarely need to interact with `ToolRegistry` directly — it is managed automatically. However, you can use it for testing or advanced scenarios:

```python
from django_ai_sdk.tools.registry import ToolRegistry
from myapp.tools import lookup_order, cancel_order

registry = ToolRegistry()
registry.register(lookup_order)
registry.register(cancel_order)

# Get all tool schemas (sent to the model)
schemas = registry.get_schemas()

# Execute a tool by name
result = registry.execute("lookup_order", {"order_id": "ABC123"})

# Async execution
result = await registry.aexecute("lookup_order", {"order_id": "ABC123"})
```

## Registering BaseTool Instances

In addition to `@tool`-decorated functions, you can register `BaseTool` subclasses:

```python
from django_ai_sdk.tools.base import BaseTool

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get the current weather for a city."

    def execute(self, city: str, unit: str = "celsius") -> str:
        return f"Sunny, 22°C in {city}"

class WeatherAgent(Agent):
    tools = [WeatherTool()]
```

## Tool Execution Error Handling

When a tool raises an exception during execution, `HasTools._execute_tool_calls()` catches it and sends the error message back to the model as the tool result. The model can then decide how to respond (retry, report an error, etc.):

```python
# If lookup_order raises ValueError("Order not found"):
# The model receives: {"role": "tool", "content": "Error: Order not found"}
```
