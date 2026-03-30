from __future__ import annotations

import inspect
from typing import Any, Callable, get_type_hints

_PYTHON_TO_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "NoneType": "null",
}


def _python_type_to_json_schema(annotation) -> dict:
    """Convert a Python type annotation to a JSON schema fragment."""
    import typing

    origin = getattr(annotation, "__origin__", None)

    if annotation is inspect.Parameter.empty or annotation is type(None):
        return {"type": "null"}

    if origin is list:
        args = getattr(annotation, "__args__", None)
        if args:
            return {"type": "array", "items": _python_type_to_json_schema(args[0])}
        return {"type": "array"}

    if origin is dict:
        return {"type": "object"}

    if origin is typing.Union:
        args = [a for a in annotation.__args__ if a is not type(None)]
        if len(args) == 1:
            return _python_type_to_json_schema(args[0])
        return {"anyOf": [_python_type_to_json_schema(a) for a in args]}

    if hasattr(annotation, "__mro__"):
        name = annotation.__name__
        json_type = _PYTHON_TO_JSON_TYPE.get(name)
        if json_type:
            return {"type": json_type}

    type_name = getattr(annotation, "__name__", str(annotation))
    json_type = _PYTHON_TO_JSON_TYPE.get(type_name, "string")
    return {"type": json_type}


def _build_tool_schema(fn: Callable) -> dict:
    """Build an OpenAI-compatible function schema from a function's signature and docstring."""
    sig = inspect.signature(fn)
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    doc = inspect.getdoc(fn) or ""
    description = doc.split("\n\n")[0].strip() if doc else fn.__name__

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        annotation = hints.get(param_name, inspect.Parameter.empty)
        prop = _python_type_to_json_schema(annotation)

        # Extract parameter description from docstring (Args: section)
        param_doc = _extract_param_doc(doc, param_name)
        if param_doc:
            prop["description"] = param_doc

        properties[param_name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _extract_param_doc(docstring: str, param_name: str) -> str:
    """Extract parameter description from a Google-style docstring."""
    lines = docstring.splitlines()
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower() in ("args:", "arguments:", "parameters:"):
            in_args = True
            continue
        if in_args:
            if stripped and not stripped.endswith(":") and ":" in stripped:
                name, _, desc = stripped.partition(":")
                if name.strip() == param_name:
                    return desc.strip()
            elif stripped.endswith(":") and not stripped.startswith(" "):
                in_args = False
    return ""


def tool(fn: Callable) -> Callable:
    """
    Decorator that marks a function as an AI tool.

    The function's docstring becomes the tool description.
    Type annotations are used to generate the JSON schema.

    Example::

        @tool
        def get_weather(city: str, unit: str = "celsius") -> dict:
            \"\"\"Get the current weather for a city.

            Args:
                city: The city name to get weather for.
                unit: Temperature unit (celsius or fahrenheit).
            \"\"\"
            ...
    """
    schema = _build_tool_schema(fn)
    fn.__tool__ = True  # type: ignore[attr-defined]
    fn.__tool_schema__ = schema  # type: ignore[attr-defined]
    return fn
