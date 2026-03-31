# 02 — Tool-Calling Agent

A customer support bot that uses the `@tool` decorator to give the agent real capabilities.

## What it demonstrates

- `HasTools` mixin and `@tool` decorator
- Multi-tool dispatch loop (agent picks the right tool automatically)
- Tool results fed back into the conversation
- Accessing `response.tool_calls` to see which tools were used

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## Try these prompts

- `"Where is order ORD-001?"`
- `"Cancel order ORD-002, I changed my mind"`
- `"Will stormy weather delay my order ORD-001 in London?"`

## Key files

| File | Purpose |
|------|---------|
| `support/agents.py` | `SupportAgent` with 3 `@tool` methods |
| `support/views.py` | JSON endpoint returning `text` + `tools_called` |

## How the tool loop works

1. User message + tool schemas → Anthropic
2. Model returns `tool_calls` → SDK executes each tool
3. Tool results appended to message history
4. Model generates final answer
5. `response.tool_calls` shows what was called

djangosdk handles steps 2–4 automatically.
