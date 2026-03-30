# Embeddings

`django-ai-sdk` provides a simple API for generating text embeddings, usable for semantic search, RAG, and similarity comparisons.

## Basic Usage

```python
from djangosdk.embeddings.embed import embed, aembed

# Synchronous
vector = embed("Hello, world!")
print(len(vector))  # 1536 for text-embedding-3-small

# Async
vector = await aembed("Hello, world!")
```

## Batch Embeddings

```python
from djangosdk.embeddings.embed import embed_many

vectors = embed_many([
    "Django is a Python web framework.",
    "Pydantic provides data validation.",
    "litellm routes to 100+ AI providers.",
])
# Returns list[list[float]]
```

## Configuration

```python
AI_SDK = {
    "EMBEDDINGS": {
        "MODEL": "text-embedding-3-small",  # Default
        "PROVIDER": "openai",
        "DIMENSIONS": 1536,                 # Optional, for models that support it
    },
}
```

## Supported Embedding Models

| Model | Provider | Dimensions |
|---|---|---|
| `text-embedding-3-small` | OpenAI | 1536 |
| `text-embedding-3-large` | OpenAI | 3072 |
| `text-embedding-ada-002` | OpenAI | 1536 |
| `voyage-3` | Voyage AI | 1024 |
| `embed-english-v3.0` | Cohere | 1024 |
| `nomic-embed-text` | Ollama | 768 |

Any model supported by litellm can be used.

## Using Embeddings for RAG

See [Semantic Memory](conversation/semantic.md) for a complete RAG integration example.

## Cosine Similarity

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

v1 = embed("cat")
v2 = embed("kitten")
v3 = embed("database")

print(cosine_similarity(v1, v2))  # ~0.87 (similar)
print(cosine_similarity(v1, v3))  # ~0.12 (dissimilar)
```
