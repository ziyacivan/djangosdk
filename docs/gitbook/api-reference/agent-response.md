# AgentResponse

**Module:** `djangosdk.agents.response`

`AgentResponse` is the unified response object returned by every `handle()` / `ahandle()` call.

## AgentResponse Fields

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Final assistant text content |
| `model` | `str` | Model that produced the response |
| `provider` | `str` | Provider name |
| `usage` | `UsageInfo` | Token usage counts |
| `thinking` | `ThinkingBlock \| None` | Reasoning trace (reasoning models only) |
| `structured` | `Any` | Validated Pydantic instance (when `output_schema` is set) |
| `tool_calls` | `list[dict]` | Tool calls made in the final turn |
| `raw` | `Any` | Raw litellm response object |
| `conversation_id` | `str \| None` | Conversation UUID (when bound to a conversation) |

## UsageInfo Fields

| Field | Type | Description |
|---|---|---|
| `prompt_tokens` | `int` | Input token count |
| `completion_tokens` | `int` | Output token count |
| `total_tokens` | `int` | Total tokens used |
| `cache_read_tokens` | `int` | Tokens read from cache (Anthropic/OpenAI) |
| `cache_write_tokens` | `int` | Tokens written to cache |

## ThinkingBlock Fields

| Field | Type | Description |
|---|---|---|
| `content` | `str` | Full reasoning trace text |
| `model` | `str` | Model that generated the thinking |

## StreamChunk Fields

| Field | Type | Description |
|---|---|---|
| `type` | `str` | `"text_delta"` \| `"thinking_delta"` \| `"tool_call"` \| `"done"` |
| `text` | `str` | Text content (for `text_delta` and `thinking_delta`) |
| `thinking` | `bool` | Whether this chunk is thinking content |
| `tool_call` | `dict \| None` | Tool call data (for `tool_call` type) |
| `usage` | `UsageInfo \| None` | Usage summary (on `done` chunk only) |

## Example

```python
response = agent.handle("What is 2 + 2?")

# Text
print(response.text)            # "2 + 2 = 4"

# Provider info
print(response.model)           # "gpt-4.1"
print(response.provider)        # "openai"

# Token usage
print(response.usage.total_tokens)       # 42
print(response.usage.cache_read_tokens)  # 0

# Reasoning (if applicable)
if response.thinking:
    print(response.thinking.content)    # "Let me think... 2+2=4"

# Structured output (if output_schema is set)
if response.structured:
    print(response.structured.field_name)

# Conversation
if response.conversation_id:
    print(f"Conversation: {response.conversation_id}")
```
