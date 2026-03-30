# Signals

`django-ai-sdk` fires Django signals at key points in the agent lifecycle. Connect to them for logging, metrics, billing, alerting, or custom side effects.

## Available Signals

### `agent_started`

Fired when an agent begins processing a request.

**kwargs:** `agent`, `prompt`, `model`, `provider`

```python
from django.dispatch import receiver
from django_ai_sdk.signals import agent_started

@receiver(agent_started)
def on_agent_started(sender, agent, prompt, model, provider, **kwargs):
    print(f"[{provider}/{model}] Starting: {prompt[:50]}")
```

### `agent_completed`

Fired when an agent successfully completes a request.

**kwargs:** `agent`, `response`, `model`, `provider`

```python
from django_ai_sdk.signals import agent_completed

@receiver(agent_completed)
def on_agent_completed(sender, agent, response, model, provider, **kwargs):
    print(f"Completed. Tokens used: {response.usage.total_tokens}")
```

### `agent_failed`

Fired when an agent raises an exception.

**kwargs:** `agent`, `exception`, `model`, `provider`

```python
from django_ai_sdk.signals import agent_failed

@receiver(agent_failed)
def on_agent_failed(sender, agent, exception, model, provider, **kwargs):
    import logging
    logging.error(f"Agent failed [{provider}/{model}]: {exception}")
```

### `agent_failed_over`

Fired when the failover mechanism switches providers.

**kwargs:** `agent`, `from_provider`, `to_provider`, `reason`

```python
from django_ai_sdk.signals import agent_failed_over

@receiver(agent_failed_over)
def on_failover(sender, agent, from_provider, to_provider, reason, **kwargs):
    print(f"Failover: {from_provider} → {to_provider} ({reason})")
```

### `cache_hit`

Fired when a prompt cache hit occurs.

**kwargs:** `agent`, `cache_read_tokens`

```python
from django_ai_sdk.signals import cache_hit

@receiver(cache_hit)
def on_cache_hit(sender, agent, cache_read_tokens, **kwargs):
    print(f"Cache hit: saved {cache_read_tokens} input tokens")
```

### `cache_miss`

Fired when no cache hit occurs.

**kwargs:** `agent`

```python
from django_ai_sdk.signals import cache_miss

@receiver(cache_miss)
def on_cache_miss(sender, agent, **kwargs):
    pass  # Normal for first requests
```

## Connecting Signals in AppConfig

The recommended place to connect signals is in your app's `AppConfig.ready()`:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from django_ai_sdk.signals import agent_completed
        from myapp.handlers import log_completion
        agent_completed.connect(log_completion)
```

## Example: Usage Tracking

```python
from django_ai_sdk.signals import agent_completed
from myapp.models import UsageRecord

def track_usage(sender, agent, response, **kwargs):
    UsageRecord.objects.create(
        agent_class=sender.__name__,
        model=response.model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        cache_read_tokens=response.usage.cache_read_tokens,
    )

agent_completed.connect(track_usage)
```
