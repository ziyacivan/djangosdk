from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any


# Approximate cost per 1M tokens (USD) — update as pricing changes
_COST_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.5": {"input": 75.00, "output": 150.00},
    "o3": {"input": 10.00, "output": 40.00},
    "o4-mini": {"input": 1.10, "output": 4.40},
    "claude-3-7-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "mistral-medium-3": {"input": 0.40, "output": 2.00},
    "grok-3": {"input": 3.00, "output": 15.00},
    "grok-3-fast": {"input": 0.60, "output": 3.00},
}


def _lookup_cost(model: str) -> dict[str, float]:
    model_lower = model.lower()
    for key, costs in _COST_TABLE.items():
        if key in model_lower:
            return costs
    return {"input": 0.0, "output": 0.0}


def calculate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> Decimal:
    """Estimate cost in USD for a single call."""
    costs = _lookup_cost(model)
    usd = (prompt_tokens * costs["input"] + completion_tokens * costs["output"]) / 1_000_000
    return Decimal(str(round(usd, 8)))


def cost_report(days: int = 7) -> dict[str, Any]:
    """
    Return a cost summary broken down by provider for the last ``days`` days.

    Example::

        from django_ai_sdk.analytics import cost_report

        report = cost_report(days=7)
        # {"openai": {"total_usd": 4.23, "total_tokens": 1_200_000}, ...}
    """
    from django.utils import timezone

    from django_ai_sdk.models.message import Message

    since = timezone.now() - datetime.timedelta(days=days)
    messages = Message.objects.filter(created_at__gte=since, role="assistant")

    report: dict[str, dict[str, Any]] = {}

    for msg in messages.iterator():
        conv = msg.conversation
        provider = getattr(conv, "provider", "unknown") or "unknown"

        if provider not in report:
            report[provider] = {"total_usd": Decimal("0"), "total_tokens": 0}

        if msg.cost_usd:
            report[provider]["total_usd"] += msg.cost_usd
        elif msg.prompt_tokens is not None and msg.completion_tokens is not None:
            estimated = calculate_cost(
                getattr(conv, "model", ""),
                msg.prompt_tokens,
                msg.completion_tokens,
            )
            report[provider]["total_usd"] += estimated

        total_tokens = (msg.prompt_tokens or 0) + (msg.completion_tokens or 0)
        report[provider]["total_tokens"] += total_tokens

    # Convert Decimal → float for JSON-serializable output
    return {
        provider: {
            "total_usd": float(data["total_usd"]),
            "total_tokens": data["total_tokens"],
        }
        for provider, data in report.items()
    }
