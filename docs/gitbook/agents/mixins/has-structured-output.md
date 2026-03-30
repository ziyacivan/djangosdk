# HasStructuredOutput

`HasStructuredOutput` adds Pydantic v2-backed structured output to an agent. When `output_schema` is set, the response is validated and returned as a Pydantic instance via `response.structured`.

## Defining an Output Schema

```python
from pydantic import BaseModel
from django_ai_sdk.agents.base import Agent

class ReviewAnalysis(BaseModel):
    sentiment: str        # "positive" | "negative" | "neutral"
    score: float          # 0.0 - 1.0
    summary: str
    key_points: list[str]

class ReviewAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "Analyze product reviews."
    output_schema = ReviewAnalysis
```

## Accessing the Structured Response

```python
agent = ReviewAgent()
response = agent.handle("This product is amazing! Fast delivery and great quality.")
analysis: ReviewAnalysis = response.structured
print(analysis.sentiment)    # "positive"
print(analysis.score)        # 0.95
print(analysis.key_points)   # ["Fast delivery", "Great quality"]
```

## Provider Behavior

The SDK adapts the structured output request to each provider:

| Provider | Method |
|---|---|
| OpenAI GPT-4o+ | `response_format: {type: "json_schema", ...}` |
| Anthropic | Tool-use trick (forces model to call a schema-defined tool) |
| Gemini | `response_schema` parameter |
| Fallback | Parses response text via `model_validate_json()` |

## Nested Models

Pydantic's full feature set is supported, including nested models:

```python
class Address(BaseModel):
    street: str
    city: str

class Customer(BaseModel):
    name: str
    email: str
    address: Address

class CustomerAgent(Agent):
    output_schema = Customer
```

## Validation Errors

If the model returns invalid JSON or a response that does not match the schema, a `ValidationError` from Pydantic will be raised. Handle this in your view or calling code:

```python
from pydantic import ValidationError

try:
    response = agent.handle(user_input)
    data = response.structured
except ValidationError as e:
    # Handle invalid structured output
    pass
```
