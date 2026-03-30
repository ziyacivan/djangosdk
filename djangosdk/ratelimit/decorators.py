from __future__ import annotations

import functools
from typing import Any, Callable

from django.http import JsonResponse


def ai_rate_limit(
    *,
    tokens_per_minute: int | None = None,
    tokens_per_day: int | None = None,
    get_user_id: Callable | None = None,
    estimated_tokens: int = 1000,
):
    """
    View decorator that enforces token-based rate limits.

    Reads current usage from ``DjangoCacheRateLimitBackend`` and rejects the
    request with HTTP 429 if the limit would be exceeded.

    ``estimated_tokens`` is the pre-request estimate. Actual consumption is
    recorded after the response by the backend (if available in the response).

    Example::

        @api_view(["POST"])
        @ai_rate_limit(tokens_per_minute=10_000)
        def my_chat_view(request):
            ...

    Global limits are read from ``settings.AI_SDK["RATE_LIMITING"]``.
    Per-view overrides are applied on top.
    """

    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs) -> Any:
            from djangosdk.conf import ai_settings

            rl_cfg = ai_settings.RATE_LIMITING
            if not rl_cfg.get("ENABLED", False):
                return view_func(request, *args, **kwargs)

            from djangosdk.ratelimit.backends import DjangoCacheRateLimitBackend

            backend = DjangoCacheRateLimitBackend()

            # Determine user identity
            if get_user_id:
                user_id = get_user_id(request)
            elif hasattr(request, "user") and request.user.is_authenticated:
                user_id = request.user.pk
            else:
                user_id = request.META.get("REMOTE_ADDR", "anonymous")

            allowed, reason = backend.check(user_id, estimated_tokens)
            if not allowed:
                return JsonResponse(
                    {"error": "rate_limit_exceeded", "detail": reason},
                    status=429,
                )

            response = view_func(request, *args, **kwargs)

            # Record consumption after the response is built
            backend.consume(user_id, estimated_tokens)

            return response

        return wrapper

    return decorator
