# djangosdk Examples

Standalone Django projects demonstrating how to use [djangosdk](https://docs.djangosdk.com).

Each example is self-contained. Install `djangosdk`, copy the `.env.example`, and run `manage.py runserver`.

## Examples

| # | Example | What it shows |
|---|---------|---------------|
| [01-basic-chat](01-basic-chat/) | Basic Chat | Agent setup, SSE streaming, HTMX real-time UI |
| [02-tool-calling](02-tool-calling/) | Tool-Calling Agent | `@tool` decorator, multi-tool dispatch, customer support bot |
| [03-rag](03-rag/) | RAG / Document Q&A | PDF ingestion, pgvector, SemanticMemory, source attribution |
| [04-structured-output](04-structured-output/) | Structured Output | Pydantic schema, `output_schema`, JSON extraction |
| [05-reasoning](05-reasoning/) | Reasoning Models | `ReasoningConfig`, o4-mini, `response.thinking` |
| [06-multi-agent](06-multi-agent/) | Multi-Agent Pipeline | `pipeline()`, `handoff()`, chained agents |

## Quick Start

```bash
cd examples/01-basic-chat
pip install djangosdk
cp .env.example .env   # add your API key
python manage.py migrate
python manage.py runserver
```

## Requirements

- Python >= 3.11
- Django >= 4.2
- An API key for the provider used in each example (see each example's `.env.example`)
