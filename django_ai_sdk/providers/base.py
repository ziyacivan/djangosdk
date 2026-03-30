from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncIterator, Iterator

if TYPE_CHECKING:
    from django_ai_sdk.agents.request import AgentRequest
    from django_ai_sdk.agents.response import AgentResponse, StreamChunk


class AbstractProvider(ABC):
    """Base class for all AI providers."""

    @abstractmethod
    def complete(self, request: AgentRequest) -> AgentResponse:
        """Synchronous, non-streaming completion."""

    @abstractmethod
    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        """Asynchronous, non-streaming completion."""

    @abstractmethod
    def stream(self, request: AgentRequest) -> Iterator[StreamChunk]:
        """Synchronous streaming completion."""

    @abstractmethod
    async def astream(self, request: AgentRequest) -> AsyncIterator[StreamChunk]:
        """Asynchronous streaming completion."""
