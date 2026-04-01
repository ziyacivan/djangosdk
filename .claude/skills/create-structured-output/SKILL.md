---
name: create-structured-output
description: >
  Scaffolds a Pydantic v2 output schema and attaches it to an Agent for
  structured JSON output. Covers provider-specific paths (OpenAI json_schema,
  Anthropic tool-use, Gemini response_schema, fallback parsing). Invoke when
  the user says "create a structured output schema", "make my agent return JSON",
  "define a Pydantic output model", "get structured data from the agent",
  "add output schema", or "validate agent output".
triggers:
  - create a structured output schema
  - make my agent return JSON
  - define a Pydantic output model
  - get structured data from the agent
  - add output schema
  - validate agent output
  - extract structured data
  - agent return typed output
  - structured response from agent
  - response.structured
  - output_schema
---

# Create Structured Output

You are adding structured (typed, validated) output to a `django-ai-sdk` agent using Pydantic v2.

## Step 1 — Define the Pydantic Model

```python
# myapp/schemas.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0–1")
    reasoning: str = Field(description="Brief explanation of the classification")
```

**Supported field types:** `str`, `int`, `float`, `bool`, `Literal`, `list`, `dict`, nested `BaseModel`, `Optional`, `Union`, discriminated unions.

## Step 2 — Attach to the Agent

```python
# myapp/agents.py
from djangosdk.agents.base import Agent
from myapp.schemas import SentimentResult


class SentimentAgent(Agent):
    model = "gpt-4.1"
    system_prompt = (
        "Classify the sentiment of the text the user provides. "
        "Always respond with valid JSON matching the required schema."
    )
    output_schema = SentimentResult   # <-- attach here
```

## Step 3 — Access the Structured Response

```python
agent = SentimentAgent()
response = agent.handle("I absolutely love this product!")

# Pydantic model instance
result = response.structured
print(result.sentiment)    # "positive"
print(result.confidence)   # 0.97
print(result.reasoning)    # "The text uses enthusiastic language..."

# Raw text is also available
print(response.text)       # the JSON string returned by the model
```

## Step 4 — Provider-Specific Paths

The `LiteLLMProvider` selects the enforcement strategy automatically based on the provider:

| Provider | Enforcement strategy |
|---|---|
| OpenAI GPT-4o, GPT-4.1+ | `response_format: {type: "json_schema", ...}` — strict JSON mode |
| Anthropic Claude | Tool-use trick — model calls a synthetic "respond" tool |
| Google Gemini | `response_schema` parameter |
| All others / fallback | `StructuredOutput.extract_json_from_text()` — parses prose response |

You don't need to configure this — it's automatic. The fallback handles markdown-fenced JSON blocks and inline JSON in prose.

## Step 5 — Nested Models

```python
from pydantic import BaseModel
from typing import List


class Entity(BaseModel):
    name: str
    type: Literal["person", "organization", "location"]
    confidence: float


class ExtractionResult(BaseModel):
    entities: List[Entity]
    summary: str
    total_count: int


class EntityExtractor(Agent):
    model = "gpt-4.1"
    system_prompt = "Extract named entities from the provided text."
    output_schema = ExtractionResult


# Usage:
agent = EntityExtractor()
response = agent.handle("Apple CEO Tim Cook announced...")

for entity in response.structured.entities:
    print(f"{entity.name} ({entity.type}) — confidence: {entity.confidence}")
```

## Step 6 — Optional Fields and Defaults

Use `Optional` with defaults for fields the model might omit:

```python
from typing import Optional
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    answer: str
    citations: Optional[list[str]] = None     # may be absent
    confidence: float = 0.5                   # default if omitted
    follow_up_questions: list[str] = []       # empty list default
```

## Step 7 — Discriminated Unions

For multi-type outputs where the model chooses between alternatives:

```python
from typing import Annotated, Union
from pydantic import BaseModel, Field


class BookResult(BaseModel):
    type: Literal["book"] = "book"
    title: str
    author: str
    isbn: str


class ArticleResult(BaseModel):
    type: Literal["article"] = "article"
    title: str
    publication: str
    url: str


class SearchResult(BaseModel):
    result: Annotated[Union[BookResult, ArticleResult], Field(discriminator="type")]
    query: str


class SearchAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "Search for books or articles and return the best match."
    output_schema = SearchResult
```

## Step 8 — Manual Schema Inspection

```python
from djangosdk.structured.output import StructuredOutput
from myapp.schemas import SentimentResult

# Inspect the generated JSON schema
schema = StructuredOutput.get_json_schema(SentimentResult)
print(schema)

# Manually validate a JSON string
raw = '{"sentiment": "positive", "confidence": 0.9, "reasoning": "Enthusiastic tone"}'
result = StructuredOutput.validate(SentimentResult, raw)
print(result.sentiment)  # "positive"
```

## Step 9 — Test Structured Output

```python
import json
import pytest
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import SentimentAgent


@pytest.fixture
def fake_provider():
    return FakeProvider()


def test_sentiment_agent_returns_pydantic_model(fake_provider):
    fake_provider.set_response(json.dumps({
        "sentiment": "positive",
        "confidence": 0.95,
        "reasoning": "The text uses enthusiastic language.",
    }))
    agent = SentimentAgent()
    agent._provider = fake_provider

    response = agent.handle("I love this product!")

    assert response.structured is not None
    assert response.structured.sentiment == "positive"
    assert response.structured.confidence >= 0.9


def test_sentiment_agent_handles_invalid_json_gracefully(fake_provider):
    # Fallback: model returns prose with embedded JSON
    fake_provider.set_response(
        'After careful analysis: ```json\n{"sentiment": "neutral", "confidence": 0.6, "reasoning": "Balanced."}\n```'
    )
    agent = SentimentAgent()
    agent._provider = fake_provider

    response = agent.handle("This product is fine.")

    assert response.structured is not None
    assert response.structured.sentiment == "neutral"
```
