# Examples

Standalone Django projects that demonstrate djangosdk in action. Each example is self-contained — clone the repo, add your API key, and run `manage.py runserver`.

All examples live in the [`examples/`](https://github.com/ziyacivan/djangosdk/tree/master/examples) directory of the repository. They are **not included** in the PyPI package — `pip install djangosdk` installs only the library.

## Quick Start

```bash
git clone https://github.com/ziyacivan/djangosdk.git
cd djangosdk/examples/01-basic-chat

pip install djangosdk
cp .env.example .env   # add your API key
python manage.py migrate
python manage.py runserver
```

## Examples at a Glance

| Example | Difficulty | Key Feature |
|---------|-----------|-------------|
| [Basic Chat](basic-chat.md) | Beginner | `Agent`, `astream()`, SSE streaming |
| [Tool-Calling Agent](tool-calling.md) | Beginner | `@tool`, `HasTools`, tool dispatch loop |
| [Structured Output](structured-output.md) | Beginner | `output_schema`, `response.structured` |
| [Reasoning Models](reasoning.md) | Intermediate | `ReasoningConfig`, `response.thinking` |
| [RAG / Document Q&A](rag.md) | Intermediate | `SemanticMemory`, pgvector, PDF ingestion |
| [Multi-Agent Pipeline](multi-agent.md) | Advanced | `pipeline()`, chained agents |
