# 05 — Reasoning Models

Compare OpenAI o4-mini and Claude 3.7 Sonnet extended thinking on complex problems.

## What it demonstrates

- `ReasoningConfig` with `effort="high"` (OpenAI o4-mini)
- `ReasoningConfig` with `extended_thinking=True, thinking_budget=10000` (Claude 3.7)
- `response.thinking` — accessing the model's internal reasoning trace
- Provider switching with the same agent interface

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY and/or ANTHROPIC_API_KEY
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## API

```bash
# o4-mini
curl -X POST http://localhost:8000/solve/ \
  -H "Content-Type: application/json" \
  -d '{"problem": "What is the 100th Fibonacci number?", "model": "o4-mini"}'

# Claude 3.7 (returns thinking field)
curl -X POST http://localhost:8000/solve/ \
  -H "Content-Type: application/json" \
  -d '{"problem": "Prove that sqrt(2) is irrational.", "model": "claude-3-7"}'
```

## Key files

| File | Purpose |
|------|---------|
| `solver/agents.py` | Two agent classes with different `ReasoningConfig` |
| `solver/views.py` | Returns `answer` + optional `thinking` in JSON |
| `solver/templates/solver/index.html` | Side-by-side comparison UI |

## ReasoningConfig reference

| Provider | Config | Effect |
|----------|--------|--------|
| OpenAI o1/o3/o4 | `ReasoningConfig(effort="low/medium/high")` | Controls reasoning compute |
| Anthropic Claude 3.7 | `ReasoningConfig(extended_thinking=True, thinking_budget=N)` | Enables thinking tokens |
| DeepSeek R1 | `ReasoningConfig(budget_tokens=N)` | Budget for chain-of-thought |
