from __future__ import annotations

from typing import Any

from django_ai_sdk.observability.base import AbstractObserver


class OpenTelemetryObserver(AbstractObserver):
    """
    OpenTelemetry observability backend.

    Requires: ``pip install opentelemetry-api opentelemetry-sdk``

    The caller is responsible for configuring an OTel exporter (OTLP, Jaeger, etc.)
    before the Django application starts. This observer only creates spans using
    the globally registered tracer provider.

    Configure in ``settings.py``::

        AI_SDK = {
            "OBSERVABILITY": {
                "BACKEND": "opentelemetry",
                "OTEL_SERVICE_NAME": "my-django-app",
            }
        }
    """

    def __init__(self, service_name: str = "django-ai-sdk") -> None:
        try:
            from opentelemetry import trace
        except ImportError as exc:
            raise ImportError(
                "opentelemetry-api is required. Run: pip install opentelemetry-api"
            ) from exc
        self._tracer = trace.get_tracer(service_name)
        self._spans: dict[int, Any] = {}

    def on_agent_start(
        self, agent: Any, prompt: str, model: str, provider: str, **kwargs
    ) -> Any:
        span = self._tracer.start_span(
            name=f"ai.agent.{agent.__class__.__name__}",
            attributes={
                "ai.provider": provider,
                "ai.model": model,
                "ai.prompt.length": len(prompt),
            },
        )
        self._spans[id(agent)] = span
        return span

    def on_agent_complete(
        self, agent: Any, response: Any, model: str, provider: str, **kwargs
    ) -> None:
        span = self._spans.pop(id(agent), None)
        if not span:
            return
        usage = getattr(response, "usage", None)
        if usage:
            span.set_attribute("ai.usage.prompt_tokens", usage.prompt_tokens)
            span.set_attribute(
                "ai.usage.completion_tokens", usage.completion_tokens
            )
            span.set_attribute("ai.usage.total_tokens", usage.total_tokens)
        span.end()

    def on_agent_error(
        self,
        agent: Any,
        exception: Exception,
        model: str,
        provider: str,
        **kwargs,
    ) -> None:
        from opentelemetry.trace import StatusCode

        span = self._spans.pop(id(agent), None)
        if not span:
            return
        span.set_status(StatusCode.ERROR, str(exception))
        span.record_exception(exception)
        span.end()

    def on_tool_call(
        self, tool_name: str, arguments: dict, result: Any, **kwargs
    ) -> None:
        with self._tracer.start_as_current_span(
            f"ai.tool.{tool_name}",
            attributes={
                "ai.tool.name": tool_name,
                "ai.tool.arguments": str(arguments),
            },
        ):
            pass
