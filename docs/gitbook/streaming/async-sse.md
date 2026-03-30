# Async SSE (ASGI)

`AsyncSSEResponse` wraps an async generator and streams it as SSE. Use this in Django async views with an ASGI server such as Daphne or Uvicorn.

## Usage

```python
from django_ai_sdk.streaming.async_sse import AsyncSSEResponse
from django_ai_sdk.agents.base import Agent

class AssistantAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"

async def stream_view(request):
    agent = AssistantAgent()
    prompt = request.GET.get("prompt", "")

    async def generate():
        async for chunk in agent.astream(prompt):
            yield chunk

    return AsyncSSEResponse(generate())
```

## ASGI Setup

Ensure your Django project is configured with an ASGI server:

```python
# asgi.py
from django.core.asgi import get_asgi_application
application = get_asgi_application()
```

Run with:
```bash
uvicorn myproject.asgi:application --host 0.0.0.0 --port 8000
```
or:
```bash
daphne myproject.asgi:application
```

## Thinking Content in Streams

To stream reasoning/thinking content alongside the response, set `stream_thinking=True` in `AI_SDK.STREAMING` and use a reasoning model:

```python
AI_SDK = {
    "STREAMING": {"STREAM_THINKING": True},
}

class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(extended_thinking=True, thinking_budget=10000, stream_thinking=True)
```

Chunks with `type == "thinking_delta"` will arrive before the final `text_delta` chunks.
