# Observability

`django-ai-sdk` supports three observability backends: LangSmith, Langfuse, and OpenTelemetry.

## Configuration

```python
AI_SDK = {
    "OBSERVABILITY": {
        "BACKEND": "langsmith",  # "langsmith" | "langfuse" | "opentelemetry" | None
    },
}
```

## LangSmith

[LangSmith](https://smith.langchain.com/) provides tracing, evaluation, and monitoring for AI applications.

```bash
uv add "django-ai-sdk[langsmith]"
```

```python
import os
os.environ["LANGCHAIN_API_KEY"] = "ls__..."
os.environ["LANGCHAIN_TRACING_V2"] = "true"

AI_SDK = {
    "OBSERVABILITY": {"BACKEND": "langsmith"},
}
```

Every `agent.handle()` call is automatically traced as a LangSmith run.

## Langfuse

[Langfuse](https://langfuse.com/) is an open-source LLM observability platform.

```bash
uv add "django-ai-sdk[langfuse]"
```

```python
AI_SDK = {
    "OBSERVABILITY": {
        "BACKEND": "langfuse",
        "LANGFUSE_PUBLIC_KEY": env("LANGFUSE_PUBLIC_KEY"),
        "LANGFUSE_SECRET_KEY": env("LANGFUSE_SECRET_KEY"),
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
    },
}
```

## OpenTelemetry

For custom observability pipelines, use the OpenTelemetry backend:

```bash
uv add "django-ai-sdk[opentelemetry]"
```

```python
AI_SDK = {
    "OBSERVABILITY": {"BACKEND": "opentelemetry"},
}
```

Traces are emitted to the configured OpenTelemetry exporter (OTLP, Jaeger, Zipkin, etc.).

```python
# Configure your OTel exporter as usual
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
```

## What Gets Traced

| Event | Data captured |
|---|---|
| Agent start | `agent_class`, `model`, `provider`, `prompt` |
| Agent complete | `response_text`, `token_usage`, `latency_ms` |
| Tool call | `tool_name`, `arguments`, `result` |
| Cache hit/miss | `cache_read_tokens` |
| Provider failover | `from_provider`, `to_provider` |

## Cost Tracking

The analytics module tracks token costs per provider:

```python
from django_ai_sdk.analytics.cost import CostCalculator

calc = CostCalculator()
cost = calc.calculate(
    provider="openai",
    model="gpt-4.1",
    prompt_tokens=500,
    completion_tokens=100,
)
print(f"Estimated cost: ${cost:.6f}")
```
