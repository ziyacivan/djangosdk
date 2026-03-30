"""Tests for token-based rate limiting (ratelimit/)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock


# ===========================================================================
# DjangoCacheRateLimitBackend
# ===========================================================================

class TestDjangoCacheRateLimitBackend:
    def _make_backend(self, per_minute: int = 1000, per_day: int = 10000):
        from django_ai_sdk.ratelimit.backends import DjangoCacheRateLimitBackend
        backend = DjangoCacheRateLimitBackend()
        backend._per_minute = per_minute
        backend._per_day = per_day
        return backend

    def test_check_allowed_when_below_limits(self):
        backend = self._make_backend()
        mock_cache = MagicMock()
        mock_cache.get.return_value = 0

        with patch.object(backend, "_cache", return_value=mock_cache):
            allowed, reason = backend.check("user_1", 100)

        assert allowed is True
        assert reason == ""

    def test_check_denied_when_exceeds_minute_limit(self):
        backend = self._make_backend(per_minute=500)
        mock_cache = MagicMock()
        mock_cache.get.side_effect = lambda key, default=0: 400  # already used 400

        with patch.object(backend, "_cache", return_value=mock_cache):
            allowed, reason = backend.check("user_1", 200)  # 400 + 200 > 500

        assert allowed is False
        assert "minute" in reason.lower()

    def test_check_denied_when_exceeds_day_limit(self):
        backend = self._make_backend(per_minute=50000, per_day=1000)
        mock_cache = MagicMock()

        def _get(key, default=0):
            if ":min:" in key:
                return 0
            return 900  # nearly at day limit

        mock_cache.get.side_effect = _get

        with patch.object(backend, "_cache", return_value=mock_cache):
            allowed, reason = backend.check("user_1", 200)  # 900 + 200 > 1000

        assert allowed is False
        assert "today" in reason.lower()

    def test_consume_creates_new_key(self):
        backend = self._make_backend()
        mock_cache = MagicMock()
        mock_cache.add.return_value = True  # key didn't exist → newly created

        with patch.object(backend, "_cache", return_value=mock_cache):
            backend.consume("user_1", 100)

        assert mock_cache.add.call_count == 2  # minute + day

    def test_consume_increments_existing_key(self):
        backend = self._make_backend()
        mock_cache = MagicMock()
        mock_cache.add.return_value = False  # key already exists

        with patch.object(backend, "_cache", return_value=mock_cache):
            backend.consume("user_1", 50)

        assert mock_cache.incr.call_count == 2

    def test_get_usage_returns_dict(self):
        backend = self._make_backend(per_minute=5000, per_day=50000)
        mock_cache = MagicMock()
        mock_cache.get.return_value = 123

        with patch.object(backend, "_cache", return_value=mock_cache):
            usage = backend.get_usage("user_1")

        assert usage["tokens_this_minute"] == 123
        assert usage["tokens_today"] == 123
        assert usage["limit_per_minute"] == 5000
        assert usage["limit_per_day"] == 50000


# ===========================================================================
# ai_rate_limit decorator
# ===========================================================================

class TestAiRateLimitDecorator:
    def _make_request(self, user_id=None, ip="127.0.0.1"):
        mock_req = MagicMock()
        if user_id is not None:
            mock_req.user = MagicMock()
            mock_req.user.is_authenticated = True
            mock_req.user.pk = user_id
        else:
            mock_req.user = MagicMock()
            mock_req.user.is_authenticated = False
        mock_req.META = {"REMOTE_ADDR": ip}
        return mock_req

    def _view_func(self, request, *args, **kwargs):
        from django.http import JsonResponse
        return JsonResponse({"ok": True})

    def test_passes_through_when_rate_limiting_disabled(self, settings):
        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": False},
        }
        from django_ai_sdk.conf import ai_settings
        ai_settings.reload()

        from django_ai_sdk.ratelimit.decorators import ai_rate_limit

        @ai_rate_limit(estimated_tokens=100)
        def view(request):
            return self._view_func(request)

        request = self._make_request(user_id=1)
        response = view(request)
        assert response.status_code == 200

        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": False},
        }
        ai_settings.reload()

    def test_returns_429_when_limit_exceeded(self, settings):
        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {
                "ENABLED": True,
                "PER_USER_TOKENS_PER_MINUTE": 100,
                "PER_USER_TOKENS_PER_DAY": 10000,
            },
        }
        from django_ai_sdk.conf import ai_settings
        ai_settings.reload()

        from django_ai_sdk.ratelimit.decorators import ai_rate_limit
        from django_ai_sdk.ratelimit.backends import DjangoCacheRateLimitBackend

        @ai_rate_limit(estimated_tokens=500)  # exceeds 100/minute limit
        def view(request):
            return self._view_func(request)

        request = self._make_request(user_id=42)

        mock_backend = MagicMock(spec=DjangoCacheRateLimitBackend)
        mock_backend.check.return_value = (False, "Rate limit exceeded: 500 > 100")

        with patch(
            "django_ai_sdk.ratelimit.backends.DjangoCacheRateLimitBackend",
            return_value=mock_backend,
        ):
            response = view(request)

        assert response.status_code == 429

        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": False},
        }
        ai_settings.reload()

    def test_uses_anonymous_ip_when_not_authenticated(self, settings):
        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": True},
        }
        from django_ai_sdk.conf import ai_settings
        ai_settings.reload()

        from django_ai_sdk.ratelimit.decorators import ai_rate_limit
        from django_ai_sdk.ratelimit.backends import DjangoCacheRateLimitBackend

        @ai_rate_limit(estimated_tokens=10)
        def view(request):
            return self._view_func(request)

        request = self._make_request(ip="192.168.1.1")

        mock_backend = MagicMock(spec=DjangoCacheRateLimitBackend)
        mock_backend.check.return_value = (True, "")

        with patch(
            "django_ai_sdk.ratelimit.backends.DjangoCacheRateLimitBackend",
            return_value=mock_backend,
        ):
            view(request)

        check_call = mock_backend.check.call_args
        assert check_call[0][0] == "192.168.1.1"

        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": False},
        }
        ai_settings.reload()

    def test_custom_get_user_id(self, settings):
        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": True},
        }
        from django_ai_sdk.conf import ai_settings
        ai_settings.reload()

        from django_ai_sdk.ratelimit.decorators import ai_rate_limit
        from django_ai_sdk.ratelimit.backends import DjangoCacheRateLimitBackend

        def get_org_id(request):
            return "org_99"

        @ai_rate_limit(estimated_tokens=10, get_user_id=get_org_id)
        def view(request):
            return self._view_func(request)

        request = self._make_request()
        mock_backend = MagicMock(spec=DjangoCacheRateLimitBackend)
        mock_backend.check.return_value = (True, "")

        with patch(
            "django_ai_sdk.ratelimit.backends.DjangoCacheRateLimitBackend",
            return_value=mock_backend,
        ):
            view(request)

        assert mock_backend.check.call_args[0][0] == "org_99"

        settings.AI_SDK = {
            "DEFAULT_PROVIDER": "fake",
            "DEFAULT_MODEL": "fake-model",
            "PROVIDERS": {},
            "RATE_LIMITING": {"ENABLED": False},
        }
        ai_settings.reload()
