from __future__ import annotations

from typing import Any

from django_ai_sdk.tools.registry import ToolRegistry


class HasTools:
    """
    Mixin that adds tool-calling capability to an Agent.

    Declare tools on the class as a list of @tool-decorated functions or BaseTool instances.

    Example::

        class SupportAgent(Agent):
            tools = [lookup_order, cancel_order]
    """

    tools: list = []
    max_tool_iterations: int = 10

    def _get_tool_registry(self) -> ToolRegistry:
        """Build and cache the tool registry for this agent instance."""
        if not hasattr(self, "_tool_registry"):
            self._tool_registry = ToolRegistry()
            for t in (self.__class__.tools or []):
                self._tool_registry.register(t)
        return self._tool_registry

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        return self._get_tool_registry().get_schemas()

    def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute tool calls and return tool result messages."""
        registry = self._get_tool_registry()
        results = []
        for tc in tool_calls:
            try:
                result = registry.execute(tc["name"], tc.get("arguments", {}))
                content = str(result)
            except Exception as exc:
                content = f"Error: {exc}"
            results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "name": tc["name"],
                "content": content,
            })
        return results

    async def _aexecute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Async version of tool execution."""
        registry = self._get_tool_registry()
        results = []
        for tc in tool_calls:
            try:
                result = await registry.aexecute(tc["name"], tc.get("arguments", {}))
                content = str(result)
            except Exception as exc:
                content = f"Error: {exc}"
            results.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "name": tc["name"],
                "content": content,
            })
        return results
