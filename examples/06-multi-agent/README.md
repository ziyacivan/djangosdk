# 06 — Multi-Agent Pipeline

Three specialized agents collaborate to produce a research report: Gatherer → Analyst → Writer.

## What it demonstrates

- `pipeline()` pattern: each agent's output feeds the next
- Specialized agents with different models and roles
- Aggregate token usage across multiple agent calls
- Clean separation of concerns — each agent does one thing well

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## How the pipeline works

```
User topic
    ↓
GathererAgent (gpt-4.1-mini)
  "Collect raw facts, statistics, recent developments"
    ↓ raw_facts text
AnalystAgent (gpt-4.1)
  "Identify 3 key trends, compare, explain dynamics"
    ↓ analysis text
WriterAgent (gpt-4.1)
  "Write executive summary + key takeaways"
    ↓ final report
```

## API

```bash
curl -X POST http://localhost:8000/research/ \
  -H "Content-Type: application/json" \
  -d '{"topic": "The rise of vector databases in 2025-2026"}'
```

Response includes `raw_facts`, `analysis`, `report`, and `usage` per stage.

## Key files

| File | Purpose |
|------|---------|
| `research/agents.py` | 3 agent classes + `run_research_pipeline()` orchestrator |
| `research/views.py` | POST endpoint, returns all 3 stages |
| `research/templates/research/index.html` | Step-by-step pipeline visualization |

## Extending this example

- Add a 4th `FactCheckerAgent` before the writer
- Switch `AnalystAgent` to Claude 3.7 with extended thinking for deeper analysis
- Use `parallel()` to run multiple `GathererAgent` instances concurrently with different sub-topics
