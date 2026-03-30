from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ReasoningConfig:
    """Configuration for reasoning models (o3, Claude 3.7, DeepSeek R1, Gemini 2.5)."""

    effort: Literal["low", "medium", "high"] = "medium"
    """Reasoning effort for o3/o4-mini."""

    budget_tokens: int | None = None
    """Token budget for DeepSeek R1."""

    extended_thinking: bool = False
    """Enable extended thinking for Claude 3.7 Sonnet."""

    thinking_budget: int = 10000
    """Token budget for Claude 3.7 extended thinking."""

    stream_thinking: bool = False
    """Stream the reasoning/thinking process as thinking_delta SSE chunks."""


@dataclass
class ModelConfig:
    """Per-model configuration overrides."""

    max_tokens: int | None = None
    temperature: float | None = None
    reasoning: ReasoningConfig | None = None


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""

    name: str
    api_key: str = ""
    base_url: str = ""
    organization: str = ""
    api_version: str = ""
    default_model: str = ""
    default_reasoning_effort: Literal["low", "medium", "high"] = "medium"
    default_thinking_budget: int = 8000
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "ProviderConfig":
        known = {
            "api_key", "base_url", "organization", "api_version",
            "default_model", "default_reasoning_effort", "default_thinking_budget",
        }
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            name=name,
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            organization=data.get("organization", ""),
            api_version=data.get("api_version", ""),
            default_model=data.get("default_model", ""),
            default_reasoning_effort=data.get("default_reasoning_effort", "medium"),
            default_thinking_budget=data.get("default_thinking_budget", 8000),
            extra=extra,
        )
