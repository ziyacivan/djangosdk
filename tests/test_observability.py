"""Tests for observability backends (LangSmith, Langfuse, OpenTelemetry)."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock


def _inject_fake_module(name: str, **attrs) -> MagicMock:
    """Inject a fake module into sys.modules so imports succeed without the real package."""
    mod = types.ModuleType(name)
    for attr, val in attrs.items():
        setattr(mod, attr, val)
    sys.modules[name] = mod
    return mod


# ===========================================================================
# AbstractObserver
# ===========================================================================

class TestAbstractObserver:
    def test_all_hooks_are_callable(self):
        from djangosdk.observability.base import AbstractObserver

        class ConcreteObserver(AbstractObserver):
            def on_agent_start(self, agent, prompt, model, provider, **kwargs): pass
            def on_agent_complete(self, agent, response, model, provider, **kwargs): pass
            def on_agent_error(self, agent, exception, model, provider, **kwargs): pass

        obs = ConcreteObserver()
        obs.on_agent_start(agent=None, prompt="hi", model="gpt-4o", provider="openai")
        obs.on_agent_complete(agent=None, response=None, model="gpt-4o", provider="openai")
        obs.on_agent_error(agent=None, exception=ValueError("oops"), model="gpt-4o", provider="openai")
        obs.on_tool_call(tool_name="lookup", arguments={}, result="ok")
        obs.on_cache_hit(cache_read_tokens=100)


# ===========================================================================
# LangSmithObserver
# ===========================================================================

class TestLangSmithObserver:
    def setup_method(self):
        """Inject a fake 'langsmith' module before each test."""
        self.mock_client_cls = MagicMock()
        self.mock_run = MagicMock()
        self.mock_run.id = "run-123"
        self.mock_client_cls.return_value.create_run.return_value = self.mock_run

        fake_langsmith = types.ModuleType("langsmith")
        fake_langsmith.Client = self.mock_client_cls
        sys.modules["langsmith"] = fake_langsmith
        # Reload the module to pick up the new fake
        if "djangosdk.observability.langsmith" in sys.modules:
            del sys.modules["djangosdk.observability.langsmith"]

    def teardown_method(self):
        sys.modules.pop("langsmith", None)
        sys.modules.pop("djangosdk.observability.langsmith", None)

    def _make_observer(self):
        from djangosdk.observability.langsmith import LangSmithObserver
        obs = LangSmithObserver(api_key="ls-test-key", project="test-project")
        return obs

    def test_on_agent_start_creates_run(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hello", model="gpt-4o", provider="openai")

        obs._client.create_run.assert_called_once()
        kwargs = obs._client.create_run.call_args[1]
        assert kwargs["inputs"] == {"prompt": "Hello"}
        assert kwargs["project_name"] == "test-project"

    def test_on_agent_complete_updates_run(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")
        response = MagicMock()
        response.text = "Hello back!"
        obs.on_agent_complete(agent=agent, response=response, model="gpt-4o", provider="openai")

        obs._client.update_run.assert_called_once()
        kwargs = obs._client.update_run.call_args[1]
        assert kwargs["outputs"]["text"] == "Hello back!"

    def test_on_agent_error_updates_run_with_error(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")
        obs.on_agent_error(
            agent=agent, exception=RuntimeError("boom"), model="gpt-4o", provider="openai"
        )

        obs._client.update_run.assert_called_once()
        kwargs = obs._client.update_run.call_args[1]
        assert "boom" in kwargs["error"]

    def test_on_agent_complete_without_prior_start_is_noop(self):
        obs = self._make_observer()
        agent = MagicMock()
        response = MagicMock()

        obs.on_agent_complete(agent=agent, response=response, model="gpt-4o", provider="openai")
        obs._client.update_run.assert_not_called()


# ===========================================================================
# LangfuseObserver
# ===========================================================================

class TestLangfuseObserver:
    def setup_method(self):
        self.mock_lf_cls = MagicMock()
        self.mock_lf = MagicMock()
        self.mock_trace = MagicMock()
        self.mock_generation = MagicMock()
        self.mock_trace.generation.return_value = self.mock_generation
        self.mock_lf.trace.return_value = self.mock_trace
        self.mock_lf_cls.return_value = self.mock_lf

        fake_langfuse = types.ModuleType("langfuse")
        fake_langfuse.Langfuse = self.mock_lf_cls
        sys.modules["langfuse"] = fake_langfuse
        sys.modules.pop("djangosdk.observability.langfuse", None)

    def teardown_method(self):
        sys.modules.pop("langfuse", None)
        sys.modules.pop("djangosdk.observability.langfuse", None)

    def _make_observer(self):
        from djangosdk.observability.langfuse import LangfuseObserver
        return LangfuseObserver(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )

    def test_on_agent_start_creates_trace(self):
        obs = self._make_observer()
        agent = MagicMock()
        agent.__class__.__name__ = "MyAgent"

        obs.on_agent_start(agent=agent, prompt="Test", model="gpt-4o", provider="openai")

        obs._client.trace.assert_called_once()
        self.mock_trace.generation.assert_called_once()

    def test_on_agent_complete_ends_generation(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")
        response = MagicMock()
        response.text = "Response text"
        response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
        obs.on_agent_complete(agent=agent, response=response, model="gpt-4o", provider="openai")

        self.mock_generation.end.assert_called_once()

    def test_on_agent_error_ends_generation_with_error(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")
        obs.on_agent_error(
            agent=agent, exception=ValueError("err"), model="gpt-4o", provider="openai"
        )

        self.mock_generation.end.assert_called_once()


# ===========================================================================
# OpenTelemetryObserver
# ===========================================================================

class TestOpenTelemetryObserver:
    def setup_method(self):
        self.mock_tracer = MagicMock()
        self.mock_span = MagicMock()
        self.mock_span.__enter__ = lambda s: s
        self.mock_span.__exit__ = MagicMock(return_value=False)
        self.mock_tracer.start_span.return_value = self.mock_span
        self.mock_tracer.start_as_current_span.return_value = self.mock_span

        mock_status_code = MagicMock()
        mock_status_code.OK = "OK"
        mock_status_code.ERROR = "ERROR"

        mock_trace_mod = types.ModuleType("opentelemetry.trace")
        mock_trace_mod.get_tracer = MagicMock(return_value=self.mock_tracer)
        mock_trace_mod.get_tracer_provider = MagicMock()
        mock_trace_mod.Status = MagicMock()
        mock_trace_mod.StatusCode = mock_status_code

        mock_otel = types.ModuleType("opentelemetry")
        mock_otel.trace = mock_trace_mod

        sys.modules["opentelemetry"] = mock_otel
        sys.modules["opentelemetry.trace"] = mock_trace_mod
        sys.modules.pop("djangosdk.observability.opentelemetry", None)

    def teardown_method(self):
        sys.modules.pop("opentelemetry", None)
        sys.modules.pop("opentelemetry.trace", None)
        sys.modules.pop("djangosdk.observability.opentelemetry", None)

    def _make_observer(self):
        from djangosdk.observability.opentelemetry import OpenTelemetryObserver
        return OpenTelemetryObserver(service_name="test-service")

    def test_on_agent_start_creates_span(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")

        # Observer uses start_span (not start_as_current_span)
        obs._tracer.start_span.assert_called_once()

    def test_on_agent_complete_sets_span_attributes(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")

        response = MagicMock()
        response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        obs.on_agent_complete(agent=agent, response=response, model="gpt-4o", provider="openai")

        self.mock_span.set_attribute.assert_called()
        self.mock_span.end.assert_called_once()

    def test_on_agent_error_records_exception(self):
        obs = self._make_observer()
        agent = MagicMock()

        obs.on_agent_start(agent=agent, prompt="Hi", model="gpt-4o", provider="openai")
        obs.on_agent_error(
            agent=agent, exception=RuntimeError("oops"), model="gpt-4o", provider="openai"
        )

        self.mock_span.record_exception.assert_called_once()
        self.mock_span.end.assert_called_once()

    def test_on_tool_call_uses_span_context_manager(self):
        obs = self._make_observer()

        obs.on_tool_call(tool_name="lookup", arguments={"id": "1"}, result="ok")

        obs._tracer.start_as_current_span.assert_called_once()

    def test_on_complete_without_prior_start_is_noop(self):
        obs = self._make_observer()
        agent = MagicMock()
        response = MagicMock()
        response.usage = None

        # Should not raise
        obs.on_agent_complete(agent=agent, response=response, model="gpt-4o", provider="openai")


# ===========================================================================
# setup_observability()
# ===========================================================================

class TestSetupObservability:
    def setup_method(self):
        import djangosdk.observability as obs_module
        obs_module._observer = None

    def teardown_method(self):
        import djangosdk.observability as obs_module
        obs_module._observer = None

    def test_no_backend_does_nothing(self):
        from djangosdk.observability import setup_observability, get_observer

        setup_observability({"OBSERVABILITY": {"BACKEND": None}})
        assert get_observer() is None

    def test_langsmith_backend_sets_observer(self):
        mock_client_cls = MagicMock()
        mock_client_cls.return_value.create_run.return_value = MagicMock(id="run-1")

        fake_ls = types.ModuleType("langsmith")
        fake_ls.Client = mock_client_cls
        sys.modules["langsmith"] = fake_ls
        sys.modules.pop("djangosdk.observability.langsmith", None)

        try:
            from djangosdk.observability import setup_observability, get_observer
            setup_observability({
                "OBSERVABILITY": {
                    "BACKEND": "langsmith",
                    "LANGCHAIN_API_KEY": "ls-key",
                    "LANGCHAIN_PROJECT": "my-project",
                }
            })
            from djangosdk.observability.langsmith import LangSmithObserver
            assert isinstance(get_observer(), LangSmithObserver)
        finally:
            sys.modules.pop("langsmith", None)
            sys.modules.pop("djangosdk.observability.langsmith", None)
            import djangosdk.observability as obs_module
            obs_module._observer = None

    def test_unknown_backend_does_nothing(self):
        from djangosdk.observability import setup_observability, get_observer

        setup_observability({"OBSERVABILITY": {"BACKEND": "unknown_backend"}})
        assert get_observer() is None
