from __future__ import annotations

import inspect
from typing import Any, Callable

from django_ai_sdk.exceptions import ToolError
from django_ai_sdk.tools.base import BaseTool
from django_ai_sdk.tools.decorator import _build_tool_schema


class ToolRegistry:
    """Per-agent registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._schemas: dict[str, dict] = {}

    def register(self, fn_or_tool: Callable | BaseTool) -> None:
        if isinstance(fn_or_tool, BaseTool):
            self._tools[fn_or_tool.name] = fn_or_tool
            self._schemas[fn_or_tool.name] = fn_or_tool.to_schema()
        elif callable(fn_or_tool):
            schema = getattr(fn_or_tool, "__tool_schema__", None) or _build_tool_schema(fn_or_tool)
            name = schema["function"]["name"]
            self._tools[name] = fn_or_tool
            self._schemas[name] = schema
        else:
            raise ToolError(f"Cannot register {fn_or_tool!r}: not a callable or BaseTool")

    def get_schemas(self) -> list[dict]:
        return list(self._schemas.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ToolError(f"Tool '{name}' not found in registry", tool_name=name)
        fn = self._tools[name]
        try:
            return fn(**arguments)
        except Exception as exc:
            raise ToolError(f"Tool '{name}' raised {type(exc).__name__}: {exc}", tool_name=name) from exc

    async def aexecute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ToolError(f"Tool '{name}' not found in registry", tool_name=name)
        fn = self._tools[name]
        try:
            if inspect.iscoroutinefunction(fn):
                return await fn(**arguments)
            return fn(**arguments)
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError(f"Tool '{name}' raised {type(exc).__name__}: {exc}", tool_name=name) from exc

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
