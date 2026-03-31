# Smart Django Shell

**Source:** [github.com/ziyacivan/smart-django-shell](https://github.com/ziyacivan/smart-django-shell)

An AI-powered Django management shell that lets you query and manipulate your database with plain English. Describe what you want — the agent generates and executes the ORM query.

## What it demonstrates

- `HasTools` for safe ORM execution
- `Agent.handle()` in a synchronous management command context
- Structured output with Pydantic to validate generated queries before running
- Guarding against unsafe operations (write protection mode)

## Setup

```bash
git clone https://github.com/ziyacivan/smart-django-shell.git
cd smart-django-shell
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py ai_shell
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools, HasStructuredOutput
from djangosdk.tools import tool
from pydantic import BaseModel

class QueryPlan(BaseModel):
    model_name: str
    filters: dict
    order_by: list[str]
    limit: int
    explanation: str

class DjangoShellAgent(Agent, HasTools, HasStructuredOutput):
    provider = "openai"
    model = "gpt-4.1"
    output_schema = QueryPlan
    system_prompt = (
        "You are a Django ORM expert. Given a natural-language request "
        "and a list of installed models, produce a QueryPlan JSON object."
    )

    @tool
    def list_models(self) -> list[str]:
        """Returns all installed Django model names."""
        from django.apps import apps
        return [m.__name__ for m in apps.get_models()]

    @tool
    def describe_model(self, model_name: str) -> dict:
        """Returns field names and types for a given Django model."""
        ...
```

**Running a query from the management command:**

```python
agent = DjangoShellAgent()
response = agent.handle("Show me the 10 most recent orders that are still pending")

plan: QueryPlan = response.structured
print(plan.explanation)  # "Filter Order by status='pending', order by created_at desc, limit 10"

# Execute the plan
results = eval_query_plan(plan)
```

## Safety Mode

Pass `--readonly` to the management command to block any non-`SELECT` operation:

```bash
python manage.py ai_shell --readonly
```

## Try These Prompts

- `"Which users signed up last week but haven't placed an order?"`
- `"Find all products with stock below 5"`
- `"How many orders were completed in March 2026?"`
