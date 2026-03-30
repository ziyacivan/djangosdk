from __future__ import annotations

from django_ai_sdk.agents.mixins.conversational import Conversational
from django_ai_sdk.agents.mixins.has_structured_output import HasStructuredOutput
from django_ai_sdk.agents.mixins.has_tools import HasTools
from django_ai_sdk.agents.mixins.promptable import Promptable
from django_ai_sdk.agents.mixins.reasoning import ReasoningMixin
from django_ai_sdk.providers.schemas import ReasoningConfig


class Agent(Promptable, ReasoningMixin, HasTools, HasStructuredOutput, Conversational):
    """
    Base class for all AI agents in django-ai-sdk.

    Override class attributes to configure the agent:

    Example::

        class SupportAgent(Agent):
            provider = "anthropic"
            model = "claude-3-5-haiku-20241022"
            system_prompt = "You are a helpful customer support agent."
            temperature = 0.3
            tools = [lookup_order, cancel_order]

        agent = SupportAgent()
        response = agent.handle("Where is my order?")
        print(response.text)
    """

    provider: str = ""
    """Provider name from AI_SDK.PROVIDERS. Defaults to AI_SDK.DEFAULT_PROVIDER."""

    model: str = ""
    """Model identifier. Defaults to AI_SDK.DEFAULT_MODEL."""

    system_prompt: str = ""
    """System prompt prepended to every request."""

    temperature: float = 0.7
    max_tokens: int = 2048
    reasoning: ReasoningConfig | None = None
    enable_cache: bool = True
    max_tool_iterations: int = 10
