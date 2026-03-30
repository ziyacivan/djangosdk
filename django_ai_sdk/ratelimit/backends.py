from __future__ import annotations

import time
from typing import Any


class DjangoCacheRateLimitBackend:
    """
    Token-based rate limiter backed by Django's cache framework.

    Redis is strongly recommended as the cache backend in production so that
    atomic counter increments work correctly across processes.

    Each counter key is a tuple of (user_id, window, granularity), e.g.:
    ``ai_rl:user_42:minute`` and ``ai_rl:user_42:day``.
    """

    PREFIX = "ai_rl"

    def __init__(self) -> None:
        from django.conf import settings as django_settings

        cfg = getattr(django_settings, "AI_SDK", {}).get("RATE_LIMITING", {})
        self._per_minute = cfg.get("PER_USER_TOKENS_PER_MINUTE", 50_000)
        self._per_day = cfg.get("PER_USER_TOKENS_PER_DAY", 500_000)

    def _cache(self):
        from django.core.cache import cache
        return cache

    def _minute_key(self, user_id: Any) -> str:
        minute = int(time.time() // 60)
        return f"{self.PREFIX}:{user_id}:min:{minute}"

    def _day_key(self, user_id: Any) -> str:
        day = int(time.time() // 86400)
        return f"{self.PREFIX}:{user_id}:day:{day}"

    def check(self, user_id: Any, tokens: int) -> tuple[bool, str]:
        """
        Check whether ``user_id`` may consume ``tokens`` more tokens.

        Returns ``(allowed, reason)``. ``reason`` is empty on success.
        """
        cache = self._cache()

        min_key = self._minute_key(user_id)
        day_key = self._day_key(user_id)

        min_used = cache.get(min_key, 0)
        day_used = cache.get(day_key, 0)

        if min_used + tokens > self._per_minute:
            return False, (
                f"Rate limit exceeded: {min_used + tokens} tokens requested "
                f"this minute (limit {self._per_minute})"
            )
        if day_used + tokens > self._per_day:
            return False, (
                f"Rate limit exceeded: {day_used + tokens} tokens requested "
                f"today (limit {self._per_day})"
            )
        return True, ""

    def consume(self, user_id: Any, tokens: int) -> None:
        """Record that ``user_id`` consumed ``tokens`` tokens."""
        cache = self._cache()
        min_key = self._minute_key(user_id)
        day_key = self._day_key(user_id)

        # Increment with TTL — set initial value if key doesn't exist
        if cache.add(min_key, tokens, timeout=120):
            pass  # key was newly created
        else:
            cache.incr(min_key, tokens)

        if cache.add(day_key, tokens, timeout=90000):
            pass
        else:
            cache.incr(day_key, tokens)

    def get_usage(self, user_id: Any) -> dict[str, int]:
        cache = self._cache()
        return {
            "tokens_this_minute": cache.get(self._minute_key(user_id), 0),
            "tokens_today": cache.get(self._day_key(user_id), 0),
            "limit_per_minute": self._per_minute,
            "limit_per_day": self._per_day,
        }
