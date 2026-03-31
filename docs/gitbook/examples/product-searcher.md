# Product Searcher

**Source:** [github.com/ziyacivan/product-searcher](https://github.com/ziyacivan/product-searcher)

Semantic product search powered by pgvector. Embed your product catalogue once, then let customers find what they need using natural language instead of keyword matching.

## What it demonstrates

- `SemanticMemory` with pgvector for catalogue indexing
- Generating embeddings with `djangosdk.embeddings`
- A `@tool` that retrieves semantically similar products
- Structured output to return ranked results as JSON

## Requirements

- PostgreSQL with the `pgvector` extension
- OpenAI API key (embeddings: `text-embedding-3-small`, chat: `gpt-4.1`)

## Setup

```bash
git clone https://github.com/ziyacivan/product-searcher.git
cd product-searcher

# Enable pgvector
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY + DATABASE_URL
python manage.py migrate
python manage.py index_products   # embed & index your catalogue
python manage.py runserver
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools, HasStructuredOutput
from djangosdk.memory.semantic import SemanticMemory
from djangosdk.tools import tool
from pydantic import BaseModel

class SearchResult(BaseModel):
    products: list[dict]
    explanation: str

class ProductSearchAgent(Agent, HasTools, HasStructuredOutput):
    provider = "openai"
    model = "gpt-4.1"
    output_schema = SearchResult
    memory = SemanticMemory(top_k=8)
    system_prompt = (
        "You are a product search assistant. Always call search_catalogue "
        "before answering. Return results ranked by relevance."
    )

    @tool
    def search_catalogue(self, query: str) -> list[dict]:
        """Searches the product catalogue using semantic similarity."""
        results = self.memory.search(query)
        return [
            {"name": r.content, "score": r.score, **r.metadata}
            for r in results
        ]
```

**Indexing products at startup:**

```python
from djangosdk.embeddings import embed_text
from djangosdk.memory.semantic import SemanticMemory

memory = SemanticMemory()
for product in Product.objects.all():
    memory.add(
        content=f"{product.name}. {product.description}",
        metadata={"id": product.pk, "price": str(product.price)},
    )
```

## API

```bash
# Semantic search
curl -X POST http://localhost:8000/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "lightweight running shoes for summer"}'
```

Response:

```json
{
  "products": [
    {"name": "AirFlex Runner X2", "price": "89.99", "score": 0.94},
    {"name": "CloudStep Lite", "price": "74.50", "score": 0.91}
  ],
  "explanation": "Found breathable, low-weight running shoes suitable for warm weather."
}
```
