default_app_config = "django_ai_sdk.apps.AiSdkConfig"

__all__ = ["Agent", "tool", "ai_settings"]


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
    raise AttributeError(f"module 'django_ai_sdk' has no attribute {name!r}")
