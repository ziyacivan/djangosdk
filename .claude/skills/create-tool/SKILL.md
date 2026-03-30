---
name: create-tool
description: >
  Creates a @tool decorated function with proper type hints and docstring so the
  JSON schema is generated automatically. Invoke when the user says "create a tool",
  "add a tool function", "write a @tool for [action]", "make a tool that [does X]",
  "define a tool called [name]", "I need a tool for [task]", or "implement a
  tool-calling function". Also triggers on "add a tool to the agent".
triggers:
  - create a tool
  - add a tool
  - write a tool
  - make a tool
  - define a tool
  - implement a tool
  - I need a tool for
  - add a tool to the agent
  - tool function
  - tool decorator
---

# Create a `@tool` Decorated Function

You are creating a tool function for use with a `django-ai-sdk` Agent.

## How `@tool` Works Internally

The `@tool` decorator (from `django_ai_sdk.tools.decorator`) does three things:
1. Reads `fn.__doc__` → becomes the tool's `description` field in the JSON schema
2. Reads `inspect.signature(fn)` + type annotations → builds `parameters` JSON schema
3. Sets `fn._is_tool = True` and `fn._tool_schema = {...}` on the function object

The schema conforms to the OpenAI/Anthropic tool format and litellm passes it through unmodified.

## Python Types → JSON Schema Mapping

| Python type | JSON Schema |
|---|---|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list[T]` | `{"type": "array", "items": <T schema>}` |
| `dict[str, T]` | `{"type": "object"}` |
| `Literal["a", "b"]` | `{"enum": ["a", "b"]}` |
| `T | None` | optional — not added to `required` list |
| Pydantic `BaseModel` | nested object schema via `model_json_schema()` |

## Rules for Well-Formed Tools

1. **Docstring is mandatory** — it becomes the tool description shown to the LLM. Write it as an imperative sentence: "Return the current weather for a given city."
2. **All parameters must be type-annotated** — unannotated parameters are skipped and won't appear in the schema.
3. **Return type should be `str` or JSON-serializable** — the SDK serializes the return value before appending it as a tool result.
4. **Raise `ToolError` for recoverable failures** — the SDK sends the error message back to the model as a tool result so the model can retry or inform the user.
5. **No side-effects that can't be undone** — tools run inside the dispatch loop; unexpected state changes break the conversation.

## Tool Template

```python
from typing import Literal
from django_ai_sdk.tools.decorator import tool


@tool
def [tool_name](
    [param1]: [type1],
    [param2]: [type2] = [default],
) -> str:
    """[Imperative description of what this tool does. One to three sentences max.]

    Args:
        [param1]: [Description of param1].
        [param2]: [Description of param2]. Defaults to [default].
    """
    # implementation
    result = ...
    return str(result)
```

## Django ORM Inside Tools

Synchronous tools can call the ORM directly (the dispatch loop is synchronous):

```python
import json
from django_ai_sdk.tools.decorator import tool


@tool
def get_user_orders(user_id: int) -> str:
    """Return a JSON list of the 10 most recent orders for a user.

    Args:
        user_id: The primary key of the user.
    """
    from myapp.models import Order
    orders = list(
        Order.objects.filter(user_id=user_id)
        .values("id", "total", "status")[:10]
    )
    return json.dumps(orders)
```

For async contexts, define an async tool — the async dispatch loop in `Agent.ahandle()` awaits it:

```python
import json
from django_ai_sdk.tools.decorator import tool
from asgiref.sync import sync_to_async


@tool
async def get_user_orders_async(user_id: int) -> str:
    """Return a JSON list of the 10 most recent orders for a user.

    Args:
        user_id: The primary key of the user.
    """
    from myapp.models import Order
    orders = await sync_to_async(list)(
        Order.objects.filter(user_id=user_id).values("id", "total", "status")[:10]
    )
    return json.dumps(orders)
```

## Attaching Tools to an Agent

```python
from django_ai_sdk.agents.base import Agent

class OrderAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You help users track their orders."
    tools = [get_user_orders, another_tool]
```

## Real-World Examples

### Web search tool

```python
@tool
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web and return the top results as a JSON list.

    Args:
        query: The search query string.
        num_results: Number of results to return. Defaults to 5.
    """
    # integrate with your search API
    results = my_search_api(query, num_results)
    return json.dumps(results)
```

### Calculator tool

```python
from decimal import Decimal, InvalidOperation
from django_ai_sdk.tools.exceptions import ToolError


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result.

    Args:
        expression: A safe arithmetic expression, e.g. "2 + 2 * 10".
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        raise ToolError(f"Invalid expression: {e}") from e
```

## Testing Tools in Isolation

Tools are plain functions — test them directly without any agent machinery:

```python
def test_get_weather_returns_string():
    result = get_weather("Istanbul", "celsius")
    assert isinstance(result, str)


def test_get_weather_schema():
    assert get_weather._is_tool is True
    schema = get_weather._tool_schema
    assert schema["function"]["name"] == "get_weather"
    props = schema["function"]["parameters"]["properties"]
    assert "city" in props
    assert props["city"]["type"] == "string"
    assert "unit" in props
    assert props["unit"]["enum"] == ["celsius", "fahrenheit"]
```
