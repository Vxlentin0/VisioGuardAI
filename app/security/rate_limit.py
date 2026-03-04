"""Sliding-window rate limiter with stale-key eviction."""

import logging
import time
from dataclasses import dataclass, field

from app.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

# Evict keys that haven't been seen for this many seconds.
_STALE_KEY_TTL = 300  # 5 minutes


@dataclass
class RateLimitInfo:
    """Snapshot returned to callers so they can set response headers."""

    limit: int
    remaining: int
    reset: int  # unix timestamp when the oldest entry expires


class RateLimiter:
    """In-memory sliding-window rate limiter.

    Args:
        calls: Maximum number of requests allowed in *period*.
        period: Window size in seconds.
    """

    def __init__(self, calls: int, period: int) -> None:
        self.calls = calls
        self.period = period
        self._buckets: dict[str, list[float]] = {}
        self._last_eviction: float = time.time()

    # -- public API --

    async def check(self, key: str) -> RateLimitInfo:
        """Record a request and raise if the limit is exceeded.

        Returns a :class:`RateLimitInfo` so the caller can attach standard
        ``X-RateLimit-*`` headers to the response.
        """
        now = time.time()
        self._maybe_evict_stale_keys(now)

        window_start = now - self.period
        bucket = self._buckets.get(key, [])
        # Prune timestamps outside the current window
        bucket = [t for t in bucket if t > window_start]

        if len(bucket) >= self.calls:
            reset_at = int(bucket[0] + self.period)
            logger.warning("Rate limit exceeded")
            raise RateLimitExceededError(retry_after=self.period)

        bucket.append(now)
        self._buckets[key] = bucket

        remaining = max(0, self.calls - len(bucket))
        reset_at = int(bucket[0] + self.period) if bucket else int(now + self.period)
        return RateLimitInfo(limit=self.calls, remaining=remaining, reset=reset_at)

    # -- internal --

    def _maybe_evict_stale_keys(self, now: float) -> None:
        """Remove buckets for keys that haven't sent traffic recently."""
        if now - self._last_eviction < _STALE_KEY_TTL:
            return
        cutoff = now - _STALE_KEY_TTL
        stale = [k for k, ts in self._buckets.items() if not ts or ts[-1] < cutoff]
        for k in stale:
            del self._buckets[k]
        if stale:
            logger.debug("Evicted %d stale rate-limit buckets", len(stale))
        self._last_eviction = now
