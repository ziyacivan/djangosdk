from __future__ import annotations

import json
from typing import Any

from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from django_ai_sdk.mcp.decorators import get_registered_resources, get_registered_tools

MCP_PROTOCOL_VERSION = "2025-03-26"


class MCPServerView(View):
    """
    Django class-based view that exposes registered MCP tools as an MCP server.

    Mount it in ``urls.py``::

        from django_ai_sdk.mcp.server import MCPServerView

        urlpatterns = [
            path("mcp/", MCPServerView.as_view()),
        ]

    Then agents (or external MCP clients) can connect to ``/mcp/`` and invoke
    your ``@mcp_tool``-decorated functions.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None},
                status=400,
            )

        method = body.get("method", "")
        params = body.get("params", {})
        req_id = body.get("id")

        handler = getattr(self, f"_handle_{method.replace('/', '_')}", None)
        if handler is None:
            return self._error(req_id, -32601, f"Method not found: {method}")

        try:
            result = handler(params)
            return JsonResponse({"jsonrpc": "2.0", "id": req_id, "result": result})
        except Exception as exc:
            return self._error(req_id, -32603, str(exc))

    # ------------------------------------------------------------------ handlers

    def _handle_initialize(self, params: dict) -> dict:
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "django-ai-sdk", "version": "2.0"},
        }

    def _handle_tools_list(self, params: dict) -> dict:
        tools = get_registered_tools()
        return {
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                }
                for t in tools.values()
            ]
        }

    def _handle_tools_call(self, params: dict) -> dict:
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        tools = get_registered_tools()

        if name not in tools:
            raise ValueError(f"Unknown tool: {name}")

        fn = tools[name]["fn"]
        result = fn(**arguments)
        return {
            "content": [{"type": "text", "text": json.dumps(result) if not isinstance(result, str) else result}]
        }

    def _handle_resources_list(self, params: dict) -> dict:
        resources = get_registered_resources()
        return {
            "resources": [
                {
                    "uri": r["uri"],
                    "name": r["name"],
                    "description": r["description"],
                    "mimeType": r["mimeType"],
                }
                for r in resources.values()
            ]
        }

    def _handle_resources_read(self, params: dict) -> dict:
        uri = params.get("uri", "")
        resources = get_registered_resources()

        if uri not in resources:
            raise ValueError(f"Unknown resource: {uri}")

        fn = resources[uri]["fn"]
        content = fn()
        mime = resources[uri]["mimeType"]
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": mime,
                    "text": content if isinstance(content, str) else json.dumps(content),
                }
            ]
        }

    # ------------------------------------------------------------------ helpers

    def _error(self, req_id: Any, code: int, message: str) -> JsonResponse:
        return JsonResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": code, "message": message},
            },
            status=200,
        )


class MCPServer:
    """
    Programmatic interface to the MCP server (for testing or embedding in views).

    For production use, mount ``MCPServerView`` in your URL conf instead.
    """

    def handle(self, message: dict) -> dict:
        view = MCPServerView()
        method = message.get("method", "")
        params = message.get("params", {})
        req_id = message.get("id")

        handler = getattr(view, f"_handle_{method.replace('/', '_')}", None)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(exc)},
            }
