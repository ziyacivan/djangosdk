from __future__ import annotations

import uuid
from typing import Any

from djangosdk.mcp.transport import MCPTransportConfig, build_transport


class MCPClient:
    """
    Connects to an external MCP server and exposes its tools to an Agent.

    The client speaks JSON-RPC 2.0 over the configured transport (HTTP or STDIO).

    Example::

        client = MCPClient.from_dict({
            "url": "https://mcp.example.com",
            "transport": "http",
        })
        tools = client.list_tools()
        result = client.call_tool("search", {"query": "Django"})
    """

    def __init__(self, transport_config: MCPTransportConfig) -> None:
        self._config = transport_config
        self._transport = build_transport(transport_config)
        self._initialized = False

    @classmethod
    def from_dict(cls, data: dict) -> "MCPClient":
        return cls(MCPTransportConfig.from_dict(data))

    # ------------------------------------------------------------------ JSON-RPC

    def _rpc(self, method: str, params: dict | None = None) -> Any:
        message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {},
        }
        response = self._transport.send(message)
        if "error" in response:
            raise RuntimeError(
                f"MCP error [{response['error'].get('code')}]: "
                f"{response['error'].get('message')}"
            )
        return response.get("result")

    def initialize(self) -> dict:
        """Send the MCP initialize handshake."""
        result = self._rpc(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "django-ai-sdk", "version": "1.0"},
            },
        )
        self._initialized = True
        return result

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    # ------------------------------------------------------------------ Tools

    def list_tools(self) -> list[dict]:
        """Return the list of tools exposed by the MCP server."""
        self._ensure_initialized()
        result = self._rpc("tools/list")
        return result.get("tools", []) if result else []

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """Execute a tool on the MCP server and return the result."""
        self._ensure_initialized()
        result = self._rpc(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
        )
        if result and "content" in result:
            # Extract text content from MCP ContentBlock list
            texts = [
                block.get("text", "")
                for block in result["content"]
                if block.get("type") == "text"
            ]
            return "\n".join(texts)
        return result

    def to_tool_schemas(self) -> list[dict]:
        """
        Convert MCP tool definitions to the OpenAI function-calling schema format
        used by litellm (and therefore AgentRequest.tools).
        """
        tools = self.list_tools()
        schemas = []
        for tool in tools:
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {}),
                    },
                }
            )
        return schemas
