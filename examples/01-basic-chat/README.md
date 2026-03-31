# 01 — Basic Chat

A minimal Django chat app with real-time SSE streaming using `djangosdk`.

## What it demonstrates

- `Agent` class with a custom `system_prompt`
- `agent.astream()` for async token streaming
- `StreamingHttpResponse` with `text/event-stream`
- Vanilla JS EventSource-style polling (no HTMX dependency for streaming)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## Key files

| File | Purpose |
|------|---------|
| `chat/agents.py` | `ChatAgent` with system prompt |
| `chat/views.py` | Streaming view using `astream()` |
| `chat/templates/chat/index.html` | Chat UI with plain JS SSE reader |
| `config/settings.py` | `AI_SDK` settings block |

## Switching providers

Edit `config/settings.py`:

```python
AI_SDK = {
    "DEFAULT_PROVIDER": "anthropic",
    "DEFAULT_MODEL": "claude-3-5-haiku-20241022",
    "PROVIDERS": {
        "anthropic": {"api_key": "sk-ant-..."},
    },
}
```

No other code changes needed.
