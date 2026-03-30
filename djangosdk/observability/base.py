from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractObserver(ABC):
    """Base class for all observability backends."""

    @abstractmethod
    def on_agent_start(
        self, agent: Any, prompt: str, model: str, provider: str, **kwargs
    ) -> Any:
        """Called when an agent begins processing. May return a span/trace handle."""

    @abstractmethod
    def on_agent_complete(
        self, agent: Any, response: Any, model: str, provider: str, **kwargs
    ) -> None:
        """Called when an agent successfully completes."""

    @abstractmethod
    def on_agent_error(
        self,
        agent: Any,
        exception: Exception,
        model: str,
        provider: str,
        **kwargs,
    ) -> None:
        """Called when an agent raises an exception."""

    def on_tool_call(
        self, tool_name: str, arguments: dict, result: Any, **kwargs
    ) -> None:
        """Called after a tool is executed. Optional hook."""

    def on_cache_hit(self, cache_read_tokens: int, **kwargs) -> None:
        """Called on a prompt cache hit. Optional hook."""
