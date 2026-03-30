from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_ai_sdk.providers.schemas import ReasoningConfig


@dataclass
class AgentRequest:
    """Encapsulates all data sent to a provider for a single completion."""

    messages: list[dict[str, Any]]
    """Full message history in OpenAI-compatible format."""

    model: str = ""
    provider: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[dict[str, Any]] = field(default_factory=list)
    """JSON schema tool definitions."""

    output_schema: dict[str, Any] | None = None
    """Pydantic-derived JSON schema for structured output."""

    reasoning: ReasoningConfig | None = None
    enable_cache: bool = True
    stream: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
