---
name: setup-ratelimit-analytics
description: >
  Configures token-based rate limiting and API cost analytics using
  djangosdk.ratelimit and djangosdk.analytics. Invoke when the user says
  "add rate limiting", "set up cost tracking", "track token usage",
  "add analytics", "limit API spend", "configure budget limits",
  or "track per-user costs".
triggers:
  - add rate limiting
  - set up cost tracking
  - track token usage
  - add analytics
  - limit API spend
  - configure budget limits
  - track per-user costs
  - ai_rate_limit decorator
  - token budget
  - cost reporting
  - usage tracking
---

# Set Up Rate Limiting and Cost Analytics

You are configuring token-based rate limiting and cost tracking for `django-ai-sdk` agents.

## Part 1 — Token-Based Rate Limiting

### Step 1 — Enable in Settings

```python
# settings.py
AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",
    "PROVIDERS": {
        "openai": {"api_key": os.environ["OPENAI_API_KEY"]},
    },
    "RATE_LIMITING": {
        "ENABLED": True,
        "TOKENS_PER_MINUTE": 100_000,     # global default
        "TOKENS_PER_DAY": 2_000_000,      # global default
        "CACHE_BACKEND": "default",       # Django cache alias
    },
}
```

### Step 2 — Apply `@ai_rate_limit` to Views

```python
# myapp/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from djangosdk.ratelimit.decorators import ai_rate_limit
from myapp.agents import SupportAgent


@api_view(["POST"])
@ai_rate_limit(
    tokens_per_minute=10_000,    # per-view override
    estimated_tokens=500,        # estimated tokens per request
)
def chat_view(request):
    agent = SupportAgent()
    response = agent.handle(request.data.get("prompt", ""))
    return Response({"text": response.text})
```

### Step 3 — Per-User Rate Limits

By default, `@ai_rate_limit` identifies users by `request.user.pk` (authenticated) or `REMOTE_ADDR` (anonymous). Override with `get_user_id`:

```python
@api_view(["POST"])
@ai_rate_limit(
    tokens_per_minute=5_000,
    get_user_id=lambda request: request.headers.get("X-Tenant-ID", "anonymous"),
)
def tenant_chat_view(request):
    ...
```

### Step 4 — 429 Response Format

When the rate limit is exceeded, the decorator returns:
```json
{
  "error": "rate_limit_exceeded",
  "detail": "Token limit exceeded: 100000 tokens/minute"
}
```
HTTP status: `429 Too Many Requests`.

### Step 5 — Check Current Usage Programmatically

```python
from djangosdk.ratelimit.backends import DjangoCacheRateLimitBackend

backend = DjangoCacheRateLimitBackend()
allowed, reason = backend.check(user_id="user_42", estimated_tokens=1000)
if not allowed:
    print(f"Blocked: {reason}")
```

---

## Part 2 — Cost Analytics

### Step 1 — Enable Cost Tracking

```python
AI_SDK = {
    ...
    "ANALYTICS": {
        "ENABLED": True,
        "STORE_BACKEND": "django",     # stores in DjangoCostRecord ORM model
    },
}
```

### Step 2 — Automatic Cost Recording

When `ANALYTICS["ENABLED"]` is `True`, every `agent.handle()` call automatically records:
- Provider, model, agent class name
- Prompt tokens, completion tokens, total tokens
- Estimated cost (USD) based on litellm's price table

### Step 3 — Query Cost Records

```python
from djangosdk.analytics.cost import CostReporter

reporter = CostReporter()

# Total cost this month
total = reporter.total_cost(period="month")
print(f"Monthly spend: ${total:.4f}")

# Cost by agent class
breakdown = reporter.cost_by_agent()
for agent_name, cost in breakdown.items():
    print(f"{agent_name}: ${cost:.4f}")

# Cost by provider
by_provider = reporter.cost_by_provider()
print(by_provider)

# Cost for a specific date range
from datetime import date
cost = reporter.cost_for_range(
    start=date(2026, 3, 1),
    end=date(2026, 3, 31),
)
```

### Step 4 — Management Command

View a cost summary from the CLI:

```bash
# Print a cost report to stdout
python manage.py ai_sdk_publish --costs

# Check provider connectivity and show token estimates
python manage.py ai_sdk_check
```

### Step 5 — Cost Alerts via Django Signals

Connect a handler to `agent_completed` to alert when spend exceeds a threshold:

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from djangosdk.signals import agent_completed

        def alert_on_high_cost(sender, response, **kwargs):
            if response.usage and response.usage.total_tokens > 10_000:
                import logging
                logging.getLogger("ai_sdk.cost").warning(
                    "High token usage: %d tokens for agent %s",
                    response.usage.total_tokens,
                    sender.__class__.__name__,
                )

        agent_completed.connect(alert_on_high_cost)
```

### Step 6 — Test Rate Limiting

```python
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient


class RateLimitTest(TestCase):
    def test_rate_limit_returns_429_when_exceeded(self):
        with patch("djangosdk.ratelimit.backends.DjangoCacheRateLimitBackend.check") as mock_check:
            mock_check.return_value = (False, "Token limit exceeded")

            client = APIClient()
            response = client.post(
                "/api/chat/",
                {"prompt": "Hello"},
                format="json",
            )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["error"], "rate_limit_exceeded")
```
