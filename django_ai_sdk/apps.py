from django.apps import AppConfig


class AiSdkConfig(AppConfig):
    name = "django_ai_sdk"
    verbose_name = "Django AI SDK"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.conf import settings as django_settings

        from django_ai_sdk.providers.registry import registry

        raw = getattr(django_settings, "AI_SDK", {})
        if isinstance(raw, dict):
            registry.configure(raw)
