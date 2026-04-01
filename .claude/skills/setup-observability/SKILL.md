---
name: setup-observability
description: >
  Configures observability backends (LangSmith, Langfuse, OpenTelemetry) by
  generating the correct AI_SDK settings block, environment variables, and
  Django signal receivers. Invoke when the user says "add observability",
  "set up LangSmith", "configure Langfuse", "add OpenTelemetry tracing",
  "how do I trace my agents", "enable tracing", or "monitor my agent".
triggers:
  - add observability
  - set up LangSmith
  - configure Langfuse
  - add OpenTelemetry
  - add OpenTelemetry tracing
  - how do I trace my agents
  - enable tracing
  - monitor my agent
  - debug agent calls
  - trace agent runs
  - add LangSmith
  - add Langfuse
---

# Set Up Agent Observability

You are configuring observability for `django-ai-sdk` agents. The SDK emits Django signals on every agent lifecycle event; observability backends receive these via signal receivers.

## Step 1 — Choose Your Backend

| Backend | Use when |
|---|---|
| **LangSmith** | LangChain ecosystem, hosted tracing, team sharing |
| **Langfuse** | Open-source, self-hostable, GDPR-friendly |
| **OpenTelemetry** | Existing OTel infra (Jaeger, Tempo, Honeycomb) |

All three can be active simultaneously.

## Step 2 — Install Dependencies

```bash
# LangSmith
pip install langsmith

# Langfuse
pip install langfuse

# OpenTelemetry
pip install opentelemetry-sdk opentelemetry-exporter-otlp
```

## Step 3 — Configure AI_SDK Settings

Add the `OBSERVABILITY` block to your `AI_SDK` settings:

```python
# settings.py
import os

AI_SDK = {
    "DEFAULT_PROVIDER": "anthropic",
    "DEFAULT_MODEL": "claude-sonnet-4-6",
    "PROVIDERS": {
        "anthropic": {"api_key": os.environ["ANTHROPIC_API_KEY"]},
    },
    "OBSERVABILITY": {
        # Choose one or more backends:
        "BACKEND": "langsmith",          # "langsmith" | "langfuse" | "opentelemetry"
        # LangSmith
        "LANGCHAIN_API_KEY": os.environ.get("LANGCHAIN_API_KEY", ""),
        "LANGCHAIN_PROJECT": "my-django-project",
        # Langfuse
        "LANGFUSE_PUBLIC_KEY": os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
        "LANGFUSE_SECRET_KEY": os.environ.get("LANGFUSE_SECRET_KEY", ""),
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
        # OpenTelemetry
        "OTEL_SERVICE_NAME": "my-django-app",
        "OTEL_EXPORTER_OTLP_ENDPOINT": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    },
}
```

## Step 4 — Register Signal Receivers

The SDK fires Django signals:
- `djangosdk.signals.agent_started` — before each agent call
- `djangosdk.signals.agent_completed` — after a successful response
- `djangosdk.signals.agent_failed` — on exception
- `djangosdk.signals.cache_hit` / `cache_miss` — prompt cache events

Wire the built-in observers in your `apps.py` (or `AppConfig.ready()`):

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from djangosdk.conf import ai_settings
        from djangosdk.signals import agent_started, agent_completed, agent_failed

        obs_cfg = ai_settings.OBSERVABILITY
        backend = obs_cfg.get("BACKEND", "")

        if backend == "langsmith":
            from djangosdk.observability.langsmith import LangSmithObserver
            observer = LangSmithObserver(
                api_key=obs_cfg["LANGCHAIN_API_KEY"],
                project=obs_cfg.get("LANGCHAIN_PROJECT", "default"),
            )
            agent_started.connect(lambda sender, **kw: observer.on_agent_start(sender, **kw))
            agent_completed.connect(lambda sender, **kw: observer.on_agent_complete(sender, **kw))
            agent_failed.connect(lambda sender, **kw: observer.on_agent_error(sender, **kw))

        elif backend == "langfuse":
            from djangosdk.observability.langfuse import LangfuseObserver
            observer = LangfuseObserver(
                public_key=obs_cfg["LANGFUSE_PUBLIC_KEY"],
                secret_key=obs_cfg["LANGFUSE_SECRET_KEY"],
                host=obs_cfg.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            agent_started.connect(lambda sender, **kw: observer.on_agent_start(sender, **kw))
            agent_completed.connect(lambda sender, **kw: observer.on_agent_complete(sender, **kw))
            agent_failed.connect(lambda sender, **kw: observer.on_agent_error(sender, **kw))

        elif backend == "opentelemetry":
            from djangosdk.observability.opentelemetry import OpenTelemetryObserver
            observer = OpenTelemetryObserver(
                service_name=obs_cfg.get("OTEL_SERVICE_NAME", "django-ai-sdk"),
                endpoint=obs_cfg.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            )
            agent_started.connect(lambda sender, **kw: observer.on_agent_start(sender, **kw))
            agent_completed.connect(lambda sender, **kw: observer.on_agent_complete(sender, **kw))
            agent_failed.connect(lambda sender, **kw: observer.on_agent_error(sender, **kw))
```

## Step 5 — Custom Signal Receiver (No Backend)

If you don't want a full observability backend, you can write a lightweight receiver:

```python
# myapp/signals.py
import logging
from djangosdk.signals import agent_started, agent_completed, agent_failed

logger = logging.getLogger("ai_sdk")


def on_agent_started(sender, prompt, model, provider, **kwargs):
    logger.info("agent_started provider=%s model=%s prompt_length=%d", provider, model, len(prompt))


def on_agent_completed(sender, response, model, provider, **kwargs):
    logger.info(
        "agent_completed provider=%s model=%s tokens=%d",
        provider, model,
        response.usage.total_tokens if response.usage else 0,
    )


def on_agent_failed(sender, exception, model, provider, **kwargs):
    logger.error("agent_failed provider=%s model=%s error=%s", provider, model, str(exception))


# Connect in AppConfig.ready():
# agent_started.connect(on_agent_started)
# agent_completed.connect(on_agent_completed)
# agent_failed.connect(on_agent_failed)
```

## Step 6 — Environment Variables

Add to `.env`:

```bash
# LangSmith
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=my-django-app
```

## Step 7 — Verify

Use the management command to fire a real test request to each provider:

```bash
python manage.py ai_sdk_check
```

After running, check your observability backend's UI for the trace.

## Step 8 — Test Signal Firing

```python
from django.test import TestCase
from djangosdk.signals import agent_completed
from djangosdk.testing.fakes import FakeProvider
from myapp.agents import SupportAgent


class ObservabilityTest(TestCase):
    def test_agent_completed_signal_fires(self):
        received = []

        def handler(sender, response, **kwargs):
            received.append(response)

        agent_completed.connect(handler)
        try:
            fake = FakeProvider()
            fake.set_response("done")
            agent = SupportAgent()
            agent._provider = fake
            agent.handle("hello")
        finally:
            agent_completed.disconnect(handler)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].text, "done")
```
