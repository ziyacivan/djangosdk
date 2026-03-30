# Structured Output

Structured output allows you to enforce a Pydantic v2 schema on the model's response, receiving a validated Python object instead of raw text.

## Setup

Set `output_schema` to a Pydantic `BaseModel` class on your agent:

```python
from pydantic import BaseModel, Field
from django_ai_sdk.agents.base import Agent

class ExtractedData(BaseModel):
    title: str
    author: str
    year: int
    keywords: list[str]
    abstract: str = Field(description="A 2-3 sentence summary")

class ExtractionAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "Extract structured data from the given text."
    output_schema = ExtractedData

agent = ExtractionAgent()
response = agent.handle("Django was created by Adrian Holovaty and Simon Willison in 2003...")

data: ExtractedData = response.structured
print(data.title)     # "Django"
print(data.author)    # "Adrian Holovaty and Simon Willison"
print(data.year)      # 2003
```

## Provider Behavior

The SDK adapts to each provider's native structured output mechanism:

| Provider | Method |
|---|---|
| OpenAI GPT-4o, GPT-4.1 | `response_format: {type: "json_schema", json_schema: {...}}` |
| Anthropic | Tool-use trick — model is forced to call a schema-defined tool |
| Gemini | `response_schema` parameter |
| All others | Parse response text via `model_validate_json()` |

## Complex Schemas

Nested models, field validators, and default values all work:

```python
from pydantic import BaseModel, field_validator

class LineItem(BaseModel):
    name: str
    quantity: int
    unit_price: float

class Invoice(BaseModel):
    invoice_number: str
    customer: str
    items: list[LineItem]
    total: float

    @field_validator("total")
    @classmethod
    def check_total(cls, v, values):
        return v  # Additional validation if needed

class InvoiceAgent(Agent):
    output_schema = Invoice
```

## Handling Validation Errors

```python
from pydantic import ValidationError

try:
    response = agent.handle(raw_text)
    invoice = response.structured
except ValidationError as e:
    print(e.errors())
```

## Combining with Tools

Structured output and tools can be used together. The model will call tools to gather data, then return the final response in the specified schema:

```python
class AnalysisAgent(Agent):
    tools = [fetch_data, calculate_stats]
    output_schema = AnalysisReport
```
