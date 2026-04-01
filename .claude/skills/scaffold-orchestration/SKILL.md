---
name: scaffold-orchestration
description: >
  Scaffolds multi-agent orchestration patterns (pipeline, parallel, handoff/router)
  from the djangosdk.orchestration module. Invoke when the user says "create a
  multi-agent pipeline", "set up agent orchestration", "build a supervisor agent",
  "create an evaluator agent", "chain agents together", "fan out to parallel agents",
  or "build a router agent".
triggers:
  - create a multi-agent pipeline
  - set up agent orchestration
  - build a supervisor agent
  - create an evaluator agent
  - chain agents together
  - fan out to parallel agents
  - build a router agent
  - multi-agent workflow
  - orchestrate agents
  - parallel agent execution
  - pipeline agents
  - handoff between agents
---

# Scaffold Multi-Agent Orchestration

You are wiring together multiple `django-ai-sdk` agents using the `orchestration` module. Three patterns are available — choose based on the coordination need.

## Step 1 — Choose the Right Pattern

| Pattern | Function / Class | Use when |
|---|---|---|
| **Pipeline** | `pipeline(*agents)` | Output of one agent feeds the next |
| **Parallel** | `await parallel(*coros)` | Multiple agents run independently on the same input |
| **Handoff / Router** | `@handoff` decorator | One agent routes to a specialist based on intent |

---

## Pattern A — Pipeline (Sequential Chain)

Each agent receives the previous agent's `.text` as its input prompt.

```python
# myapp/orchestration.py
from djangosdk.orchestration.patterns import pipeline
from myapp.agents import TranslateAgent, SummarizeAgent, FormatAgent

# Create the pipeline once
translate_then_summarize = pipeline(
    TranslateAgent(),   # Step 1: translate to English
    SummarizeAgent(),   # Step 2: summarize the translation
    FormatAgent(),      # Step 3: format as bullet points
)

# Sync call
result = translate_then_summarize.handle("Gelen müşteri şikayetleri...")
print(result.text)

# Async call
result = await translate_then_summarize.ahandle("Gelen müşteri şikayetleri...")
```

**When to use:** ETL-style workflows, multi-stage content processing, translation + refinement.

---

## Pattern B — Parallel Fan-Out

All agents run concurrently on the same prompt. Results are collected as a list.

```python
import asyncio
from djangosdk.orchestration.patterns import parallel
from myapp.agents import SummaryAgent, FactCheckAgent, SentimentAgent


async def analyze_article(text: str):
    results = await parallel(
        SummaryAgent().ahandle(text),
        FactCheckAgent().ahandle(text),
        SentimentAgent().ahandle(text),
    )
    summary, fact_check, sentiment = results
    return {
        "summary": summary.text,
        "fact_check": fact_check.text,
        "sentiment": sentiment.structured,
    }
```

**When to use:** Independent analyses of the same input, A/B comparison, ensemble approaches.

---

## Pattern C — Handoff / Router

A router agent inspects the prompt and delegates to a specialist.

```python
# myapp/agents.py
from djangosdk.agents.base import Agent
from djangosdk.orchestration.patterns import handoff


class BillingAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a billing specialist. Help with invoices and payments."


class TechSupportAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "You are a technical support engineer. Help with product issues."


class RouterAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = (
        "Classify the user's intent as 'billing' or 'tech_support'. "
        "Respond with only one of those two words."
    )

    @handoff
    def route(self, prompt: str) -> Agent:
        """Route to the correct specialist agent."""
        # Ask this agent to classify the intent
        classification = self.handle(prompt).text.strip().lower()

        if "billing" in classification:
            return BillingAgent()
        return TechSupportAgent()


# Usage:
router = RouterAgent()
specialist = router.route("I can't log into my account")
response = specialist.handle("I can't log into my account")
print(response.text)
```

**When to use:** Customer support triage, intent-based routing, multi-domain assistants.

---

## Pattern D — Evaluator-Optimizer Loop

An evaluator agent scores the output of a worker agent and loops until quality is acceptable.

```python
from djangosdk.agents.base import Agent
from djangosdk.orchestration.evaluator import Evaluator


class WriterAgent(Agent):
    model = "claude-sonnet-4-6"
    system_prompt = "Write a professional blog post based on the given topic."


class QualityEvaluator(Evaluator):
    model = "claude-sonnet-4-6"
    system_prompt = (
        "Rate the quality of the blog post from 1-10. "
        "Respond with JSON: {\"score\": <int>, \"feedback\": \"<string>\"}. "
        "Score 8 or above means acceptable."
    )
    pass_threshold = 8       # score >= 8 = pass
    max_iterations = 3       # stop after 3 revision attempts


# Usage:
writer = WriterAgent()
evaluator = QualityEvaluator(worker=writer)

result = evaluator.run("Write about the impact of AI on software development")
print(result.text)
print(f"Accepted after {result.iterations} iteration(s)")
```

---

## Full Example: Article Processing Pipeline with Parallel Analysis

```python
# myapp/workflows.py
import asyncio
from djangosdk.orchestration.patterns import pipeline, parallel
from myapp.agents import (
    CleanupAgent,
    TranslateAgent,
    SummaryAgent,
    FactCheckAgent,
)


async def process_article(raw_text: str) -> dict:
    # Step 1: Clean + translate (sequential)
    prep = pipeline(CleanupAgent(), TranslateAgent())
    prepared = await prep.ahandle(raw_text)

    # Step 2: Analyze in parallel
    summary, fact_check = await parallel(
        SummaryAgent().ahandle(prepared.text),
        FactCheckAgent().ahandle(prepared.text),
    )

    return {
        "prepared": prepared.text,
        "summary": summary.text,
        "fact_check": fact_check.text,
    }
```

---

## Test Orchestration Patterns

Use `FakeProvider` or `FakeAgent` to test without real API calls:

```python
import pytest
from unittest.mock import MagicMock
from djangosdk.agents.response import AgentResponse
from djangosdk.orchestration.patterns import pipeline


def make_fake_agent(response_text: str):
    agent = MagicMock()
    fake_response = MagicMock(spec=AgentResponse)
    fake_response.text = response_text
    agent.handle.return_value = fake_response
    return agent


def test_pipeline_passes_output_as_input():
    agent_a = make_fake_agent("translated text")
    agent_b = make_fake_agent("summarized text")

    chain = pipeline(agent_a, agent_b)
    result = chain.handle("original text")

    agent_a.handle.assert_called_once_with("original text")
    agent_b.handle.assert_called_once_with("translated text")  # output of A
    assert result.text == "summarized text"


@pytest.mark.asyncio
async def test_parallel_runs_all_agents():
    import asyncio

    async def fake_ahandle(text):
        resp = MagicMock()
        resp.text = f"processed: {text}"
        return resp

    agent_a = MagicMock()
    agent_a.ahandle = fake_ahandle
    agent_b = MagicMock()
    agent_b.ahandle = fake_ahandle

    from djangosdk.orchestration.patterns import parallel
    results = await parallel(
        agent_a.ahandle("topic"),
        agent_b.ahandle("topic"),
    )
    assert len(results) == 2
    assert results[0].text == "processed: topic"
```
