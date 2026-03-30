from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.conf import ai_settings
from django_ai_sdk.providers.registry import registry


class Command(BaseCommand):
    help = "Sends a test request to each configured AI provider and reports results."

    def handle(self, *args, **options):
        providers = registry.list_providers()
        if not providers:
            self.stdout.write(self.style.WARNING("No providers configured in AI_SDK.PROVIDERS."))
            return

        default_model_setting = ai_settings.DEFAULT_MODEL
        results = []

        for provider_name in providers:
            config = registry.get_config(provider_name)
            model = (config.default_model if config and config.default_model else default_model_setting)
            start = time.monotonic()
            try:
                provider = registry.get(provider_name)
                request = AgentRequest(
                    messages=[{"role": "user", "content": "Reply with just: Hello!"}],
                    model=model,
                    provider=provider_name,
                    max_tokens=10,
                    temperature=0.0,
                    enable_cache=False,
                )
                response = provider.complete(request)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                results.append((True, provider_name, model, repr(response.text[:40]), elapsed_ms, ""))
            except Exception as exc:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                results.append((False, provider_name, model, "", elapsed_ms, str(exc)[:80]))

        for ok, pname, model, text, ms, err in results:
            label = f"{pname}/{model}"
            if ok:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {label:<40}  {text}  ({ms}ms)")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {label:<40}  {err}  ({ms}ms)")
                )
