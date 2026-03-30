from __future__ import annotations

from django.conf import settings

from django_ai_sdk.exceptions import ConfigurationError

DEFAULTS: dict = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4o-mini",
    "PROVIDERS": {},
    "FAILOVER": [],
    "CONVERSATION": {
        "PERSIST": True,
        "MAX_HISTORY": 50,
        "AUTO_SUMMARIZE": False,
    },
    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],
    },
    "STREAMING": {
        "CHUNK_SEPARATOR": "\n\n",
        "SSE_RETRY_MS": 3000,
        "STREAM_THINKING": False,
    },
    "OBSERVABILITY": {
        "BACKEND": None,
    },
    "RATE_LIMITING": {
        "ENABLED": False,
        "BACKEND": "django_cache",
        "PER_USER_TOKENS_PER_MINUTE": 50000,
        "PER_USER_TOKENS_PER_DAY": 500000,
    },
}


class AiSettings:
    """Lazy accessor for the AI_SDK settings block."""

    def __init__(self) -> None:
        self._raw: dict | None = None

    def _load(self) -> dict:
        if self._raw is None:
            raw = getattr(settings, "AI_SDK", {})
            if not isinstance(raw, dict):
                raise ConfigurationError("AI_SDK must be a dict in settings.py")
            self._raw = self._deep_merge(DEFAULTS, raw)
        return self._raw

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def __getattr__(self, name: str):
        data = self._load()
        key = name.upper()
        if key in data:
            return data[key]
        raise AttributeError(f"AI_SDK has no setting '{name}'")

    def get(self, key: str, default=None):
        data = self._load()
        return data.get(key.upper(), default)

    def reload(self) -> None:
        """Force re-load (useful in tests)."""
        self._raw = None


ai_settings = AiSettings()
