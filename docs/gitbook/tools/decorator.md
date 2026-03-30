# The @tool Decorator

The `@tool` decorator marks a Python function as an AI tool. It automatically generates an OpenAI-compatible JSON schema from the function's signature and docstring.

## Basic Usage

```python
from django_ai_sdk.tools.decorator import tool

@tool
def get_weather(city: str, unit: str = "celsius") -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to look up.
        unit: Temperature unit, either celsius or fahrenheit.
    """
    return f"Sunny, 22°C in {city}"
```

The decorator:
1. Reads the function signature to determine parameter names and types
2. Reads the first paragraph of the docstring as the tool description
3. Reads `Args:` section of the docstring for parameter descriptions
4. Generates the JSON schema and attaches it as `fn.__tool_schema__`

## Supported Type Annotations

| Python type | JSON schema type |
|---|---|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `list` | `array` |
| `list[str]` | `array` with `items: {type: string}` |
| `dict` | `object` |
| `Optional[X]` | type `X` (nullable) |
| `Union[X, Y]` | `anyOf: [{type: X}, {type: Y}]` |

## Required vs. Optional Parameters

Parameters with no default value are listed in `required`. Parameters with a default value are optional:

```python
@tool
def search(query: str, max_results: int = 10) -> list:
    """Search the database.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
    """
    ...

# Generates:
# required: ["query"]
# properties: {"query": {"type": "string"}, "max_results": {"type": "integer"}}
```

## Using a Tool in an Agent

```python
from django_ai_sdk.agents.base import Agent

class SearchAgent(Agent):
    tools = [search]
```

## Inspecting the Generated Schema

```python
import json
print(json.dumps(search.__tool_schema__, indent=2))
```

Output:
```json
{
  "type": "function",
  "function": {
    "name": "search",
    "description": "Search the database.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query string."
        },
        "max_results": {
          "type": "integer",
          "description": "Maximum number of results to return."
        }
      },
      "required": ["query"]
    }
  }
}
```

## Async Tools

Async tool functions are fully supported:

```python
import httpx

@tool
async def fetch_page(url: str) -> str:
    """Fetch the content of a web page.

    Args:
        url: The URL to fetch.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```
