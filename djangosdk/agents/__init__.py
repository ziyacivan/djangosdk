from djangosdk.agents.request import AgentRequest
from djangosdk.agents.response import AgentResponse, StreamChunk, ThinkingBlock, UsageInfo

__all__ = ["Agent", "AgentRequest", "AgentResponse", "StreamChunk", "ThinkingBlock", "UsageInfo"]


def __getattr__(name: str):
    if name == "Agent":
        from djangosdk.agents.base import Agent
        return Agent
    raise AttributeError(f"module 'djangosdk.agents' has no attribute {name!r}")
