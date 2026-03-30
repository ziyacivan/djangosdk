# Streaming

`django-ai-sdk` supports streaming via Server-Sent Events (SSE). Both synchronous (WSGI) and asynchronous (ASGI) streaming are supported.

## StreamChunk

Each chunk emitted during streaming is a `StreamChunk`:

```python
@dataclass
class StreamChunk:
    type: str    # "text_delta" | "thinking_delta" | "tool_call" | "done"
    text: str = ""
    thinking: bool = False
    tool_call: dict | None = None
    usage: UsageInfo | None = None
```

- `text_delta` — A piece of the final response text
- `thinking_delta` — A piece of the reasoning trace (requires `stream_thinking=True`)
- `tool_call` — A tool call event
- `done` — The final chunk, contains `usage` info

## Sync Streaming (WSGI)

Use `agent.stream()` in a standard Django view:

```python
from djangosdk.agents.base import Agent

class AssistantAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"

def chat_stream(request):
    agent = AssistantAgent()
    return agent.stream(request.GET.get("prompt", ""))
```

This returns a `StreamingHttpResponse` with `Content-Type: text/event-stream`.

## Async Streaming (ASGI)

Use `agent.astream()` in an async view:

```python
from django.http import StreamingHttpResponse
from djangosdk.agents.base import Agent
from djangosdk.streaming.async_sse import AsyncSSEResponse

class AssistantAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"

async def chat_stream_async(request):
    agent = AssistantAgent()
    prompt = request.GET.get("prompt", "")

    async def generate():
        async for chunk in agent.astream(prompt):
            if chunk.type == "text_delta":
                yield chunk.text

    return AsyncSSEResponse(generate())
```

## SSE Format

Each SSE message follows the standard format:

```
data: {"type": "text_delta", "text": "Hello"}

data: {"type": "text_delta", "text": ", world!"}

data: {"type": "done", "usage": {"total_tokens": 42}}

```

## JavaScript Client Example

```javascript
const evtSource = new EventSource("/api/chat/stream/?prompt=Hello");

evtSource.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  if (chunk.type === "text_delta") {
    document.getElementById("output").textContent += chunk.text;
  }
  if (chunk.type === "done") {
    evtSource.close();
  }
};
```

## Configuration

```python
AI_SDK = {
    "STREAMING": {
        "CHUNK_SEPARATOR": "\n\n",    # SSE event separator
        "SSE_RETRY_MS": 3000,          # Reconnection delay hint
        "STREAM_THINKING": False,       # Emit thinking_delta chunks
    },
}
```
