# Configuration

All configuration lives in a single `AI_SDK` dict in your `settings.py`.

## Minimal Configuration

```python
# settings.py
AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",
    "PROVIDERS": {
        "openai": {
            "api_key": env("OPENAI_API_KEY"),
        },
    },
}
```

## Full Configuration Reference

```python
AI_SDK = {
    # Default provider and model used when an agent does not specify one
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",

    # Provider configurations
    "PROVIDERS": {
        "openai": {
            "api_key": env("OPENAI_API_KEY"),
        },
        "anthropic": {
            "api_key": env("ANTHROPIC_API_KEY"),
            "default_model": "claude-3-5-haiku-20241022",
            "default_thinking_budget": 8000,
        },
        "gemini": {
            "api_key": env("GEMINI_API_KEY"),
        },
        "groq": {
            "api_key": env("GROQ_API_KEY"),
        },
        "deepseek": {
            "api_key": env("DEEPSEEK_API_KEY"),
            "base_url": "https://api.deepseek.com",
        },
        "ollama": {
            "base_url": "http://localhost:11434",
        },
    },

    # Provider failover chain
    "FAILOVER": ["openai", "anthropic"],

    # Conversation persistence
    "CONVERSATION": {
        "PERSIST": True,          # Save messages to the database
        "MAX_HISTORY": 50,        # Maximum messages loaded per turn
        "AUTO_SUMMARIZE": False,  # Auto-summarize older messages
    },

    # Prompt caching (Anthropic + OpenAI native caching)
    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],
    },

    # Server-Sent Events streaming
    "STREAMING": {
        "CHUNK_SEPARATOR": "\n\n",
        "SSE_RETRY_MS": 3000,
        "STREAM_THINKING": False,  # Include thinking_delta chunks
    },

    # Observability backend
    "OBSERVABILITY": {
        "BACKEND": None,  # "langsmith" | "langfuse" | "opentelemetry" | None
    },

    # Token-based rate limiting
    "RATE_LIMITING": {
        "ENABLED": False,
        "BACKEND": "django_cache",
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}
```

## Provider Config Options

Each entry under `PROVIDERS` supports the following keys:

| Key | Type | Description |
|---|---|---|
| `api_key` | `str` | Provider API key |
| `base_url` | `str` | Custom API base URL (e.g., for self-hosted Ollama) |
| `organization` | `str` | OpenAI organization ID |
| `api_version` | `str` | Azure OpenAI API version |
| `default_model` | `str` | Default model for this provider |
| `default_reasoning_effort` | `"low" \| "medium" \| "high"` | Default reasoning effort |
| `default_thinking_budget` | `int` | Default thinking token budget for Claude |

Unknown keys are passed through to litellm as-is, so any litellm-supported parameter can be set here.

## Multiple Providers Example

```python
AI_SDK = {
    "DEFAULT_PROVIDER": "anthropic",
    "DEFAULT_MODEL": "claude-3-5-haiku-20241022",
    "PROVIDERS": {
        "anthropic": {"api_key": env("ANTHROPIC_API_KEY")},
        "openai": {"api_key": env("OPENAI_API_KEY")},
        "ollama": {"base_url": "http://localhost:11434"},
    },
    "FAILOVER": ["anthropic", "openai"],
}
```

## Validating Configuration

Run the built-in management command to test every configured provider:

```bash
python manage.py ai_sdk_check
```

To print the current resolved settings block:

```bash
python manage.py ai_sdk_publish
```

## Environment Variables

We recommend using `django-environ` or `python-decouple` to keep API keys out of version control:

```python
import environ
env = environ.Env()

AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
    },
}
```
