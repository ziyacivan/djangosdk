---
name: debug-agent
description: >
  Diagnoses failing or misbehaving django-ai-sdk agents using a structured
  debug checklist and extended thinking. Invoke when the user says "my agent
  is not working", "debug my agent", "agent returns empty response", "tool is
  not being called", "agent loop not terminating", "agent is ignoring the
  system prompt", "why is my agent failing", or "trace an agent run".
triggers:
  - my agent is not working
  - debug my agent
  - agent returns empty response
  - tool is not being called
  - agent loop not terminating
  - agent is ignoring the system prompt
  - why is my agent failing
  - trace an agent run
  - agent not responding
  - agent keeps looping
  - agent returns wrong output
  - agent fails silently
  - inspect agent call log
---

# Debug a Failing Agent

You are diagnosing a misbehaving `django-ai-sdk` agent. Work through the checklist below **in order** — each category covers a distinct failure mode. Use extended thinking when multiple categories may interact.

## Step 1 — Gather Information

Before diagnosing, read the following from the user's codebase:
1. The Agent class definition (system_prompt, tools, model, provider, reasoning config)
2. Any `@tool` functions used by the agent
3. The AI_SDK settings block (provider + model config)
4. The call site — how `agent.handle()` / `agent.ahandle()` is called and what error or symptom occurs

Ask the user for the **exact symptom**:
- Empty response text?
- Exception (what type + message)?
- Tool not called despite being listed?
- Tool loop never stops?
- Wrong model being used?
- Streaming not working?

---

## Checklist: Common Failure Modes

### A. Provider / Model Configuration

**Symptom:** `ProviderNotFoundError`, `AuthenticationError`, or silent empty response.

```python
# Check: is the provider registered?
from djangosdk.providers.registry import ProviderRegistry
registry = ProviderRegistry.instance()
print(list(registry._providers.keys()))

# Check: is the API key set?
from djangosdk.conf import ai_settings
print(ai_settings.PROVIDERS)
```

**Common causes:**
- `AI_SDK["PROVIDERS"]` key doesn't match the `provider = "..."` set on the Agent class
- API key env var not set (returns empty string or `None`)
- Model name has a typo (e.g., `"gpt-4o"` vs `"gpt-4.1"`)
- Provider requires a specific litellm prefix (e.g., DeepSeek must be `"deepseek/deepseek-r1"`, not just `"deepseek-r1"`)

---

### B. Tool Schema Issues

**Symptom:** Tool is listed on the agent but never called by the model; or model calls tool but execution fails with `TypeError`.

```python
# Check: does the tool have the _tool decorator marker?
print(my_tool._is_tool)        # must be True
print(my_tool._tool_schema)    # inspect the generated JSON schema
```

**Common causes:**
- Missing type annotation on a parameter → parameter silently dropped from schema → model can't call it correctly
- `@tool` decorator not applied (function is listed in `tools = [...]` but decorator was forgotten)
- Tool function raises an exception internally — check if it's a Django ORM call without `sync_to_async` inside an async context
- Parameter name mismatch: model sends `{"city": "Istanbul"}` but tool expects `{"location": "Istanbul"}`

**Fix — add missing type annotations:**
```python
from djangosdk.tools.decorator import tool

@tool
def get_weather(city: str, unit: str = "celsius") -> str:  # all params typed
    """Return weather for a city."""
    ...
```

---

### C. Sync / Async Context Mismatch

**Symptom:** `SynchronousOnlyOperation`, `RuntimeError: no running event loop`, or Django ORM queries failing inside `ahandle()`.

**Common causes:**
- Calling `agent.handle()` (sync) inside an async Django view — use `agent.ahandle()` instead
- Calling `agent.ahandle()` without `await` — always `await agent.ahandle(...)`
- Django ORM queries inside an async tool — wrap with `sync_to_async`:

```python
from asgiref.sync import sync_to_async
from djangosdk.tools.decorator import tool

@tool
async def get_user_profile(user_id: int) -> str:
    """Fetch user profile from the database."""
    from myapp.models import UserProfile
    profile = await sync_to_async(UserProfile.objects.get)(id=user_id)
    return f"{profile.name}: {profile.bio}"
```

---

### D. Tool Loop Not Terminating

**Symptom:** Agent keeps calling tools indefinitely, response takes very long, or `MaxToolIterationsError` is raised.

**Cause:** The model never produces a final text response — it keeps requesting tool calls.

**Fix — check `max_tool_iterations`:**
```python
class MyAgent(Agent):
    max_tool_iterations = 10   # default; raise if your workflow needs more
```

**Debugging the loop:**
```python
from djangosdk.testing.fakes import FakeProvider

fake = FakeProvider()
# Simulate the exact tool call / response sequence
fake.set_response(text="", tool_calls=[{"name": "my_tool", "arguments": {"x": 1}}])
fake.set_response(text="", tool_calls=[{"name": "my_tool", "arguments": {"x": 2}}])
fake.set_response(text="Final answer.")  # termination response

agent = MyAgent()
agent._provider = fake
response = agent.handle("Do the thing.")
print(len(fake.call_log))  # should be 3
```

---

### E. Reasoning Model Configuration Conflicts

**Symptom:** Agent using `ReasoningConfig` returns empty `thinking` blocks, or provider returns `400 Bad Request`.

**Common causes:**
- `extended_thinking=True` set for a non-Anthropic model — only works with `claude-3-7-sonnet-20250219` and later
- `reasoning_effort="high"` sent to Anthropic — this parameter is only valid for OpenAI o3/o4-mini
- `thinking_budget` too high for the model's context window

**Fix:**
```python
from djangosdk.providers.schemas import ReasoningConfig

# Anthropic extended thinking
class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-sonnet-4-6"
    reasoning = ReasoningConfig(extended_thinking=True, thinking_budget=10000)

# OpenAI reasoning effort
class O3Agent(Agent):
    provider = "openai"
    model = "o3"
    reasoning = ReasoningConfig(effort="high")  # NOT extended_thinking

# DeepSeek R1
class DeepSeekAgent(Agent):
    provider = "deepseek"
    model = "deepseek/deepseek-r1"
    reasoning = ReasoningConfig(budget_tokens=8000)
```

---

### F. Structured Output Validation Failure

**Symptom:** `response.structured` is `None` despite `output_schema` being set; or `SchemaError` raised.

**Common causes:**
- The model returned prose instead of valid JSON — this happens with older models or when `system_prompt` doesn't reinforce the JSON requirement
- Pydantic model has a `required` field with no default and the model omitted it
- Provider doesn't support `response_format` (non-OpenAI models fall back to text extraction — check `StructuredOutput.extract_json_from_text()` parsing)

**Debugging:**
```python
from djangosdk.structured.output import StructuredOutput
from myapp.agents import SentimentAgent

schema = StructuredOutput.get_json_schema(SentimentAgent.output_schema)
print(schema)  # verify the schema looks correct

# Test JSON extraction from raw text
raw = '{"sentiment": "positive", "confidence": 0.9, "reasoning": "..."}'
result = StructuredOutput.validate(SentimentAgent.output_schema, raw)
print(result)
```

---

### G. Streaming Returns No Chunks

**Symptom:** `StreamingChatAPIView` returns `200 OK` but client receives no SSE events, or stream hangs.

**Common causes:**
- WSGI server (Gunicorn sync workers) doesn't support streaming — use async workers or switch to ASGI
- Client not setting `Accept: text/event-stream` header
- Nginx proxy buffering enabled — add `X-Accel-Buffering: no` or `proxy_buffering off`

**Server-side check:**
```python
# Verify stream yields chunks
from djangosdk.testing.fakes import FakeProvider

fake = FakeProvider()
fake.set_stream_chunks(["Hello", " world", "!"])
agent = MyAgent()
agent._provider = fake

chunks = list(agent.stream("Say hello."))
print([c.text for c in chunks])  # ["Hello", " world", "!"]
```

---

## Step 2 — Minimal Reproduction

Once the failure mode is identified, produce a minimal reproduction using `FakeProvider`:

```python
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import MyBrokenAgent

fake = FakeProvider()
fake.set_response("expected output")

agent = MyBrokenAgent()
agent._provider = fake

try:
    response = agent.handle("test prompt")
    print("text:", response.text)
    print("structured:", response.structured)
    print("calls:", len(fake.call_log))
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
```

## Step 3 — Verify Fix with `ai_sdk_check`

After applying a fix, run the management command to smoke-test the real provider:

```bash
python manage.py ai_sdk_check
```
