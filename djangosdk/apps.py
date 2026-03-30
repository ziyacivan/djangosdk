from django.apps import AppConfig


class AiSdkConfig(AppConfig):
    name = "djangosdk"
    verbose_name = "Django AI SDK"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.conf import settings as django_settings

        from djangosdk.providers.registry import registry

        raw = getattr(django_settings, "AI_SDK", {})
        if isinstance(raw, dict):
            registry.configure(raw)

        # Initialize observability backend (Phase 2)
        if isinstance(raw, dict) and raw.get("OBSERVABILITY", {}).get("BACKEND"):
            try:
                from djangosdk.observability import setup_observability
                setup_observability(raw)
            except Exception:
                pass  # Observability is non-critical — never block startup
