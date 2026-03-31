# Multi-Agent Pipeline

**Source:** [`examples/06-multi-agent/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/06-multi-agent)

Three specialized agents collaborate to produce a research report: Gatherer → Analyst → Writer. Each agent's output becomes the next agent's input.

## What it demonstrates

- The `pipeline()` pattern from `djangosdk.orchestration`
- Specialized agents with different models and single responsibilities
- Aggregate token usage tracking across multiple agent calls
- Clean separation of concerns — each agent does exactly one thing

## Setup

```bash
cd examples/06-multi-agent
pip install djangosdk python-decouple
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## Pipeline Architecture

```
User topic
    ↓
GathererAgent (gpt-4.1-mini)
  "Collect raw facts, statistics, recent developments"
    ↓  raw facts text
AnalystAgent (gpt-4.1)
  "Identify 3 key trends, explain underlying dynamics"
    ↓  analysis text
WriterAgent (gpt-4.1)
  "Write executive summary + 3 key takeaways"
    ↓  final report
```

## Key Code

```python
from djangosdk.agents import Agent

class GathererAgent(Agent):
    model = "gpt-4.1-mini"
    system_prompt = "Collect raw facts and recent developments about the topic."

class AnalystAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "Identify the 3 most important trends and explain the dynamics."

class WriterAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "Write a concise executive summary with key takeaways."

def run_research_pipeline(topic: str) -> dict:
    facts = GathererAgent().handle(f"Research: {topic}").text
    analysis = AnalystAgent().handle(f"Facts:\n{facts}\n\nAnalyze.").text
    report = WriterAgent().handle(f"Analysis:\n{analysis}\n\nWrite summary.").text
    return {"raw_facts": facts, "analysis": analysis, "report": report}
```

## API

```bash
curl -X POST http://localhost:8000/research/ \
  -H "Content-Type: application/json" \
  -d '{"topic": "The rise of vector databases in 2025–2026"}'
```

Response includes `raw_facts`, `analysis`, `report`, and per-stage `usage`.

## Extending the Pipeline

- Add a `FactCheckerAgent` between Analyst and Writer
- Switch `AnalystAgent` to Claude 3.7 Sonnet with `extended_thinking=True` for deeper analysis
- Use `parallel()` to run multiple `GathererAgent` instances on different sub-topics concurrently
