# Prompt Caching

`django-ai-sdk` supports native prompt caching for Anthropic and OpenAI, which can significantly reduce costs and latency on repeated requests.

## How It Works

`PromptCacheMiddleware` is applied automatically inside `LiteLLMProvider` when:
- `AI_SDK.CACHE.ENABLED` is `True`
- The provider is listed in `AI_SDK.CACHE.PROVIDERS`
- `Agent.enable_cache` is `True` (the default)

The middleware adds the appropriate cache control headers to the system prompt and the first few user messages.

## Configuration

```python
AI_SDK = {
    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],
    },
}
```

## Disabling Cache for a Specific Agent

```python
class NoCacheAgent(Agent):
    enable_cache = False
```

## Monitoring Cache Performance

The SDK fires signals for cache hits and misses. Connect to them to collect metrics:

```python
from django.dispatch import receiver
from django_ai_sdk.signals import cache_hit, cache_miss

@receiver(cache_hit)
def on_cache_hit(sender, agent, cache_read_tokens, **kwargs):
    print(f"Cache hit: saved {cache_read_tokens} tokens")

@receiver(cache_miss)
def on_cache_miss(sender, agent, **kwargs):
    print("Cache miss")
```

Cache token counts are also available on `AgentResponse.usage`:

```python
response.usage.cache_read_tokens   # Tokens read from cache
response.usage.cache_write_tokens  # Tokens written to cache
```

## Provider Notes

**Anthropic** — Cache prefixes are added using the `cache_control` field. Long system prompts and repeated context are automatically marked as cacheable.

**OpenAI** — Prompt caching is handled transparently by the OpenAI API when the `enable_cache` flag is set. No special parameters are needed.
