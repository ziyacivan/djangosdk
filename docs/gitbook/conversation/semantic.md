# Semantic Memory

Semantic memory uses vector embeddings to store and retrieve knowledge by meaning. It powers RAG (Retrieval-Augmented Generation) use cases.

## Overview

`SemanticMemory` stores text chunks as embeddings in a vector store (backed by pgvector or a compatible database). When the agent needs context, it retrieves the most semantically relevant chunks.

## Setup

Semantic memory requires the embeddings module and pgvector:

```bash
uv add "django-ai-sdk[pgvector]"
```

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        ...
    }
}

AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
    },
}
```

## Usage

```python
from djangosdk.memory.semantic import SemanticMemory

# Index documents
memory = SemanticMemory(namespace="docs")
memory.index("Django was released in 2005 by the Lawrence Journal-World.")
memory.index("Django uses a Model-View-Template architecture.")
memory.index("The Django ORM provides a Pythonic way to interact with databases.")

# Retrieve relevant context
results = memory.search("How does Django handle databases?", top_k=3)
for result in results:
    print(result.text, result.score)
```

## Integration with Agents

```python
from djangosdk.agents.base import Agent
from djangosdk.memory.semantic import SemanticMemory

class DocumentAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"

    def handle(self, prompt: str, **kwargs):
        mem = SemanticMemory(namespace="company-docs")
        context_chunks = mem.search(prompt, top_k=5)
        context = "\n\n".join(c.text for c in context_chunks)
        enriched_prompt = f"Relevant context:\n{context}\n\nQuestion: {prompt}"
        return super().handle(enriched_prompt, **kwargs)
```

## Embedding Models

Embeddings are generated via the `embed()` function. The default embedding model is `text-embedding-3-small`:

```python
AI_SDK = {
    "EMBEDDINGS": {
        "MODEL": "text-embedding-3-small",
        "PROVIDER": "openai",
    },
}
```

See [Embeddings](../embeddings.md) for full configuration options.
