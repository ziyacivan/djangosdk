from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbstractMemoryStore(ABC):
    """Base class for all memory store backends."""

    @abstractmethod
    def add(self, key: str, value: Any, **kwargs) -> None:
        """Store a memory entry."""

    @abstractmethod
    def get(self, key: str, **kwargs) -> Any:
        """Retrieve a memory entry by key."""

    @abstractmethod
    def list(self, **kwargs) -> list[dict]:
        """List all memory entries."""

    @abstractmethod
    def clear(self, **kwargs) -> None:
        """Clear all memory entries."""

    def as_context(self) -> str:
        """Render memory as a plain-text context string for injection into a system prompt."""
        items = self.list()
        if not items:
            return ""
        lines = ["## Memory", ""]
        for item in items:
            lines.append(f"- {item.get('key', '')}: {item.get('value', '')}")
        return "\n".join(lines)
