---
name: scaffold-memory
description: >
  Scaffolds EpisodicMemory (DB-backed ordered recall) or SemanticMemory
  (pgvector embedding search) backends and attaches them to an Agent.
  Invoke when the user says "add memory to my agent", "set up episodic memory",
  "set up semantic memory", "give my agent long-term memory", "use BaseMemory",
  "store and retrieve memories", or "make my agent remember things".
triggers:
  - add memory to my agent
  - set up episodic memory
  - set up semantic memory
  - give my agent long-term memory
  - use BaseMemory
  - store and retrieve memories
  - make my agent remember things
  - agent memory
  - long-term memory
  - remember facts
  - semantic search memory
  - episodic memory backend
---

# Scaffold Agent Memory

You are adding persistent memory to a `django-ai-sdk` agent. Two backends are available — choose based on the retrieval pattern needed.

## Step 1 — Choose the Right Memory Backend

| Backend | Retrieval | Requires |
|---|---|---|
| `EpisodicMemory` | Key-based, FIFO-evicted, ordered | `djangosdk` ORM only |
| `SemanticMemory` | Cosine similarity vector search | `pgvector`, PostgreSQL |

**Episodic** = "Remember the last N facts" (user preferences, session context)
**Semantic** = "Find the most relevant memory for this query" (knowledge base, RAG)

## Step 2a — Episodic Memory

### Attach to Agent

```python
# myapp/agents.py
from djangosdk.agents.base import Agent
from djangosdk.memory.episodic import EpisodicMemory


class PersonalAssistant(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a personal assistant."

    # Stores up to 50 key-value facts, evicts oldest FIFO
    episodic_memory = EpisodicMemory(max_episodes=50, namespace="personal_assistant")
```

### Store and Retrieve Facts

```python
agent = PersonalAssistant()

# Store facts
agent.episodic_memory.add("user_name", "Alice")
agent.episodic_memory.add("preferred_language", "Turkish")

# Retrieve a fact
name = agent.episodic_memory.get("user_name")  # "Alice"

# Inject all facts into a prompt as context
context = agent.episodic_memory.as_context()
# Returns:
# ## Episodic Memory
# Previous facts and experiences:
# - user_name: Alice
# - preferred_language: Turkish

# Use context in handle():
response = agent.handle(f"{context}\n\nWhat language should I use?")
```

### Async Support

```python
await agent.episodic_memory.aadd("user_timezone", "Europe/Istanbul")
name = await agent.episodic_memory.aget("user_name")
context = await agent.episodic_memory.alist()
```

## Step 2b — Semantic Memory

### Install Dependencies

```bash
pip install pgvector psycopg2-binary
```

### Add `pgvector` Extension to PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Configure PostgreSQL in Settings

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mydb",
        "USER": "myuser",
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": "localhost",
    }
}
```

### Attach to Agent

```python
from djangosdk.agents.base import Agent
from djangosdk.memory.semantic import SemanticMemory


class ResearchAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a research assistant."

    semantic_memory = SemanticMemory(
        namespace="research",
        max_results=5,
        embedding_model="text-embedding-3-small",
        embedding_provider="openai",
    )
```

### Store and Search

```python
agent = ResearchAgent()

# Store knowledge
agent.semantic_memory.add("quantum computing", "A computation paradigm using quantum mechanics")
agent.semantic_memory.add("machine learning", "Algorithms that learn from data")

# Semantic similarity search (not exact match)
results = agent.semantic_memory.search("quantum physics", top_k=3)
# results = [{"key": "quantum computing", "value": "...", "similarity": 0.92}, ...]

# Inject top-k relevant memories as prompt context
context = agent.semantic_memory.as_context()

response = agent.handle(f"{context}\n\nExplain quantum entanglement.")
```

## Step 3 — Migrations

Both backends rely on Django ORM. Run migrations after adding `djangosdk` to `INSTALLED_APPS`:

```bash
python manage.py migrate djangosdk
```

For `SemanticMemory`, the `SemanticMemoryEntry` model requires the `pgvector` extension active in your PostgreSQL database before migration.

## Step 4 — Inject Memory Context into System Prompt

The cleanest pattern is to override `handle()` to prepend memory context:

```python
from djangosdk.agents.base import Agent
from djangosdk.agents.response import AgentResponse
from djangosdk.memory.episodic import EpisodicMemory


class ContextAwareAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a helpful assistant."
    episodic_memory = EpisodicMemory(max_episodes=100, namespace="context_aware")

    def handle(self, prompt: str, **kwargs) -> AgentResponse:
        memory_context = self.episodic_memory.as_context()
        if memory_context:
            enriched_prompt = f"{memory_context}\n\n{prompt}"
        else:
            enriched_prompt = prompt
        return super().handle(enriched_prompt, **kwargs)
```

## Step 5 — Namespace Isolation (Multi-Tenant)

Use `namespace` to isolate memory per user or session:

```python
def get_agent_for_user(user_id: str) -> Agent:
    agent = PersonalAssistant()
    agent.episodic_memory = EpisodicMemory(
        max_episodes=50,
        namespace=f"user_{user_id}",
    )
    return agent
```

## Step 6 — Custom Memory Backend

To implement a custom backend (Redis, S3, etc.), subclass `AbstractMemoryStore`:

```python
from djangosdk.memory.base import AbstractMemoryStore


class RedisMemoryStore(AbstractMemoryStore):
    def __init__(self, redis_client, namespace: str = "default"):
        self._redis = redis_client
        self._ns = namespace

    def add(self, key: str, value, **kwargs) -> None:
        self._redis.hset(self._ns, key, str(value))

    def get(self, key: str, **kwargs):
        return self._redis.hget(self._ns, key)

    def list(self, **kwargs) -> list[dict]:
        data = self._redis.hgetall(self._ns)
        return [{"key": k, "value": v} for k, v in data.items()]

    def clear(self, **kwargs) -> None:
        self._redis.delete(self._ns)
```

## Step 7 — Test Memory

```python
import pytest
from unittest.mock import patch
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import PersonalAssistant


@pytest.mark.django_db
def test_episodic_memory_stores_and_retrieves():
    agent = PersonalAssistant()
    agent.episodic_memory.add("language", "Turkish")
    result = agent.episodic_memory.get("language")
    assert result == "Turkish"


@pytest.mark.django_db
def test_memory_context_is_injected_into_prompt():
    fake = FakeProvider()
    fake.set_response("I'll respond in Turkish.")

    agent = PersonalAssistant()
    agent._provider = fake
    agent.episodic_memory.add("language", "Turkish")

    agent.handle("What language should I use?")

    from djangosdk.testing.assertions import assert_prompt_sent
    assert_prompt_sent(fake, "Turkish")
```
