# Promptable

`Promptable` is the core mixin. It provides `handle()`, `ahandle()`, `stream()`, and `astream()`, and runs the tool-call loop.

## Methods

### `handle(prompt: str, **kwargs) -> AgentResponse`

Synchronous, blocking completion. Fires `agent_started` and `agent_completed` signals.

```python
response = agent.handle("Summarize this article.")
```

### `ahandle(prompt: str, **kwargs) -> AgentResponse`

Async version. Use inside Django async views or with `asyncio`.

```python
response = await agent.ahandle("Summarize this article.")
```

### `stream(prompt: str, **kwargs) -> StreamingHttpResponse`

Synchronous streaming. Returns a Django `StreamingHttpResponse` emitting SSE chunks. Return this directly from a Django view.

```python
def my_view(request):
    return agent.stream(request.GET.get("prompt", ""))
```

### `astream(prompt: str, **kwargs) -> AsyncGenerator[StreamChunk, None]`

Async streaming generator. Use in async views to yield chunks.

```python
async def my_async_view(request):
    async for chunk in agent.astream("Tell me a story."):
        # chunk.type: "text_delta" | "thinking_delta" | "done"
        # chunk.text: str
        pass
```

## Tool Loop

When the model returns `tool_calls`, `Promptable` runs the dispatch loop:

1. Build `AgentRequest` with tool schemas
2. Call provider — get response
3. If `response.tool_calls` is non-empty: execute tools, append results to messages, repeat
4. Stop when no tool calls are returned, or `max_tool_iterations` is reached

The loop runs up to `max_tool_iterations` times (default: 10).

## Internal Method: `_build_request`

Assembles an `AgentRequest` by combining:
- Agent class attributes (`model`, `provider`, `system_prompt`, `temperature`, `max_tokens`)
- Conversation history from `Conversational._load_conversation_messages()`
- Tool schemas from `HasTools._get_tool_schemas()`
- Output schema from `HasStructuredOutput._get_output_json_schema()`
- MCP tool schemas from configured `mcp_servers`
