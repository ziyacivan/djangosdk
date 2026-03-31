# Basic Chat

**Source:** [`examples/01-basic-chat/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/01-basic-chat)

A minimal Django chat app with real-time token streaming over SSE (Server-Sent Events).

## What it demonstrates

- Defining an `Agent` subclass with a custom `system_prompt`
- Streaming responses token-by-token with `agent.astream()`
- Returning a `StreamingHttpResponse` with `content_type="text/event-stream"`
- Reading the SSE stream in plain JavaScript (no framework required)

## Setup

```bash
cd examples/01-basic-chat
pip install djangosdk python-decouple whitenoise
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

**`chat/agents.py`** — one class, one attribute:

```python
from djangosdk.agents import Agent

class ChatAgent(Agent):
    system_prompt = (
        "You are a helpful assistant. Be concise and friendly."
    )
```

**`chat/views.py`** — async streaming view:

```python
from django.http import StreamingHttpResponse
from .agents import ChatAgent

async def stream(request):
    agent = ChatAgent()
    prompt = request.POST.get("message", "")

    async def event_generator():
        async for chunk in agent.astream(prompt):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

## Switching Providers

Change two lines in `config/settings.py` — no other code changes:

```python
AI_SDK = {
    "DEFAULT_PROVIDER": "anthropic",
    "DEFAULT_MODEL": "claude-3-5-haiku-20241022",
    "PROVIDERS": {
        "anthropic": {"api_key": env("ANTHROPIC_API_KEY")},
    },
}
```
