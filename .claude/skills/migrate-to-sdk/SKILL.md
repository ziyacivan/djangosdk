---
name: migrate-to-sdk
description: >
  Migrates existing AI code (raw OpenAI/Anthropic SDK calls, LangChain chains,
  LlamaIndex pipelines) to django-ai-sdk patterns. Produces side-by-side
  before/after code with a migration checklist. Invoke when the user says
  "migrate from OpenAI SDK", "migrate from LangChain", "convert my existing agent",
  "replace openai.ChatCompletion", or "port to django-ai-sdk".
triggers:
  - migrate from OpenAI SDK
  - migrate from LangChain
  - convert my existing agent
  - replace openai.ChatCompletion
  - port to django-ai-sdk
  - convert to django-ai-sdk
  - migrate from Anthropic SDK
  - migrate from LlamaIndex
  - replace direct API calls
  - convert OpenAI code
  - migrate existing AI code
---

# Migrate Existing AI Code to django-ai-sdk

You are migrating existing AI code to `django-ai-sdk`. If the user pastes a screenshot or code snippet, analyze it and produce a side-by-side migration.

## Step 1 — Identify the Source Pattern

Detect which pattern the existing code uses:

| Source pattern | Migration target |
|---|---|
| `openai.chat.completions.create()` | `Agent.handle()` |
| `anthropic.messages.create()` | `Agent.handle()` with `provider="anthropic"` |
| LangChain `ChatOpenAI` + `LLMChain` | `Agent` subclass |
| LangChain `ConversationChain` + memory | `Agent` with `enable_conversation=True` |
| LangChain tool / agent executor | `Agent` with `tools = [...]` |
| LlamaIndex `QueryEngine` | `Agent` with `SemanticMemory` or RAG tool |
| Raw `requests.post` to OpenAI API | `Agent.handle()` |

---

## Migration Map: Raw OpenAI → django-ai-sdk

**Before (raw openai SDK):**
```python
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
    max_tokens=1024,
)
text = response.choices[0].message.content
```

**After (django-ai-sdk):**
```python
# myapp/agents.py
from djangosdk.agents.base import Agent


class AssistantAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = "You are a helpful assistant."
    temperature = 0.7
    max_tokens = 1024


# Usage:
agent = AssistantAgent()
response = agent.handle(prompt)
text = response.text
```

**What's removed:** manual API key passing, manual message list construction, manual response parsing.

---

## Migration Map: LangChain LLMChain → django-ai-sdk

**Before (LangChain):**
```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
prompt = ChatPromptTemplate.from_template("Summarize: {text}")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.invoke({"text": article_text})
summary = result["text"]
```

**After (django-ai-sdk):**
```python
from djangosdk.agents.base import Agent


class SummaryAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a summarization expert."
    temperature = 0.5


agent = SummaryAgent()
response = agent.handle(f"Summarize: {article_text}")
summary = response.text
```

---

## Migration Map: LangChain ConversationChain → django-ai-sdk

**Before (LangChain + memory):**
```python
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

llm = ChatOpenAI(model="gpt-4o")
memory = ConversationBufferMemory()
chain = ConversationChain(llm=llm, memory=memory)

chain.predict(input="Hello!")
chain.predict(input="What did I just say?")
```

**After (django-ai-sdk):**
```python
from djangosdk.agents.base import Agent


class ChatAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a helpful assistant."
    enable_conversation = True   # persists history in Django ORM


agent = ChatAgent()
response1 = agent.handle("Hello!", conversation_id="session-001")
response2 = agent.handle("What did I just say?", conversation_id="session-001")
```

**What's different:** history is persisted in the database across requests, not in-memory. Pass the same `conversation_id` from the client.

---

## Migration Map: LangChain Agent Executor → django-ai-sdk

**Before (LangChain tool-use):**
```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"It's sunny in {city}"

llm = ChatOpenAI(model="gpt-4o")
agent = create_openai_functions_agent(llm, [get_weather], prompt)
executor = AgentExecutor(agent=agent, tools=[get_weather])
result = executor.invoke({"input": "What's the weather in Istanbul?"})
```

**After (django-ai-sdk):**
```python
from djangosdk.agents.base import Agent
from djangosdk.tools.decorator import tool


@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"It's sunny in {city}"


class WeatherAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a helpful weather assistant."
    tools = [get_weather]


agent = WeatherAgent()
response = agent.handle("What's the weather in Istanbul?")
print(response.text)
```

**What's removed:** `AgentExecutor`, manual prompt construction, framework-specific `@tool` import. The dispatch loop is built into `Agent.handle()`.

---

## Migration Checklist

After migrating, verify each item:

- [ ] Replace `openai.OpenAI()` / `anthropic.Anthropic()` client instances with an `Agent` subclass
- [ ] Move `api_key` to `AI_SDK["PROVIDERS"]` in settings — remove from code
- [ ] Move `system` / `system_prompt` to `Agent.system_prompt` class attribute
- [ ] Move `model` to `Agent.model` class attribute
- [ ] Replace raw `@tool` (LangChain) with `djangosdk.tools.decorator.tool`
- [ ] Replace `ConversationBufferMemory` with `enable_conversation = True` + `conversation_id` kwarg
- [ ] Replace `LLMChain` pipelines with `pipeline(agent_a, agent_b, ...)` from `orchestration`
- [ ] Replace `AgentExecutor` with `Agent` + `tools = [...]`
- [ ] Replace manual streaming loops with `agent.stream()` or `StreamingChatAPIView`
- [ ] Replace manual structured output parsing with `output_schema = MyPydanticModel`
- [ ] Add `FakeProvider` tests — remove any tests that call real APIs

## What You Keep

- Custom business logic inside tool functions — just add `@tool` and type hints
- Pydantic models for structured output — attach as `output_schema`
- System prompts — paste directly into `system_prompt`
- Any prompt templates — inline them in `handle()` calls or in `system_prompt`
