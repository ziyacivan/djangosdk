default_app_config = "django_ai_sdk.apps.AiSdkConfig"

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
        from django_ai_sdk.agents.base import Agent
        return Agent
    if name == "tool":
        from django_ai_sdk.tools.decorator import tool
        return tool
    if name == "ai_settings":
        from django_ai_sdk.conf import ai_settings
        return ai_settings
    if name in ("embed", "aembed"):
        import django_ai_sdk.embeddings as _emb
        return getattr(_emb, name)
    if name in ("mcp_tool", "mcp_resource"):
        import django_ai_sdk.mcp.decorators as _mcp
        return getattr(_mcp, name)
    if name == "EpisodicMemory":
        from django_ai_sdk.memory.episodic import EpisodicMemory
        return EpisodicMemory
    if name == "cost_report":
        from django_ai_sdk.analytics.cost import cost_report
        return cost_report
    if name == "ai_rate_limit":
        from django_ai_sdk.ratelimit.decorators import ai_rate_limit
        return ai_rate_limit
    raise AttributeError(f"module 'django_ai_sdk' has no attribute {name!r}")
