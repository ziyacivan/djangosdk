# DRF Views

`django-ai-sdk` provides two pre-built Django REST Framework views for building AI endpoints.

## Setup

Ensure `djangorestframework` is installed:

```bash
pip install django-ai-sdk[drf]
```

## ChatAPIView

`ChatAPIView` is a synchronous DRF `APIView` that accepts a message and returns the agent's response as JSON.

### Usage

```python
# myapp/views.py
from django_ai_sdk.views.chat import ChatAPIView
from myapp.agents import SupportAgent

class SupportChatView(ChatAPIView):
    agent_class = SupportAgent
```

```python
# myapp/urls.py
from django.urls import path
from myapp.views import SupportChatView

urlpatterns = [
    path("api/chat/", SupportChatView.as_view()),
]
```

### Request Format

```json
POST /api/chat/
{
    "message": "Where is my order?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"  // optional
}
```

### Response Format

```json
{
    "text": "Your order is on its way!",
    "model": "gpt-4.1",
    "provider": "openai",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "usage": {
        "prompt_tokens": 85,
        "completion_tokens": 22,
        "total_tokens": 107
    }
}
```

## StreamingChatAPIView

`StreamingChatAPIView` returns a Server-Sent Events stream.

### Usage

```python
from django_ai_sdk.views.streaming import StreamingChatAPIView
from myapp.agents import SupportAgent

class SupportStreamView(StreamingChatAPIView):
    agent_class = SupportAgent
```

```python
urlpatterns = [
    path("api/chat/stream/", SupportStreamView.as_view()),
]
```

### Request Format

```
GET /api/chat/stream/?message=Hello
```

or

```
POST /api/chat/stream/
{ "message": "Hello", "conversation_id": "..." }
```

### SSE Response

```
data: {"type": "text_delta", "text": "Hello! How can I help you"}

data: {"type": "text_delta", "text": " today?"}

data: {"type": "done", "usage": {"total_tokens": 42}}

```

## Authentication

Both views work with DRF's standard authentication and permission classes:

```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class SecureChatView(ChatAPIView):
    agent_class = SupportAgent
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
```

## Customizing the Agent Per Request

Override `get_agent()` to create an agent based on request context:

```python
class PersonalizedChatView(ChatAPIView):
    def get_agent(self):
        agent = SupportAgent()
        conv_id = self.request.session.get("conversation_id")
        if conv_id:
            return agent.with_conversation(conv_id)
        return agent
```

## URL Configuration

Include the SDK's pre-built URL patterns:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("ai/", include("django_ai_sdk.urls")),
]
```

This mounts:
- `POST /ai/chat/` → `ChatAPIView`
- `GET /ai/chat/stream/` → `StreamingChatAPIView`
