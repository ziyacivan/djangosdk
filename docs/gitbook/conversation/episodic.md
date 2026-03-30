# Episodic Memory

Episodic memory is a higher-level abstraction over conversation persistence. It stores discrete episodes (events, facts, interactions) and retrieves them on demand.

## Overview

While `Conversational` manages the raw message history for a single conversation, `EpisodicMemory` stores structured memories that can be retrieved across conversations — e.g., a user's preferences, past interactions, or key facts.

## Usage

```python
from djangosdk.memory.episodic import EpisodicMemory

# Store a memory
memory = EpisodicMemory(agent_id="support-agent", user_id=str(request.user.id))
memory.remember("User prefers email notifications over SMS.")
memory.remember("User's account tier is Pro.")

# Retrieve memories
context = memory.recall(limit=10)
# Returns: list of relevant memory strings

# Use in an agent
class SupportAgent(Agent):
    system_prompt = "You are a support agent."

    def handle_with_memory(self, prompt: str, user_id: str):
        mem = EpisodicMemory(agent_id="support", user_id=user_id)
        memories = mem.recall()
        memory_context = "\n".join(memories)
        enriched_prompt = f"User context:\n{memory_context}\n\nUser: {prompt}"
        return self.handle(enriched_prompt)
```

## When to Use Episodic Memory

- Storing user preferences across sessions
- Tracking key facts about a customer or project
- Remembering previous decisions or outcomes
- Building a personal assistant that improves over time

## vs. Conversational History

| | `Conversational` | `EpisodicMemory` |
|---|---|---|
| Scope | Per-conversation | Cross-conversation |
| Format | Raw messages (role/content) | Structured facts/strings |
| Storage | `Message` ORM model | `EpisodicMemory` ORM model |
| Retrieval | Ordered by time | Retrieved by relevance or recency |
