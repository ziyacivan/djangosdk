from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.agents.response import AgentResponse, StreamChunk, ThinkingBlock, UsageInfo

__all__ = ["Agent", "AgentRequest", "AgentResponse", "StreamChunk", "ThinkingBlock", "UsageInfo"]


def __getattr__(name: str):
    if name == "Agent":
        from django_ai_sdk.agents.base import Agent
        return Agent
    raise AttributeError(f"module 'django_ai_sdk.agents' has no attribute {name!r}")
