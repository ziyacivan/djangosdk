# MCP Support

`django-ai-sdk` supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — the emerging standard for connecting AI agents to external tools and data sources.

## Overview

MCP allows AI agents to:
- Call tools hosted on remote MCP servers
- Access resources (files, databases, APIs) via a standardized protocol
- Expose Django endpoints as MCP servers for other agents to use

## Connecting to MCP Servers

Add `mcp_servers` to your agent class. Each entry is a connection config:

```python
class ResearchAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    mcp_servers = [
        # HTTP MCP server
        {
            "url": "https://mcp.example.com/server",
            "transport": "http",
        },
        # Local MCP server via stdio
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        },
    ]
```

When the agent handles a request, it automatically:
1. Fetches tool schemas from all configured MCP servers
2. Includes them alongside the agent's own tools
3. Routes tool calls to the correct MCP server

## Exposing a Django App as an MCP Server

Use `@mcp_tool` and `@mcp_resource` decorators to expose Django functionality via MCP:

```python
from django_ai_sdk.mcp.decorators import mcp_tool, mcp_resource

@mcp_tool
def query_database(sql: str) -> list:
    """Execute a read-only SQL query against the Django database.

    Args:
        sql: The SQL query to execute.
    """
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()

@mcp_resource(uri="myapp://products")
def list_products():
    """Return all active products."""
    from myapp.models import Product
    return list(Product.objects.filter(active=True).values())
```

Mount the MCP server in your URL configuration:

```python
from django.urls import path
from django_ai_sdk.mcp.server import mcp_server_view

urlpatterns = [
    path("mcp/", mcp_server_view),
]
```

## MCP Transport

`django-ai-sdk` supports two MCP transport types:

| Transport | Use case |
|---|---|
| `http` | Remote MCP servers over HTTPS |
| `stdio` | Local MCP servers launched as subprocesses |

## Error Handling

MCP tool failures are non-fatal by default. If an MCP server is unreachable or returns an error, the failure is silently logged and the agent continues without that server's tools.

To make MCP failures fatal:

```python
AI_SDK = {
    "MCP": {
        "FAIL_SILENTLY": False,
    },
}
```
