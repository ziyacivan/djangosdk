---
name: wire-chat-view
description: >
  Scaffolds the full DRF integration to expose an Agent over HTTP using
  ChatAPIView (sync) or StreamingChatAPIView (SSE streaming). Invoke when
  the user says "wire up a chat endpoint", "expose my agent over HTTP",
  "add a chat API view", "set up ChatAPIView", "add a streaming endpoint",
  "hook up the DRF view", or "create a Django view for my agent".
triggers:
  - wire up a chat endpoint
  - expose my agent over HTTP
  - add a chat API view
  - set up ChatAPIView
  - add a streaming endpoint
  - hook up the DRF view
  - create a Django view for my agent
  - wire a view to my agent
  - add a streaming view
  - create a REST endpoint for my agent
---

# Wire an Agent to a DRF Chat Endpoint

You are wiring a `django-ai-sdk` Agent to an HTTP endpoint using Django REST Framework.

## Step 1 — Decide: Regular or Streaming?

| Use case | View class |
|---|---|
| Single-turn or multi-turn, response waits | `ChatAPIView` |
| Real-time token streaming (WSGI or ASGI) | `StreamingChatAPIView` |

Both views accept `POST` with a JSON body `{"prompt": "...", "conversation_id": "..."}`.

## Step 2 — Subclass the View

Place the view in your app (e.g., `myapp/views.py`):

```python
# myapp/views.py
from djangosdk.views.chat import ChatAPIView
from myapp.agents import SupportAgent


class SupportChatView(ChatAPIView):
    agent_class = SupportAgent
```

For streaming:

```python
from djangosdk.views.streaming import StreamingChatAPIView
from myapp.agents import SupportAgent


class StreamingSupportView(StreamingChatAPIView):
    agent_class = SupportAgent
```

## Step 3 — Register URLs

```python
# myapp/urls.py
from django.urls import path
from myapp.views import SupportChatView, StreamingSupportView

urlpatterns = [
    path("chat/", SupportChatView.as_view(), name="chat"),
    path("chat/stream/", StreamingSupportView.as_view(), name="chat-stream"),
]
```

Include in the project `urls.py`:

```python
# project/urls.py
from django.urls import include, path

urlpatterns = [
    path("api/", include("myapp.urls")),
]
```

## Step 4 — Request / Response Contract

### `POST /api/chat/`

**Request body:**
```json
{
  "prompt": "What is the return policy?",
  "conversation_id": "conv-abc123"   // optional — omit for single-turn
}
```

**Response:**
```json
{
  "text": "Our return policy allows returns within 30 days.",
  "conversation_id": "conv-abc123",
  "thinking": null,
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 22,
    "cache_read_tokens": 0,
    "cache_write_tokens": 0,
    "total_tokens": 67
  }
}
```

### `POST /api/chat/stream/`

Returns `text/event-stream` (SSE). Each chunk:
```
data: {"chunk": "Our return ", "done": false}
data: {"chunk": "policy...", "done": false}
data: {"chunk": "", "done": true}
```

## Step 5 — Add Authentication / Permissions (optional)

Override `get_agent()` to inject request context:

```python
from rest_framework.permissions import IsAuthenticated
from djangosdk.views.chat import ChatAPIView
from myapp.agents import SupportAgent


class SupportChatView(ChatAPIView):
    agent_class = SupportAgent
    permission_classes = [IsAuthenticated]

    def get_agent(self, request):
        agent = SupportAgent()
        # Inject user context into the system prompt at runtime
        agent.system_prompt = (
            f"You are a support agent helping {request.user.get_full_name()}. "
            + agent.system_prompt
        )
        return agent
```

## Step 6 — Multi-Turn Conversations

When `conversation_id` is passed, the SDK calls `agent.with_conversation(conversation_id)`, which enables `EpisodicMemory` backed by Django ORM (`Conversation` + `Message` models).

The response always echoes back the `conversation_id` so the client can reuse it in subsequent requests.

**Prerequisites:** `djangosdk` must be in `INSTALLED_APPS` and migrations run:
```bash
python manage.py migrate djangosdk
```

## Step 7 — ASGI Streaming (async)

For async streaming you need ASGI (Daphne, Uvicorn, or Granian). In `asgi.py`:

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
application = get_asgi_application()
```

`StreamingChatAPIView` uses `AsyncSSEResponse` automatically when the agent's `astream()` is called. No extra configuration needed.

## Step 8 — Test the View

```python
import pytest
from django.test import RequestFactory
from rest_framework.test import APIClient
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import SupportAgent
from myapp.views import SupportChatView


@pytest.fixture
def fake_provider(monkeypatch):
    fp = FakeProvider()
    fp.set_response("Our return policy allows returns within 30 days.")
    monkeypatch.setattr(SupportAgent, "_provider_class", lambda self: fp)
    return fp


def test_chat_view_returns_text(fake_provider, rf):
    request = rf.post(
        "/chat/",
        data={"prompt": "What is the return policy?"},
        content_type="application/json",
    )
    view = SupportChatView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert "return policy" in response.data["text"]
```
