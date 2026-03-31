from django.apps import AppConfig


def _patch_django_context_copy() -> None:
    """Patch BaseContext.__copy__ for Python 3.14 + Django < 5.1 compatibility.

    Django 4.x/5.0 replaces an instance's __dict__ wholesale inside __copy__,
    which Python 3.14 no longer permits after __class__ reassignment — the
    object ends up in a broken state and subsequent attribute writes raise
    AttributeError.  The fix creates the duplicate via object.__new__ (avoiding
    __class__ mutation) and updates __dict__ in-place instead of replacing it.

    The patch is a no-op on Python < 3.14 or Django >= 5.1, where the issue
    either does not exist or has already been resolved upstream.
    """
    import sys

    if sys.version_info < (3, 14):
        return

    import django

    if django.VERSION[:2] >= (5, 1):
        return

    from copy import copy
    from django.template.context import BaseContext

    def _copy(self):  # noqa: ANN001, ANN202
        cls = type(self)
        duplicate = object.__new__(cls)
        duplicate.__dict__.update(copy(self.__dict__))
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _copy


class AiSdkConfig(AppConfig):
    name = "djangosdk"
    verbose_name = "Django AI SDK"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        _patch_django_context_copy()

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
