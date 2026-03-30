from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable


def handoff(method: Callable) -> Callable:
    """
    Decorator for the routing/handoff pattern.

    Marks a method as a handoff router. The decorated method should return an
    Agent instance or ``None``. When a non-None agent is returned, the original
    prompt is forwarded to that agent's ``handle()`` / ``ahandle()`` call.

    Apply to a method on an Agent subclass. The agent's ``handle()`` call will
    detect the ``_is_handoff_router`` marker and delegate automatically when an
    agent is returned.

    Example::

        class RouterAgent(Agent):
            @handoff
            def route(self, intent: str):
                if intent == "billing":
                    return BillingAgent()
                return SupportAgent()

        router = RouterAgent()
        response = router.route("billing").handle("I need a refund")
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        target_agent = method(self, *args, **kwargs)
        return target_agent

    @functools.wraps(method)
    async def async_wrapper(self, *args, **kwargs):
        target_agent = method(self, *args, **kwargs)
        return target_agent

    # Preserve async-ness of the original method
    if asyncio.iscoroutinefunction(method):
        async_wrapper._is_handoff_router = True  # type: ignore[attr-defined]
        return async_wrapper
    else:
        wrapper._is_handoff_router = True  # type: ignore[attr-defined]
        return wrapper


async def parallel(*coros) -> list[Any]:
    """
    Run multiple agent coroutines in parallel and collect results.

    All coroutines are awaited concurrently via ``asyncio.gather``.

    Example::

        results = await parallel(
            SummaryAgent().ahandle("topic"),
            FactCheckAgent().ahandle("topic"),
        )
    """
    return await asyncio.gather(*coros)


def pipeline(*agents) -> "_Pipeline":
    """
    Chain agents so the output of one feeds as the input to the next.

    The first agent receives the original prompt. Each subsequent agent
    receives the ``.text`` attribute of the previous agent's ``AgentResponse``.
    The final ``AgentResponse`` is returned.

    Example::

        chain = pipeline(TranslateAgent(), SummarizeAgent(), FormatAgent())
        result = chain.handle("Raw text in French")
        print(result.text)
    """
    return _Pipeline(list(agents))


class _Pipeline:
    """Sequential pipeline that chains agent responses."""

    def __init__(self, agents: list) -> None:
        self._agents = agents

    def handle(self, prompt: str, **kwargs) -> Any:
        """Run the pipeline synchronously, feeding each agent's text to the next."""
        current = prompt
        last_response = None
        for agent in self._agents:
            last_response = agent.handle(current, **kwargs)
            current = last_response.text
        return last_response

    async def ahandle(self, prompt: str, **kwargs) -> Any:
        """Run the pipeline asynchronously."""
        current = prompt
        last_response = None
        for agent in self._agents:
            last_response = await agent.ahandle(current, **kwargs)
            current = last_response.text
        return last_response
