from __future__ import annotations

from djangosdk.observability.base import AbstractObserver

__all__ = ["AbstractObserver", "get_observer", "setup_observability"]

_observer: AbstractObserver | None = None


def get_observer() -> AbstractObserver | None:
    """Return the active observability backend, or None if disabled."""
    return _observer


def setup_observability(settings: dict) -> None:
    """
    Instantiate the configured observability backend and wire it to Django signals.

    Called from ``AiSdkConfig.ready()``.
    """
    global _observer

    obs_cfg = settings.get("OBSERVABILITY", {})
    backend = obs_cfg.get("BACKEND")

    if not backend:
        return

    if backend == "langfuse":
        from djangosdk.observability.langfuse import LangfuseObserver

        _observer = LangfuseObserver(
            public_key=obs_cfg.get("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=obs_cfg.get("LANGFUSE_SECRET_KEY", ""),
            host=obs_cfg.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

    elif backend == "langsmith":
        from djangosdk.observability.langsmith import LangSmithObserver

        _observer = LangSmithObserver(
            api_key=obs_cfg.get("LANGCHAIN_API_KEY", ""),
            project=obs_cfg.get("LANGCHAIN_PROJECT", "default"),
        )

    elif backend == "opentelemetry":
        from djangosdk.observability.opentelemetry import OpenTelemetryObserver

        _observer = OpenTelemetryObserver(
            service_name=obs_cfg.get("OTEL_SERVICE_NAME", "django-ai-sdk")
        )
    else:
        return

    _connect_signals(_observer)


def _connect_signals(observer: AbstractObserver) -> None:
    """Connect Django signals to observer methods."""
    from django.dispatch import receiver

    from djangosdk.signals import (
        agent_completed,
        agent_failed,
        agent_started,
        cache_hit,
    )

    @receiver(agent_started)
    def _on_start(sender, agent, prompt, model, provider, **kwargs):
        observer.on_agent_start(
            agent=agent, prompt=prompt, model=model, provider=provider
        )

    @receiver(agent_completed)
    def _on_complete(sender, agent, response, model, provider, **kwargs):
        observer.on_agent_complete(
            agent=agent, response=response, model=model, provider=provider
        )

    @receiver(agent_failed)
    def _on_error(sender, agent, exception, model, provider, **kwargs):
        observer.on_agent_error(
            agent=agent, exception=exception, model=model, provider=provider
        )

    @receiver(cache_hit)
    def _on_cache_hit(sender, agent, cache_read_tokens, **kwargs):
        observer.on_cache_hit(cache_read_tokens=cache_read_tokens)
