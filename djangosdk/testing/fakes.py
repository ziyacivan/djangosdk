from __future__ import annotations

import contextlib
from typing import Any, AsyncIterator, Iterator
from unittest.mock import patch

from djangosdk.agents.request import AgentRequest
from djangosdk.agents.response import AgentResponse, StreamChunk, ThinkingBlock, UsageInfo
from djangosdk.providers.base import AbstractProvider


class FakeProvider(AbstractProvider):
    """
    An in-memory provider for unit tests. Never calls a real API.

    Example::

        fake = FakeProvider(text="Hello!", thinking="Let me think...")
        with override_ai_provider(fake):
            agent = MyAgent()
            response = agent.handle("Say hello.")
        assert response.text == "Hello!"
    """

    def __init__(
        self,
        text: str = "Fake response.",
        thinking: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        usage: UsageInfo | None = None,
        stream_chunks: list[str] | None = None,
    ) -> None:
        self._text = text
        self._thinking = thinking
        self._tool_calls = tool_calls or []
        self._usage = usage or UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        self._stream_chunks = stream_chunks or [text]
        self.calls: list[AgentRequest] = []

    def _make_response(self, request: AgentRequest) -> AgentResponse:
        self.calls.append(request)
        thinking_block = ThinkingBlock(content=self._thinking) if self._thinking else None
        return AgentResponse(
            text=self._text,
            model=request.model,
            provider=request.provider,
            usage=self._usage,
            thinking=thinking_block,
            tool_calls=self._tool_calls,
        )

    def complete(self, request: AgentRequest) -> AgentResponse:
        return self._make_response(request)

    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        return self._make_response(request)

    def stream(self, request: AgentRequest) -> Iterator[StreamChunk]:
        self.calls.append(request)
        for chunk_text in self._stream_chunks:
            yield StreamChunk(type="text_delta", text=chunk_text)
        yield StreamChunk(type="done", usage=self._usage)

    async def astream(self, request: AgentRequest) -> AsyncIterator[StreamChunk]:
        self.calls.append(request)
        for chunk_text in self._stream_chunks:
            yield StreamChunk(type="text_delta", text=chunk_text)
        yield StreamChunk(type="done", usage=self._usage)


class FakeAgent:
    """
    A pre-wired agent instance backed by FakeProvider.

    Useful when you want a complete agent without configuring settings.

    Example::

        agent = FakeAgent(text="Order found.")
        response = agent.handle("Find my order.")
        assert response.text == "Order found."
    """

    def __init__(self, **fake_kwargs) -> None:
        from djangosdk.agents.base import Agent

        class _Inner(Agent):
            provider = "fake"
            model = "fake-model"

        self._fake_provider = FakeProvider(**fake_kwargs)
        self._agent = _Inner()
        self._agent._fake_provider = self._fake_provider

    def handle(self, prompt: str, **kwargs) -> AgentResponse:
        with patch(
            "djangosdk.agents.mixins.promptable.Promptable._get_provider",
            return_value=self._fake_provider,
        ):
            return self._agent.handle(prompt, **kwargs)


@contextlib.contextmanager
def override_ai_provider(provider: AbstractProvider):
    """
    Context manager that replaces the provider used by registry.get() with
    the given provider instance for all agents in the block.
    """
    with patch(
        "djangosdk.providers.registry.registry.get",
        return_value=provider,
    ):
        yield provider
