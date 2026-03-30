from __future__ import annotations

from typing import Any

from django_ai_sdk.observability.base import AbstractObserver


class LangSmithObserver(AbstractObserver):
    """
    LangSmith observability backend.

    Requires: ``pip install langsmith``

    Configure in ``settings.py``::

        AI_SDK = {
            "OBSERVABILITY": {
                "BACKEND": "langsmith",
                "LANGCHAIN_API_KEY": env("LANGCHAIN_API_KEY"),
                "LANGCHAIN_PROJECT": "my-project",
            }
        }
    """

    def __init__(self, api_key: str, project: str = "default") -> None:
        try:
            from langsmith import Client
        except ImportError as exc:
            raise ImportError(
                "langsmith is required. Run: pip install langsmith"
            ) from exc
        self._client = Client(api_key=api_key)
        self._project = project
        self._runs: dict[int, Any] = {}

    def on_agent_start(
        self, agent: Any, prompt: str, model: str, provider: str, **kwargs
    ) -> Any:
        import datetime

        run = self._client.create_run(
            name=f"{agent.__class__.__name__}.handle",
            run_type="llm",
            inputs={"prompt": prompt},
            extra={"metadata": {"provider": provider, "model": model}},
            project_name=self._project,
            start_time=datetime.datetime.utcnow(),
        )
        self._runs[id(agent)] = run
        return run

    def on_agent_complete(
        self, agent: Any, response: Any, model: str, provider: str, **kwargs
    ) -> None:
        import datetime

        run = self._runs.pop(id(agent), None)
        if not run:
            return
        self._client.update_run(
            run.id,
            outputs={"text": getattr(response, "text", "")},
            end_time=datetime.datetime.utcnow(),
        )

    def on_agent_error(
        self,
        agent: Any,
        exception: Exception,
        model: str,
        provider: str,
        **kwargs,
    ) -> None:
        import datetime

        run = self._runs.pop(id(agent), None)
        if not run:
            return
        self._client.update_run(
            run.id, error=str(exception), end_time=datetime.datetime.utcnow()
        )

    def on_tool_call(
        self, tool_name: str, arguments: dict, result: Any, **kwargs
    ) -> None:
        pass
