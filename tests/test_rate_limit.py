"""Tests for the sliding-window rate limiter."""

import pytest

from app.exceptions import RateLimitExceededError
from app.security.rate_limit import RateLimiter


@pytest.fixture()
def limiter():
    return RateLimiter(calls=3, period=60)


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter):
        info = await limiter.check("key-a")
        assert info.remaining == 2
        assert info.limit == 3

    @pytest.mark.asyncio
    async def test_decrements_remaining(self, limiter):
        await limiter.check("key-a")
        info = await limiter.check("key-a")
        assert info.remaining == 1

    @pytest.mark.asyncio
    async def test_raises_at_limit(self, limiter):
        for _ in range(3):
            await limiter.check("key-a")
        with pytest.raises(RateLimitExceededError):
            await limiter.check("key-a")

    @pytest.mark.asyncio
    async def test_separate_keys_independent(self, limiter):
        for _ in range(3):
            await limiter.check("key-a")
        # key-b should still work
        info = await limiter.check("key-b")
        assert info.remaining == 2

    @pytest.mark.asyncio
    async def test_stale_key_eviction(self, limiter):
        await limiter.check("key-a")
        assert "key-a" in limiter._buckets

        # Force the last eviction time far back and set timestamps to stale
        limiter._last_eviction = 0
        limiter._buckets["key-a"] = [0.0]  # ancient timestamp
        limiter._maybe_evict_stale_keys(9999999999.0)

        assert "key-a" not in limiter._buckets
