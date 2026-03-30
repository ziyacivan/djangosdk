from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base for class-based tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool."""

    def to_schema(self) -> dict:
        """Return OpenAI-compatible tool schema."""
        raise NotImplementedError(
            f"Tool {self.__class__.__name__} must implement to_schema()"
        )
