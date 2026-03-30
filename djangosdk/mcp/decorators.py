from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

# Registry of MCP tools and resources exposed by this Django app
_mcp_tools: dict[str, dict] = {}
_mcp_resources: dict[str, dict] = {}


def mcp_tool(func: Callable | None = None, *, name: str | None = None, description: str | None = None):
    """
    Decorator that registers a function as an MCP tool.

    The function's docstring becomes the tool description; type annotations
    generate the JSON input schema (same strategy as the ``@tool`` decorator).

    Example::

        @mcp_tool
        def search_products(query: str, max_results: int = 5) -> list[dict]:
            \"\"\"Searches the product catalog.\"\"\"
            return list(Product.objects.filter(name__icontains=query).values()[:max_results])
    """

    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        tool_description = description or (fn.__doc__ or "").strip()
        schema = _build_input_schema(fn)

        _mcp_tools[tool_name] = {
            "name": tool_name,
            "description": tool_description,
            "inputSchema": schema,
            "fn": fn,
        }

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.__mcp_tool__ = tool_name
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def mcp_resource(
    uri: str, *, name: str | None = None, description: str | None = None, mime_type: str = "text/plain"
):
    """
    Decorator that registers a function as an MCP resource.

    Example::

        @mcp_resource("file:///products/catalog", description="Product catalog")
        def get_catalog() -> str:
            return Product.objects.all().values_list("name", flat=True)
    """

    def decorator(fn: Callable) -> Callable:
        resource_name = name or fn.__name__
        _mcp_resources[uri] = {
            "uri": uri,
            "name": resource_name,
            "description": description or (fn.__doc__ or "").strip(),
            "mimeType": mime_type,
            "fn": fn,
        }

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.__mcp_resource__ = uri
        return wrapper

    return decorator


def _build_input_schema(fn: Callable) -> dict:
    """Build a minimal JSON Schema from function type annotations."""
    import typing

    sig = inspect.signature(fn)
    try:
        hints = typing.get_type_hints(fn)
    except Exception:
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    _type_map: dict[Any, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        annotation = hints.get(param_name, inspect.Parameter.empty)
        json_type = _type_map.get(annotation, "string")
        properties[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def get_registered_tools() -> dict[str, dict]:
    return dict(_mcp_tools)


def get_registered_resources() -> dict[str, dict]:
    return dict(_mcp_resources)
