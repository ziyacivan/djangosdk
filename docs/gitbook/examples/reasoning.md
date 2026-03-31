# Reasoning Models

**Source:** [`examples/05-reasoning/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/05-reasoning)

Compare OpenAI o4-mini and Claude 3.7 Sonnet extended thinking on complex problems. Inspect the model's internal reasoning with `response.thinking`.

## What it demonstrates

- `ReasoningConfig(effort="high")` for OpenAI o4-mini
- `ReasoningConfig(extended_thinking=True, thinking_budget=10000)` for Claude 3.7
- `response.thinking` — the model's full reasoning trace
- Two agents, same interface, different providers

## Setup

```bash
cd examples/05-reasoning
pip install djangosdk python-decouple
cp .env.example .env   # set OPENAI_API_KEY and/or ANTHROPIC_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.providers.schemas import ReasoningConfig

class O4MiniSolverAgent(Agent):
    provider = "openai"
    model = "o4-mini"
    reasoning = ReasoningConfig(effort="high")
    system_prompt = "You are an expert problem solver."

class ClaudeSonnetSolverAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=10000,
    )
    system_prompt = "You are an expert problem solver."
```

**Accessing the thinking trace (Claude only):**

```python
agent = ClaudeSonnetSolverAgent()
response = agent.handle("Prove that sqrt(2) is irrational.")

print(response.text)             # The final answer
print(response.thinking.content) # The extended thinking trace
```

## ReasoningConfig Reference

| Provider | Config | Effect |
|----------|--------|--------|
| OpenAI o1/o3/o4 | `ReasoningConfig(effort="low/medium/high")` | Controls reasoning compute budget |
| Anthropic Claude 3.7 | `ReasoningConfig(extended_thinking=True, thinking_budget=N)` | Enables thinking tokens (billed separately) |
| DeepSeek R1 | `ReasoningConfig(budget_tokens=N)` | Chain-of-thought budget |

`LiteLLMProvider` injects the correct parameters automatically — you never touch the raw API.
