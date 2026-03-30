from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UsageInfo:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass
class ThinkingBlock:
    """Extended thinking content from reasoning models."""

    content: str
    model: str = ""


@dataclass
class StreamChunk:
    """A single chunk emitted during streaming."""

    type: str
    """text_delta | thinking_delta | tool_call | done"""

    text: str = ""
    thinking: bool = False
    tool_call: dict[str, Any] | None = None
    usage: UsageInfo | None = None


@dataclass
class AgentResponse:
    """The unified response returned by every agent handle/stream call."""

    text: str
    """Final assistant text content."""

    model: str = ""
    provider: str = ""
    usage: UsageInfo = field(default_factory=UsageInfo)
    thinking: ThinkingBlock | None = None
    structured: Any = None
    """Validated Pydantic instance when output_schema is set."""

    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: Any = None
    """Raw litellm response object."""

    conversation_id: str | None = None
