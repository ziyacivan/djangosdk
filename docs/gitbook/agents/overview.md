# Agents

The `Agent` class is the primary abstraction in `django-ai-sdk`. An agent encapsulates a provider, a model, a system prompt, tools, and any configuration needed to handle a request.

## Defining an Agent

Subclass `Agent` and declare class attributes:

```python
from djangosdk.agents.base import Agent
from djangosdk.providers.schemas import ReasoningConfig

class MyAgent(Agent):
    provider = "openai"             # From AI_SDK.PROVIDERS
    model = "gpt-4.1"
    system_prompt = "You are a helpful assistant."
    temperature = 0.7               # Default: 0.7
    max_tokens = 2048               # Default: 2048
    enable_cache = True             # Enable prompt caching
    max_tool_iterations = 10        # Max tool-call rounds per turn
    tools = []                      # List of @tool functions or BaseTool instances
    reasoning = None                # ReasoningConfig for reasoning models
    mcp_servers = []                # MCP server configs (Phase 2)
```

## Calling an Agent

### Synchronous

```python
agent = MyAgent()
response = agent.handle("What is the capital of Turkey?")
print(response.text)
```

### Asynchronous

```python
response = await agent.ahandle("What is the capital of Turkey?")
print(response.text)
```

### Streaming

```python
# Returns a StreamingHttpResponse (use in Django views)
return agent.stream("Tell me a story.")

# Async streaming generator
async for chunk in agent.astream("Tell me a story."):
    print(chunk.text)
```

## Agent Response

Every `handle()` / `ahandle()` call returns an `AgentResponse`:

```python
response.text             # str: The final assistant message
response.model            # str: The model that produced the response
response.provider         # str: The provider name
response.usage            # UsageInfo: Token counts
response.thinking         # ThinkingBlock | None: Reasoning content
response.structured       # Pydantic instance | None: Validated output
response.tool_calls       # list[dict]: Tool calls made (if any)
response.conversation_id  # str | None: Conversation UUID
```

## Mixin Composition

`Agent` inherits from five mixins. Each adds a distinct capability:

| Mixin | Adds |
|---|---|
| `Promptable` | `handle()`, `ahandle()`, `stream()`, `astream()` |
| `HasTools` | Tool calling, dispatch loop |
| `HasStructuredOutput` | Pydantic output validation |
| `Conversational` | DB-backed conversation history |
| `ReasoningMixin` | Reasoning model parameters |

All five are composed by default. You can create leaner agents by composing only the mixins you need:

```python
from djangosdk.agents.mixins.promptable import Promptable
from djangosdk.agents.mixins.has_tools import HasTools

class LeanAgent(Promptable, HasTools):
    provider = "openai"
    model = "gpt-4.1"
    tools = [my_tool]
```

## Default Provider / Model

If `provider` or `model` is left empty, the SDK falls back to `AI_SDK.DEFAULT_PROVIDER` and `AI_SDK.DEFAULT_MODEL`:

```python
class MinimalAgent(Agent):
    system_prompt = "You are a minimal agent."

agent = MinimalAgent()
response = agent.handle("Hello!")
```

## Using Multiple Agents Together

Agents are plain Python objects. You can chain them, pipe output from one into another, or run them in parallel with `asyncio.gather`:

```python
import asyncio

async def pipeline(user_input: str):
    classifier = ClassifierAgent()
    responder = ResponderAgent()

    classification = await classifier.ahandle(user_input)
    response = await responder.ahandle(
        f"Topic: {classification.text}\nQuestion: {user_input}"
    )
    return response
```
