# Conversational

`Conversational` adds database-backed conversation history. Messages are persisted to `Conversation` and `Message` ORM models between turns.

## Starting a Conversation

```python
agent = SupportAgent()
conv = agent.start_conversation()
print(conv.id)  # UUID
```

`start_conversation()` creates a `Conversation` record and binds the agent to it.

## Continuing a Conversation

Use `with_conversation(id)` to bind an existing conversation to an agent. This returns a copy of the agent — the original is unmodified.

```python
agent = SupportAgent()

# First turn
r1 = agent.with_conversation(conv_id).handle("My name is Alice.")

# Second turn — history is loaded from the database
r2 = agent.with_conversation(conv_id).handle("What is my name?")
print(r2.text)  # "Your name is Alice."
```

## Persistent Conversation Example (Django View)

```python
from django.http import JsonResponse
from myapp.agents import SupportAgent

def chat_view(request):
    conv_id = request.session.get("conversation_id")
    agent = SupportAgent()

    if not conv_id:
        conv = agent.start_conversation()
        request.session["conversation_id"] = str(conv.id)
        conv_id = conv.id

    response = agent.with_conversation(conv_id).handle(request.POST["message"])
    return JsonResponse({"reply": response.text})
```

## Configuration

Conversation behavior is controlled via `AI_SDK.CONVERSATION`:

```python
AI_SDK = {
    "CONVERSATION": {
        "PERSIST": True,          # Save messages to DB (default: True)
        "MAX_HISTORY": 50,        # Max messages loaded per turn
        "AUTO_SUMMARIZE": False,  # Summarize old messages automatically
    },
}
```

### Auto-Summarization

When `AUTO_SUMMARIZE = True` and the conversation exceeds `MAX_HISTORY` messages, the SDK automatically:
1. Selects the oldest messages beyond the limit
2. Sends them to the model for summarization
3. Replaces them with a single system message containing the summary
4. Deletes the original messages

This keeps the active context within the token budget while preserving continuity.

## Methods

### `start_conversation(metadata=None) -> Conversation`

Creates a new `Conversation` record and binds this agent to it.

```python
conv = agent.start_conversation(metadata={"user_id": request.user.id})
```

### `with_conversation(conversation_id) -> Agent`

Returns a copy of the agent bound to the given conversation ID. The original agent is not modified.

```python
bound_agent = agent.with_conversation("550e8400-e29b-41d4-a716-446655440000")
```

## Database Models

`Conversational` works with two ORM models:

- **`Conversation`** — one record per session, tracks `agent_class`, `provider`, `model`, metadata, and cost
- **`Message`** — one record per turn, tracks `role`, `content`, `tool_calls`, `thinking_content`, token counts

See [Django Integration → Admin](../../django-integration/admin.md) for the admin interface.
