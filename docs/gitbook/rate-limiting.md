# Rate Limiting

`djangosdk` supports token-based rate limiting — rate limits based on the number of tokens consumed, not the number of requests. This is more accurate for AI workloads where a single request can consume vastly different amounts of tokens.

## Configuration

```python
AI_SDK = {
    "RATE_LIMITING": {
        "ENABLED": True,
        "BACKEND": "django_cache",
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}
```

## The `@ai_rate_limit` Decorator

Apply rate limiting to a view or function:

```python
from djangosdk.ratelimit.decorators import ai_rate_limit

@ai_rate_limit(tokens_per_minute=10000, tokens_per_day=100000)
def chat_view(request):
    agent = SupportAgent()
    response = agent.handle(request.POST["message"])
    return JsonResponse({"text": response.text})
```

If the rate limit is exceeded, the decorator raises `RateLimitExceeded` (HTTP 429).

## Rate Limit Backend

The default backend (`django_cache`) uses Django's cache framework to track token usage. Any Django cache backend works (Redis, Memcached, database, etc.).

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

## Custom Backend

Implement `AbstractRateLimitBackend` to use a custom store:

```python
from djangosdk.ratelimit.backends import AbstractRateLimitBackend

class MyRateLimitBackend(AbstractRateLimitBackend):
    def check_and_consume(self, user_id: str, tokens: int) -> bool:
        # Return True if allowed, False if rate limit exceeded
        ...
```

## Per-User Limits

Rate limits are tracked per user. The default key is `request.user.id`. Override the key function for custom scoping:

```python
@ai_rate_limit(
    tokens_per_minute=10000,
    key_func=lambda request: request.META.get("HTTP_X_API_KEY", "anonymous"),
)
def api_view(request):
    ...
```
