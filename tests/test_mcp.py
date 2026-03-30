"""Tests for MCP client, server, transport and decorators."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch


# ===========================================================================
# Transport tests
# ===========================================================================

class TestMCPTransportConfig:
    def test_http_from_dict(self):
        from djangosdk.mcp.transport import MCPTransportConfig, TransportType
        cfg = MCPTransportConfig.from_dict({"url": "https://mcp.example.com", "transport": "http"})
        assert cfg.type == TransportType.HTTP
        assert cfg.url == "https://mcp.example.com"

    def test_stdio_from_dict(self):
        from djangosdk.mcp.transport import MCPTransportConfig, TransportType
        cfg = MCPTransportConfig.from_dict({"command": "npx", "args": ["-y", "@mcp/server"]})
        assert cfg.type == TransportType.STDIO
        assert cfg.command == "npx"
        assert cfg.args == ["-y", "@mcp/server"]

    def test_default_transport_is_http(self):
        from djangosdk.mcp.transport import MCPTransportConfig, TransportType
        cfg = MCPTransportConfig.from_dict({"url": "https://mcp.example.com"})
        assert cfg.type == TransportType.HTTP


class TestHttpTransport:
    def _send(self, payload: dict) -> dict:
        from djangosdk.mcp.transport import HttpTransport, MCPTransportConfig, TransportType
        cfg = MCPTransportConfig(type=TransportType.HTTP, url="https://mcp.example.com")
        transport = HttpTransport(cfg)

        response_data = {"jsonrpc": "2.0", "id": "1", "result": payload}

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            return transport.send({"jsonrpc": "2.0", "id": "1", "method": "test", "params": {}})

    def test_send_returns_parsed_json(self):
        result = self._send({"tools": []})
        assert result == {"jsonrpc": "2.0", "id": "1", "result": {"tools": []}}

    def test_send_raises_on_network_error(self):
        from djangosdk.mcp.transport import HttpTransport, MCPTransportConfig, TransportType
        cfg = MCPTransportConfig(type=TransportType.HTTP, url="https://mcp.example.com")
        transport = HttpTransport(cfg)
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with pytest.raises(RuntimeError, match="MCP HTTP transport error"):
                transport.send({"method": "test", "params": {}})


class TestStdioTransport:
    def test_send_writes_and_reads_process(self):
        from djangosdk.mcp.transport import StdioTransport, MCPTransportConfig, TransportType

        cfg = MCPTransportConfig(type=TransportType.STDIO, command="echo", args=[])
        transport = StdioTransport(cfg)

        response_data = {"jsonrpc": "2.0", "id": "1", "result": {"ok": True}}

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout.readline.return_value = json.dumps(response_data) + "\n"

        with patch("subprocess.Popen", return_value=mock_proc):
            result = transport.send({"jsonrpc": "2.0", "id": "1", "method": "ping", "params": {}})

        assert result["result"]["ok"] is True
        mock_proc.stdin.write.assert_called_once()
        mock_proc.stdin.flush.assert_called_once()

    def test_stop_terminates_process(self):
        from djangosdk.mcp.transport import StdioTransport, MCPTransportConfig, TransportType
        cfg = MCPTransportConfig(type=TransportType.STDIO, command="echo")
        transport = StdioTransport(cfg)

        mock_proc = MagicMock()
        transport._process = mock_proc

        transport.stop()
        mock_proc.terminate.assert_called_once()
        assert transport._process is None


# ===========================================================================
# MCPClient tests
# ===========================================================================

class TestMCPClient:
    def _make_client_with_mock(self, responses: list[dict]):
        """Build an MCPClient whose transport is mocked to return `responses` in order."""
        from djangosdk.mcp.client import MCPClient
        from djangosdk.mcp.transport import MCPTransportConfig, TransportType

        cfg = MCPTransportConfig(type=TransportType.HTTP, url="https://mcp.test")
        client = MCPClient(cfg)

        call_count = [0]

        def _mock_send(message):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(responses):
                return responses[idx]
            return {"jsonrpc": "2.0", "id": "x", "result": {}}

        client._transport.send = _mock_send
        return client

    def test_initialize_sets_flag(self):
        client = self._make_client_with_mock([
            {"jsonrpc": "2.0", "id": "1", "result": {"protocolVersion": "2025-03-26"}},
        ])
        assert not client._initialized
        client.initialize()
        assert client._initialized

    def test_list_tools_returns_tools(self):
        client = self._make_client_with_mock([
            # initialize
            {"jsonrpc": "2.0", "id": "1", "result": {"protocolVersion": "2025-03-26"}},
            # tools/list
            {"jsonrpc": "2.0", "id": "2", "result": {
                "tools": [{"name": "search", "description": "Search the web", "inputSchema": {}}]
            }},
        ])
        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "search"

    def test_call_tool_extracts_text_content(self):
        client = self._make_client_with_mock([
            # initialize
            {"jsonrpc": "2.0", "id": "1", "result": {}},
            # tools/call
            {"jsonrpc": "2.0", "id": "2", "result": {
                "content": [{"type": "text", "text": "Found 5 results."}]
            }},
        ])
        result = client.call_tool("search", {"query": "Django"})
        assert result == "Found 5 results."

    def test_call_tool_joins_multiple_text_blocks(self):
        client = self._make_client_with_mock([
            {"jsonrpc": "2.0", "id": "1", "result": {}},
            {"jsonrpc": "2.0", "id": "2", "result": {
                "content": [
                    {"type": "text", "text": "Part 1."},
                    {"type": "text", "text": "Part 2."},
                ]
            }},
        ])
        result = client.call_tool("multi", {})
        assert "Part 1." in result
        assert "Part 2." in result

    def test_rpc_raises_on_error_response(self):
        client = self._make_client_with_mock([
            {"jsonrpc": "2.0", "id": "1", "error": {"code": -32600, "message": "Invalid request"}},
        ])
        client._initialized = True
        with pytest.raises(RuntimeError, match="MCP error"):
            client._rpc("tools/list")

    def test_to_tool_schemas_converts_to_openai_format(self):
        client = self._make_client_with_mock([
            {"jsonrpc": "2.0", "id": "1", "result": {}},
            {"jsonrpc": "2.0", "id": "2", "result": {
                "tools": [{
                    "name": "lookup",
                    "description": "Look something up",
                    "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}},
                }]
            }},
        ])
        schemas = client.to_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "lookup"

    def test_from_dict_http(self):
        from djangosdk.mcp.client import MCPClient
        client = MCPClient.from_dict({"url": "https://mcp.example.com", "transport": "http"})
        assert client is not None


# ===========================================================================
# MCPServer tests
# ===========================================================================

class TestMCPServer:
    def _call(self, method: str, params: dict = None) -> dict:
        from djangosdk.mcp.server import MCPServer
        server = MCPServer()
        return server.handle({
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": method,
            "params": params or {},
        })

    def test_initialize_returns_protocol_version(self):
        result = self._call("initialize")
        assert result["result"]["protocolVersion"] == "2025-03-26"
        assert "tools" in result["result"]["capabilities"]

    def test_tools_list_returns_registered_tools(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool

        @mcp_tool
        def my_tool(query: str) -> str:
            """Search for something."""
            return f"Results for {query}"

        result = self._call("tools/list")
        tool_names = [t["name"] for t in result["result"]["tools"]]
        assert "my_tool" in tool_names

    def test_tools_call_executes_function(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool

        @mcp_tool
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        result = self._call("tools/call", {"name": "greet", "arguments": {"name": "Alice"}})
        assert "Hello, Alice!" in result["result"]["content"][0]["text"]

    def test_tools_call_unknown_tool_returns_error(self):
        result = self._call("tools/call", {"name": "nonexistent", "arguments": {}})
        assert "error" in result

    def test_resources_list(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_resource

        @mcp_resource("file:///test.txt", name="Test File")
        def get_test():
            return "test content"

        result = self._call("resources/list")
        uris = [r["uri"] for r in result["result"]["resources"]]
        assert "file:///test.txt" in uris

    def test_resources_read(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_resource

        @mcp_resource("file:///data.json")
        def get_data():
            return {"key": "value"}

        result = self._call("resources/read", {"uri": "file:///data.json"})
        assert result["result"]["contents"][0]["uri"] == "file:///data.json"

    def test_unknown_method_returns_error(self):
        result = self._call("unknown/method")
        assert "error" in result
        assert result["error"]["code"] == -32601


# ===========================================================================
# MCPServerView tests
# ===========================================================================

class TestMCPServerView:
    def _post(self, body: dict):
        from django.test import RequestFactory
        from djangosdk.mcp.server import MCPServerView

        factory = RequestFactory()
        request = factory.post(
            "/mcp/",
            data=json.dumps(body),
            content_type="application/json",
        )
        view = MCPServerView()
        return view.post(request)

    def test_initialize_via_http(self):
        resp = self._post({"jsonrpc": "2.0", "id": "1", "method": "initialize", "params": {}})
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["result"]["protocolVersion"] == "2025-03-26"

    def test_invalid_json_returns_400(self):
        from django.test import RequestFactory
        from djangosdk.mcp.server import MCPServerView

        factory = RequestFactory()
        request = factory.post("/mcp/", data=b"not-json", content_type="application/json")
        view = MCPServerView()
        resp = view.post(request)
        assert resp.status_code == 400


# ===========================================================================
# Decorators tests
# ===========================================================================

class TestMCPDecorators:
    def test_mcp_tool_registers_function(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool, get_registered_tools

        @mcp_tool
        def my_func(query: str, limit: int = 10) -> list:
            """Search for items."""
            return []

        tools = get_registered_tools()
        assert "my_func" in tools
        assert tools["my_func"]["description"] == "Search for items."

    def test_mcp_tool_generates_schema(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool, get_registered_tools

        @mcp_tool
        def typed_tool(name: str, count: int) -> str:
            """A typed tool."""
            return name

        schema = get_registered_tools()["typed_tool"]["inputSchema"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert "name" in schema["required"]
        assert "count" in schema["required"]

    def test_mcp_tool_with_custom_name(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool, get_registered_tools

        @mcp_tool(name="custom_name", description="A custom tool")
        def my_fn(x: str) -> str:
            return x

        tools = get_registered_tools()
        assert "custom_name" in tools
        assert tools["custom_name"]["description"] == "A custom tool"

    def test_mcp_tool_callable_after_decoration(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_tool

        @mcp_tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert add(2, 3) == 5

    def test_mcp_resource_registers(self, reset_mcp_registry):
        from djangosdk.mcp.decorators import mcp_resource, get_registered_resources

        @mcp_resource("file:///catalog.json", name="Catalog", mime_type="application/json")
        def get_catalog() -> dict:
            return {}

        resources = get_registered_resources()
        assert "file:///catalog.json" in resources
        assert resources["file:///catalog.json"]["mimeType"] == "application/json"
