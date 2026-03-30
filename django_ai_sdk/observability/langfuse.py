from __future__ import annotations

from typing import Any

from django_ai_sdk.observability.base import AbstractObserver


class LangfuseObserver(AbstractObserver):
    """
    Langfuse observability backend.

    Requires: ``pip install langfuse``

    Configure in ``settings.py``::

        AI_SDK = {
            "OBSERVABILITY": {
                "BACKEND": "langfuse",
                "LANGFUSE_PUBLIC_KEY": env("LANGFUSE_PUBLIC_KEY"),
                "LANGFUSE_SECRET_KEY": env("LANGFUSE_SECRET_KEY"),
                "LANGFUSE_HOST": "https://cloud.langfuse.com",
            }
        }
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
    ) -> None:
        try:
            from langfuse import Langfuse
        except ImportError as exc:
            raise ImportError(
                "langfuse is required. Run: pip install langfuse"
            ) from exc
        self._client = Langfuse(
            public_key=public_key, secret_key=secret_key, host=host
        )
        self._traces: dict[int, dict] = {}

    def on_agent_start(
        self, agent: Any, prompt: str, model: str, provider: str, **kwargs
    ) -> Any:
        trace = self._client.trace(
            name=f"{agent.__class__.__name__}.handle",
            input=prompt,
            metadata={"provider": provider, "model": model},
        )
        span = trace.generation(
            name="completion",
            model=model,
            input=[{"role": "user", "content": prompt}],
        )
        self._traces[id(agent)] = {"trace": trace, "span": span}
        return trace

    def on_agent_complete(
        self, agent: Any, response: Any, model: str, provider: str, **kwargs
    ) -> None:
        entry = self._traces.pop(id(agent), None)
        if not entry:
            return
        usage = getattr(response, "usage", None)
        entry["span"].end(
            output=getattr(response, "text", ""),
            usage={
                "input": usage.prompt_tokens if usage else 0,
                "output": usage.completion_tokens if usage else 0,
                "total": usage.total_tokens if usage else 0,
            },
        )
        entry["trace"].update(output=getattr(response, "text", ""))

    def on_agent_error(
        self,
        agent: Any,
        exception: Exception,
        model: str,
        provider: str,
        **kwargs,
    ) -> None:
        entry = self._traces.pop(id(agent), None)
        if entry:
            entry["span"].end(level="ERROR", status_message=str(exception))

    def on_tool_call(
        self, tool_name: str, arguments: dict, result: Any, **kwargs
    ) -> None:
        pass

    def on_cache_hit(self, cache_read_tokens: int, **kwargs) -> None:
        pass
