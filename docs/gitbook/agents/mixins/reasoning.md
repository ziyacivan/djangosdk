# ReasoningMixin

`ReasoningMixin` adds support for reasoning models. Set `reasoning = ReasoningConfig(...)` on an agent class to enable reasoning capabilities.

## ReasoningConfig

```python
from djangosdk.providers.schemas import ReasoningConfig

config = ReasoningConfig(
    effort="medium",              # "low" | "medium" | "high" — for o3/o4-mini
    budget_tokens=8000,           # Token budget for DeepSeek R1
    extended_thinking=False,      # Enable for Claude 3.7 Sonnet
    thinking_budget=10000,        # Token budget for Claude 3.7 extended thinking
    stream_thinking=False,        # Include thinking_delta chunks in streams
)
```

## OpenAI o3 / o4-mini

```python
from djangosdk.agents.base import Agent
from djangosdk.providers.schemas import ReasoningConfig

class ReasoningAgent(Agent):
    provider = "openai"
    model = "o4-mini"
    reasoning = ReasoningConfig(effort="high")

agent = ReasoningAgent()
response = agent.handle("What is the optimal solution to the travelling salesman problem for 10 cities?")
print(response.text)
```

The `effort` parameter maps to the `reasoning_effort` parameter in the OpenAI API.

## Claude 3.7 Extended Thinking

```python
class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=15000,
    )

agent = ThinkingAgent()
response = agent.handle("Prove that there are infinitely many prime numbers.")
print(response.thinking.content)  # The thinking trace
print(response.text)              # The final answer
```

## DeepSeek R1

```python
class DeepSeekAgent(Agent):
    provider = "deepseek"
    model = "deepseek-reasoner"
    reasoning = ReasoningConfig(budget_tokens=8000)
```

## Streaming Thinking Content

To stream the reasoning trace along with the final response, set `stream_thinking=True`:

```python
class StreamingThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=10000,
        stream_thinking=True,
    )
```

When streaming, chunks with `chunk.type == "thinking_delta"` will be emitted before the final `text_delta` chunks.

## Accessing Thinking Content

Thinking content is available on the response:

```python
response = agent.handle(prompt)
if response.thinking:
    print(response.thinking.content)  # Full reasoning trace
    print(response.thinking.model)    # Model that generated it
```

## Parameter Mapping

`LiteLLMProvider` injects the correct API parameters automatically:

| Model family | `ReasoningConfig` field | API parameter |
|---|---|---|
| o3, o4-mini | `effort` | `reasoning_effort` |
| Claude 3.7 | `extended_thinking`, `thinking_budget` | `thinking.type`, `thinking.budget_tokens` |
| DeepSeek R1 | `budget_tokens` | `budget_tokens` |
| Gemini 2.5 | `effort` | `thinking_config.thinking_budget` (via litellm) |
