# Sync SSE (WSGI)

`SyncSSEResponse` wraps a synchronous streaming generator and returns it as a `StreamingHttpResponse` with the correct SSE headers.

## Usage

`agent.stream()` uses `SyncSSEResponse` internally. You can also use it directly:

```python
from django_ai_sdk.streaming.sse import SyncSSEResponse, format_sse_chunk
from django_ai_sdk.agents.response import StreamChunk

def my_stream_view(request):
    def generate():
        yield StreamChunk(type="text_delta", text="Hello")
        yield StreamChunk(type="text_delta", text=", world!")
        yield StreamChunk(type="done")

    return SyncSSEResponse(generate())
```

## `format_sse_chunk`

Formats a `StreamChunk` into an SSE-compliant string:

```python
from django_ai_sdk.streaming.sse import format_sse_chunk
from django_ai_sdk.agents.response import StreamChunk

chunk = StreamChunk(type="text_delta", text="Hello!")
print(format_sse_chunk(chunk))
# data: {"type": "text_delta", "text": "Hello!"}
#
```

## Headers Set

`SyncSSEResponse` sets the following headers automatically:

| Header | Value |
|---|---|
| `Content-Type` | `text/event-stream` |
| `Cache-Control` | `no-cache` |
| `X-Accel-Buffering` | `no` (disables nginx buffering) |
