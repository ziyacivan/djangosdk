# Conversation Persistence

`django-ai-sdk` persists conversation history to the Django ORM using two models: `Conversation` and `Message`.

## Database Models

### Conversation

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDField` (PK) | Unique conversation identifier |
| `agent_class` | `CharField` | Dotted path to the agent class |
| `provider` | `CharField` | Provider name |
| `model` | `CharField` | Model identifier |
| `metadata` | `JSONField` | Arbitrary metadata (user ID, session, etc.) |
| `total_cost` | `DecimalField` | Cumulative cost (updated per turn) |
| `created_at` | `DateTimeField` | Creation timestamp |
| `updated_at` | `DateTimeField` | Last update timestamp |

### Message

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDField` (PK) | Unique message identifier |
| `conversation` | `ForeignKey(Conversation)` | Parent conversation |
| `role` | `CharField` | `system`, `user`, `assistant`, `tool`, `thinking` |
| `content` | `TextField` | Message text |
| `tool_calls` | `JSONField` | Tool calls made (assistant messages) |
| `tool_call_id` | `CharField` | Tool call ID (tool messages) |
| `thinking_content` | `TextField` | Reasoning trace (Claude 3.7, o3, etc.) |
| `prompt_tokens` | `IntegerField` | Input token count |
| `completion_tokens` | `IntegerField` | Output token count |
| `cache_read_tokens` | `IntegerField` | Tokens read from cache |
| `cache_write_tokens` | `IntegerField` | Tokens written to cache |
| `created_at` | `DateTimeField` | Creation timestamp |

## Querying Conversations

```python
from djangosdk.models.conversation import Conversation
from djangosdk.models.message import Message

# All conversations for a user
convs = Conversation.objects.filter(metadata__user_id=user.id)

# Messages in a conversation
messages = Message.objects.filter(conversation=conv).order_by("created_at")

# Last assistant message
last = Message.objects.filter(
    conversation=conv,
    role=Message.Role.ASSISTANT,
).order_by("-created_at").first()
```

## Disabling Persistence

Set `PERSIST = False` to keep history only in memory for the current request:

```python
AI_SDK = {
    "CONVERSATION": {
        "PERSIST": False,
    },
}
```

## Running Migrations

After installing the SDK:

```bash
python manage.py migrate
```

## Admin Interface

Conversations and messages are available in Django Admin. See [Django Admin](../django-integration/admin.md).
