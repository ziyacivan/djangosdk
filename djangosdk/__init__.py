__version__ = "0.1.1"

default_app_config = "djangosdk.apps.AiSdkConfig"

__all__ = [
    # Phase 1
    "Agent",
    "tool",
    "ai_settings",
    # Phase 2
    "embed",
    "aembed",
    "mcp_tool",
    "mcp_resource",
    "EpisodicMemory",
    "cost_report",
    "ai_rate_limit",
]


def __getattr__(name: str):
    if name == "Agent":
        from djangosdk.agents.base import Agent
        return Agent
    if name == "tool":
        from djangosdk.tools.decorator import tool
        return tool
    if name == "ai_settings":
        from djangosdk.conf import ai_settings
        return ai_settings
    if name in ("embed", "aembed"):
        import djangosdk.embeddings as _emb
        return getattr(_emb, name)
    if name in ("mcp_tool", "mcp_resource"):
        import djangosdk.mcp.decorators as _mcp
        return getattr(_mcp, name)
    if name == "EpisodicMemory":
        from djangosdk.memory.episodic import EpisodicMemory
        return EpisodicMemory
    if name == "cost_report":
        from djangosdk.analytics.cost import cost_report
        return cost_report
    if name == "ai_rate_limit":
        from djangosdk.ratelimit.decorators import ai_rate_limit
        return ai_rate_limit
    raise AttributeError(f"module 'djangosdk' has no attribute {name!r}")
