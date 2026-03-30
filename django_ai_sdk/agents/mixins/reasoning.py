from __future__ import annotations

from django_ai_sdk.providers.schemas import ReasoningConfig


class ReasoningMixin:
    """
    Mixin that adds reasoning model configuration to an Agent.

    Set ``reasoning`` on the agent class to enable o3/o4-mini, Claude 3.7
    extended thinking, or DeepSeek R1 budget token control.

    Example::

        class MathAgent(Agent):
            model = "o3"
            reasoning = ReasoningConfig(effort="high")
    """

    reasoning: ReasoningConfig | None = None
