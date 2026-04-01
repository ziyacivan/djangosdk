---
name: setup-mcp
description: >
  Scaffolds an MCP (Model Context Protocol) server and client using
  djangosdk.mcp. Invoke when the user says "set up MCP", "create an MCP server",
  "connect to an MCP client", "expose tools via MCP", "use MCP decorators",
  "integrate MCP", or "add MCP support".
triggers:
  - set up MCP
  - create an MCP server
  - connect to an MCP client
  - expose tools via MCP
  - use MCP decorators
  - integrate MCP
  - add MCP support
  - MCP server
  - MCP tool
  - mcp_tool decorator
  - mcp_resource decorator
  - Model Context Protocol
---

# Set Up MCP (Model Context Protocol)

You are integrating the Model Context Protocol (2025-03-26 spec) into a `django-ai-sdk` project.

## Overview

| Concept | django-ai-sdk class / decorator |
|---|---|
| MCP Server | `MCPServerView` (Django CBV) |
| MCP Tool | `@mcp_tool` decorator |
| MCP Resource | `@mcp_resource` decorator |
| MCP Client | `MCPClient` |

## Step 1 — Define MCP Tools

Place MCP tool definitions in a dedicated module (e.g., `myapp/mcp_tools.py`). The `@mcp_tool` decorator registers the function in a global registry — auto-discovered when the Django app loads.

```python
# myapp/mcp_tools.py
from djangosdk.mcp.decorators import mcp_tool, mcp_resource


@mcp_tool
def search_products(query: str, max_results: int = 5) -> list[dict]:
    """Search the product catalog by keyword."""
    from myapp.models import Product
    return list(
        Product.objects.filter(name__icontains=query)
        .values("id", "name", "price")[:max_results]
    )


@mcp_tool
def get_order_status(order_id: str) -> dict:
    """Return the current status of an order."""
    from myapp.models import Order
    try:
        order = Order.objects.get(pk=order_id)
        return {"order_id": order_id, "status": order.status, "updated_at": str(order.updated_at)}
    except Order.DoesNotExist:
        return {"error": f"Order {order_id} not found"}
```

## Step 2 — Define MCP Resources

Resources expose read-only data (documents, catalogs, configs) as URIs.

```python
@mcp_resource(
    uri="file:///products/catalog",
    name="Product Catalog",
    description="Full product catalog in JSON format",
    mime_type="application/json",
)
def get_product_catalog() -> str:
    import json
    from myapp.models import Product
    products = list(Product.objects.all().values("id", "name", "description", "price"))
    return json.dumps(products)


@mcp_resource(
    uri="file:///docs/faq",
    name="FAQ Document",
    description="Frequently asked questions",
    mime_type="text/plain",
)
def get_faq() -> str:
    return open("docs/faq.txt").read()
```

## Step 3 — Mount the MCP Server View

```python
# myapp/urls.py
from django.urls import path
from djangosdk.mcp.server import MCPServerView

urlpatterns = [
    path("mcp/", MCPServerView.as_view(), name="mcp-server"),
]
```

Import your MCP tools module in `apps.py` to ensure registration on startup:

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        import myapp.mcp_tools  # noqa: F401 — registers @mcp_tool and @mcp_resource
```

## Step 4 — MCP Protocol Endpoints

The `MCPServerView` handles all MCP JSON-RPC 2.0 methods via `POST /mcp/`:

| Method | What it returns |
|---|---|
| `initialize` | Protocol version + server capabilities |
| `tools/list` | All registered `@mcp_tool` functions with schemas |
| `tools/call` | Executes a tool by name with given arguments |
| `resources/list` | All registered `@mcp_resource` URIs |
| `resources/read` | Executes a resource by URI and returns content |

**Example request:**
```bash
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

## Step 5 — Connect an Agent to an MCP Client

Use `MCPClient` to call tools on a remote MCP server and bridge them into an Agent:

```python
# myapp/agents.py
from djangosdk.agents.base import Agent
from djangosdk.mcp.client import MCPClient
from djangosdk.tools.decorator import tool


# Bridge remote MCP tool into a local @tool function
mcp_client = MCPClient(base_url="https://external-service.example.com/mcp/")


@tool
def search_external_catalog(query: str) -> str:
    """Search the external product catalog via MCP."""
    result = mcp_client.call_tool("search_products", {"query": query, "max_results": 5})
    return str(result)


class ShoppingAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a shopping assistant."
    tools = [search_external_catalog]
```

## Step 6 — Self-Connecting Agent (Same Django App)

An agent can consume its own MCP server using the programmatic `MCPServer` interface (no HTTP needed):

```python
from djangosdk.mcp.server import MCPServer
from djangosdk.tools.decorator import tool


mcp_server = MCPServer()


@tool
def call_local_mcp(tool_name: str, arguments: dict) -> str:
    """Call a locally registered MCP tool."""
    result = mcp_server.handle({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    })
    return str(result.get("result", {}).get("content", [{}])[0].get("text", ""))
```

## Step 7 — Test MCP Tools

```python
import pytest
from djangosdk.mcp.server import MCPServer


def test_mcp_server_lists_registered_tools():
    server = MCPServer()
    response = server.handle({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    })
    tool_names = [t["name"] for t in response["result"]["tools"]]
    assert "search_products" in tool_names


def test_mcp_tool_executes_correctly(db):
    from myapp.models import Product
    Product.objects.create(name="Django Book", price=29.99)

    server = MCPServer()
    response = server.handle({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "search_products", "arguments": {"query": "Django"}},
    })
    content = response["result"]["content"][0]["text"]
    assert "Django Book" in content
```
