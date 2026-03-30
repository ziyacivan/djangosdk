---
name: create-agent
description: >
  Creates a new Agent subclass with correct mixin composition. Invoke when the user
  says "create an agent", "make a new agent class", "write an agent for [task]",
  "add a [name]Agent", "build a [tool-calling / conversational / reasoning] agent",
  or "I need an agent that does [X]". Also triggers on "implement an agent" or
  "scaffold a new Agent subclass".
triggers:
  - create an agent
  - create a new agent
  - make a new agent class
  - write an agent for
  - add a agent
  - build a agent
  - implement an agent
  - scaffold an agent subclass
  - new Agent subclass
  - I need an agent
---

# Create a New Agent Subclass

You are creating a new `Agent` subclass for the `django-ai-sdk` project.

## Step 1 — Gather Requirements

Ask or infer the following before writing code:
1. **What does this agent do?** (summarization, code review, customer support, data analysis...)
2. **Does it need tools?** → set `tools = [fn1, fn2]` and register `@tool` functions
3. **Does it need structured output?** → set `output_schema = MyPydanticModel`
4. **Is it conversational?** → set `enable_conversation = True` for ORM persistence
5. **Does it use a reasoning model?** → set `reasoning = ReasoningConfig(...)`
6. **Which provider and model?** → or omit to use project defaults from `AI_SDK` settings

## Step 2 — Choose the Right Capability Set

`Agent` already inherits all mixins. Activate capabilities via class attributes only:

| Capability | Class attribute to set |
|---|---|
| Tool calling | `tools = [my_tool_fn]` |
| Structured output | `output_schema = MyPydanticModel` |
| Conversation persistence | `enable_conversation = True` |
| Reasoning model | `reasoning = ReasoningConfig(effort="high")` |
| Prompt caching | `enable_cache = True` (default) |

Never subclass the mixins directly — subclass `Agent` only.

## Step 3 — Tool Registration

Define tools with the `@tool` decorator, then assign to the class:

```python
from djangosdk.tools.decorator import tool

@tool
def get_weather(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
    """Return current weather for a city."""
    # implementation
    ...

class WeatherAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a helpful weather assistant."
    tools = [get_weather]
```

The `@tool` decorator automatically generates the JSON schema. The dispatch loop in `Agent.handle()` calls tools and loops until the model stops requesting them (capped at `max_tool_iterations=10`).

## Step 4 — Structured Output

For agents that must return a validated Pydantic model:

```python
from pydantic import BaseModel
from djangosdk.agents.base import Agent

class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    reasoning: str

class SentimentAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "Classify the sentiment of the provided text."
    output_schema = SentimentResult

# Usage:
response = agent.handle("I love this product!")
print(response.structured)  # SentimentResult instance
```

## Step 5 — Reasoning Agents

For agents backed by a reasoning model (o3, Claude 3.7, DeepSeek R1):

```python
from djangosdk.agents.base import Agent
from djangosdk.providers.schemas import ReasoningConfig

# OpenAI o3 / o4-mini
class DeepAnalysisAgent(Agent):
    provider = "openai"
    model = "o3"
    reasoning = ReasoningConfig(effort="high")

# Anthropic Claude 3.7 Sonnet (extended thinking)
class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(extended_thinking=True, thinking_budget=16000)

# DeepSeek R1
class DeepSeekAgent(Agent):
    provider = "deepseek"
    model = "deepseek/deepseek-r1"
    reasoning = ReasoningConfig(budget_tokens=8000)
```

Access thinking blocks: `response.thinking` → `List[ThinkingBlock]`

## Step 6 — Conversational Agent (Persistent History)

```python
class SupportAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a helpful support agent."
    enable_conversation = True

# Usage — pass conversation_id to persist history in the DB:
response = agent.handle("My order hasn't arrived.", conversation_id="conv-abc123")
```

## Step 7 — Agent File Template

Place new agents in the consuming project (e.g. `myapp/agents.py`), not in the SDK itself:

```python
"""[AgentName] — [one-line description]."""
from __future__ import annotations

from typing import Literal

from djangosdk.agents.base import Agent
from djangosdk.providers.schemas import ReasoningConfig
from djangosdk.tools.decorator import tool

# Define tools here or import them
# @tool
# def my_tool(...) -> str: ...


class [Name]Agent(Agent):
    provider = "[provider]"           # omit to use DEFAULT_PROVIDER
    model = "[model]"                 # omit to use DEFAULT_MODEL
    system_prompt = "[system prompt]"
    temperature = 0.7
    max_tokens = 2048
    tools = []                        # remove if no tools
    output_schema = None              # set to Pydantic model if needed
    reasoning = None                  # set to ReasoningConfig if needed
    enable_cache = True
    enable_conversation = False       # set True for persistent history

    # Optional: override handle for pre/post processing
    # def handle(self, prompt: str, **kwargs) -> AgentResponse:
    #     response = super().handle(prompt, **kwargs)
    #     return response


# Usage:
# agent = [Name]Agent()
# response = agent.handle("[example prompt]")
# print(response.text)
```

## Step 8 — Write Tests Immediately

Always write tests alongside the agent. Use the `write-tests` skill or follow this pattern:

```python
from djangosdk.testing.fakes import FakeProvider
from djangosdk.testing.assertions import assert_prompt_sent

def test_[name]_agent_returns_text(fake_provider):
    fake_provider.set_response("[expected output]")
    agent = [Name]Agent()
    agent._provider = fake_provider

    response = agent.handle("[example prompt]")

    assert response.text == "[expected output]"
    assert_prompt_sent(fake_provider, "[example prompt]")
```
