# AgentRequest

**Module:** `django_ai_sdk.agents.request`

`AgentRequest` is a dataclass that encapsulates all data sent to a provider for a single completion. It is built internally by `Promptable._build_request()` and passed to the provider.

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `messages` | `list[dict]` | — | Full message history in OpenAI-compatible format |
| `model` | `str` | `""` | Model identifier |
| `provider` | `str` | `""` | Provider name |
| `system_prompt` | `str` | `""` | System prompt |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_tokens` | `int` | `2048` | Maximum response tokens |
| `tools` | `list[dict]` | `[]` | JSON schema tool definitions |
| `output_schema` | `dict \| None` | `None` | Pydantic-derived JSON schema for structured output |
| `reasoning` | `ReasoningConfig \| None` | `None` | Reasoning model configuration |
| `enable_cache` | `bool` | `True` | Enable prompt caching |
| `stream` | `bool` | `False` | Whether this is a streaming request |
| `extra` | `dict` | `{}` | Pass-through params for litellm |

## Message Format

Messages follow the OpenAI message format:

```python
# User message
{"role": "user", "content": "Hello!"}

# Assistant message
{"role": "assistant", "content": "Hi there!"}

# System message
{"role": "system", "content": "You are a helpful assistant."}

# Tool result message
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "name": "lookup_order",
    "content": "Order status: shipped",
}

# Assistant message with tool calls
{
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "lookup_order",
                "arguments": "{\"order_id\": \"XYZ\"}",
            },
        }
    ],
}
```
