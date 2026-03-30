# Settings Reference

All `djangosdk` settings live in `AI_SDK` in your `settings.py`. Unspecified keys use the defaults shown below.

## Complete Reference

```python
AI_SDK = {
    # ──────────────────────────────────────────────
    # Default provider and model
    # ──────────────────────────────────────────────
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4o-mini",

    # ──────────────────────────────────────────────
    # Provider configurations
    # ──────────────────────────────────────────────
    "PROVIDERS": {
        # Each key matches a provider name used in Agent.provider
        "openai": {
            "api_key": "sk-...",
            "organization": "",           # Optional
            "default_model": "",          # Override default model for this provider
        },
        "anthropic": {
            "api_key": "sk-ant-...",
            "default_model": "claude-3-5-haiku-20241022",
            "default_thinking_budget": 8000,
        },
        "gemini": {
            "api_key": "AIza...",
        },
        "groq": {
            "api_key": "gsk_...",
        },
        "deepseek": {
            "api_key": "sk-...",
            "base_url": "https://api.deepseek.com",
        },
        "mistral": {
            "api_key": "...",
        },
        "xai": {
            "api_key": "xai-...",
        },
        "ollama": {
            "base_url": "http://localhost:11434",
        },
        "azure": {
            "api_key": "...",
            "base_url": "https://YOUR_RESOURCE.openai.azure.com",
            "api_version": "2024-02-01",
        },
    },

    # ──────────────────────────────────────────────
    # Provider failover chain
    # If a provider call fails, try the next one in order.
    # ──────────────────────────────────────────────
    "FAILOVER": [],   # e.g., ["openai", "anthropic"]

    # ──────────────────────────────────────────────
    # Conversation persistence
    # ──────────────────────────────────────────────
    "CONVERSATION": {
        "PERSIST": True,           # Save messages to the database
        "MAX_HISTORY": 50,         # Max messages loaded per agent turn
        "AUTO_SUMMARIZE": False,   # Auto-summarize old messages when MAX_HISTORY is exceeded
    },

    # ──────────────────────────────────────────────
    # Prompt caching
    # ──────────────────────────────────────────────
    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],  # Providers with native caching
    },

    # ──────────────────────────────────────────────
    # Server-Sent Events streaming
    # ──────────────────────────────────────────────
    "STREAMING": {
        "CHUNK_SEPARATOR": "\n\n",   # SSE event separator
        "SSE_RETRY_MS": 3000,         # Client reconnect delay hint (ms)
        "STREAM_THINKING": False,     # Include thinking_delta chunks
    },

    # ──────────────────────────────────────────────
    # Observability backend
    # ──────────────────────────────────────────────
    "OBSERVABILITY": {
        "BACKEND": None,   # "langsmith" | "langfuse" | "opentelemetry" | None
    },

    # ──────────────────────────────────────────────
    # Token-based rate limiting
    # ──────────────────────────────────────────────
    "RATE_LIMITING": {
        "ENABLED": False,
        "BACKEND": "django_cache",
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}
```

## Accessing Settings in Code

Use `ai_settings` to read values programmatically:

```python
from djangosdk.conf import ai_settings

print(ai_settings.DEFAULT_PROVIDER)   # "openai"
print(ai_settings.DEFAULT_MODEL)      # "gpt-4o-mini"
print(ai_settings.CONVERSATION)       # {"PERSIST": True, "MAX_HISTORY": 50, ...}

# With a fallback
value = ai_settings.get("RATE_LIMITING", {}).get("ENABLED", False)
```

## Programmatic Reload (Tests)

In tests, settings may change between test cases. Force a reload with:

```python
from djangosdk.conf import ai_settings

ai_settings.reload()
```

## Environment Variable Pattern

Keep secrets out of version control:

```python
import environ
env = environ.Env()

AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
        "anthropic": {"api_key": env("ANTHROPIC_API_KEY", default="")},
    },
}
```
