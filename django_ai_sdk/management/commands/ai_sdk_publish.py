from __future__ import annotations

from django.core.management.base import BaseCommand


_SETTINGS_TEMPLATE = '''\
AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4o-mini",

    "PROVIDERS": {
        "openai": {
            "api_key": env("OPENAI_API_KEY"),
            "default_model": "gpt-4o-mini",
            "default_reasoning_effort": "medium",
        },
        "anthropic": {
            "api_key": env("ANTHROPIC_API_KEY"),
            "default_model": "claude-3-5-haiku-20241022",
            "default_thinking_budget": 8000,
        },
        "gemini": {
            "api_key": env("GEMINI_API_KEY"),
            "default_model": "gemini-2.0-flash",
        },
        "groq": {
            "api_key": env("GROQ_API_KEY"),
            "default_model": "llama-4-scout-17b-16e-instruct",
        },
        "deepseek": {
            "api_key": env("DEEPSEEK_API_KEY"),
            "default_model": "deepseek-chat",
        },
        "mistral": {
            "api_key": env("MISTRAL_API_KEY"),
            "default_model": "mistral-medium-3",
        },
        "xai": {
            "api_key": env("XAI_API_KEY"),
            "default_model": "grok-3-fast",
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "default_model": "llama4:scout",
        },
    },

    "FAILOVER": [],

    "CONVERSATION": {
        "PERSIST": True,
        "MAX_HISTORY": 50,
    },

    "CACHE": {
        "ENABLED": True,
        "PROVIDERS": ["anthropic", "openai"],
    },

    "STREAMING": {
        "CHUNK_SEPARATOR": "\\n\\n",
        "SSE_RETRY_MS": 3000,
        "STREAM_THINKING": False,
    },
}
'''


class Command(BaseCommand):
    help = "Writes a copy-paste-ready AI_SDK settings block to stdout."

    def handle(self, *args, **options):
        self.stdout.write(_SETTINGS_TEMPLATE)
