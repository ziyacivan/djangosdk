from __future__ import annotations

import pytest
from django_ai_sdk.agents.base import Agent
from django_ai_sdk.orchestration.patterns import handoff, pipeline, parallel
from django_ai_sdk.testing import FakeProvider, override_ai_provider


class AgentA(Agent):
    provider = "fake"
    model = "fake-model"


class AgentB(Agent):
    provider = "fake"
    model = "fake-model"


# --- pipeline ---

def test_pipeline_chains_two_agents():
    a_fake = FakeProvider(text="step-one")
    b_fake = FakeProvider(text="step-two")

    a = AgentA()
    b = AgentB()

    original_get = None

    # Patch each agent's _get_provider independently
    from unittest.mock import patch

    with patch.object(AgentA, "_get_provider", return_value=a_fake), \
         patch.object(AgentB, "_get_provider", return_value=b_fake):
        chain = pipeline(a, b)
        result = chain.handle("start")

    assert result.text == "step-two"
    # B received the output of A as its prompt
    b_prompts = [m["content"] for req in b_fake.calls for m in req.messages if m["role"] == "user"]
    assert "step-one" in b_prompts


@pytest.mark.asyncio
async def test_pipeline_ahandle():
    from unittest.mock import patch

    a_fake = FakeProvider(text="async-one")
    b_fake = FakeProvider(text="async-two")

    a = AgentA()
    b = AgentB()

    with patch.object(AgentA, "_get_provider", return_value=a_fake), \
         patch.object(AgentB, "_get_provider", return_value=b_fake):
        chain = pipeline(a, b)
        result = await chain.ahandle("start async")

    assert result.text == "async-two"


# --- parallel ---

@pytest.mark.asyncio
async def test_parallel_runs_both_agents():
    from unittest.mock import patch

    fake_a = FakeProvider(text="result-a")
    fake_b = FakeProvider(text="result-b")

    a = AgentA()
    b = AgentB()

    with patch.object(AgentA, "_get_provider", return_value=fake_a), \
         patch.object(AgentB, "_get_provider", return_value=fake_b):
        results = await parallel(a.ahandle("topic"), b.ahandle("topic"))

    texts = [r.text for r in results]
    assert "result-a" in texts
    assert "result-b" in texts


# --- handoff ---

def test_handoff_decorator_returns_target_agent():
    class RouterAgent(Agent):
        provider = "fake"
        model = "fake-model"

        @handoff
        def route(self, intent: str):
            if intent == "billing":
                return AgentB()
            return AgentA()

    router = RouterAgent()
    target = router.route("billing")
    assert isinstance(target, AgentB)

    target2 = router.route("other")
    assert isinstance(target2, AgentA)


def test_handoff_marks_function():
    @handoff
    def router(self, x):
        return AgentA()

    assert getattr(router, "_is_handoff_router", False) is True
