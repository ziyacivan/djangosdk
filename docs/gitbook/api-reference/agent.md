# Agent API Reference

## Class: `Agent`

**Module:** `djangosdk.agents.base`

Base class for all AI agents. Inherits from `Promptable`, `ReasoningMixin`, `HasTools`, `HasStructuredOutput`, and `Conversational`.

## Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `provider` | `str` | `""` | Provider name from `AI_SDK.PROVIDERS`. Falls back to `DEFAULT_PROVIDER`. |
| `model` | `str` | `""` | Model identifier. Falls back to `DEFAULT_MODEL`. |
| `system_prompt` | `str` | `""` | System prompt prepended to every request. |
| `temperature` | `float` | `0.7` | Sampling temperature. |
| `max_tokens` | `int` | `2048` | Maximum tokens in the response. |
| `reasoning` | `ReasoningConfig \| None` | `None` | Reasoning config for o3, Claude 3.7, DeepSeek R1. |
| `enable_cache` | `bool` | `True` | Enable prompt caching. |
| `max_tool_iterations` | `int` | `10` | Maximum tool-call rounds per `handle()` call. |
| `tools` | `list` | `[]` | List of `@tool` functions or `BaseTool` instances. |
| `output_schema` | `type[BaseModel] \| None` | `None` | Pydantic model for structured output. |
| `mcp_servers` | `list[dict]` | `[]` | MCP server connection configs. |

## Instance Methods

### `handle(prompt: str, **kwargs) -> AgentResponse`

Synchronous completion with tool-call loop.

- Fires `agent_started` and `agent_completed` (or `agent_failed`) signals
- Runs the tool loop until no more tool calls are returned (up to `max_tool_iterations`)
- Persists messages if bound to a conversation

### `ahandle(prompt: str, **kwargs) -> Coroutine[AgentResponse]`

Async version of `handle()`.

### `stream(prompt: str, **kwargs) -> StreamingHttpResponse`

Synchronous streaming. Returns a Django `StreamingHttpResponse` with SSE content.

### `astream(prompt: str, **kwargs) -> AsyncGenerator[StreamChunk, None]`

Async streaming generator.

### `start_conversation(metadata=None) -> Conversation`

Creates a new `Conversation` ORM record and binds this agent to it.

### `with_conversation(conversation_id) -> Agent`

Returns a copy of this agent bound to the given conversation ID.

## Example

```python
from djangosdk.agents.base import Agent
from djangosdk.providers.schemas import ReasoningConfig
from djangosdk.tools.decorator import tool

@tool
def search(query: str) -> str:
    """Search the knowledge base."""
    return f"Results for: {query}"

class MyAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are a research assistant."
    temperature = 0.3
    max_tokens = 4096
    tools = [search]

agent = MyAgent()
response = agent.handle("Find information about Django migrations.")
print(response.text)
```
