"""
Redis-based rate limiting using sliding window
"""
import redis.asyncio as redis
from datetime import datetime
from typing import Optional
from app.config import settings


class RateLimiter:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if self.redis is None:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def check_rate_limit(
        self,
        key: str,
        limit: int = None,
        window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """
        Check if rate limit is exceeded using sliding window
        Returns: (allowed, current_count, limit)
        """
        if self.redis is None:
            await self.connect()

        if limit is None:
            limit = settings.RATE_LIMIT_PER_MIN

        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        # Redis key for this rate limit
        redis_key = f"rate_limit:{key}"

        # Use sorted set with timestamps as scores
        pipe = self.redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count current entries in window
        pipe.zcard(redis_key)

        # Add current request
        pipe.zadd(redis_key, {str(now): now})

        # Set expiry on the key
        pipe.expire(redis_key, window_seconds * 2)

        results = await pipe.execute()
        current_count = results[1]

        # Check if limit exceeded
        allowed = current_count < limit

        if not allowed:
            # Remove the request we just added since it's not allowed
            await self.redis.zrem(redis_key, str(now))

        return allowed, current_count + (1 if allowed else 0), limit

    async def get_remaining(self, key: str, limit: int = None, window_seconds: int = 60) -> int:
        """Get remaining requests in current window"""
        if self.redis is None:
            await self.connect()

        if limit is None:
            limit = settings.RATE_LIMIT_PER_MIN

        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        redis_key = f"rate_limit:{key}"

        # Clean old entries and count
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        results = await pipe.execute()

        current_count = results[1]
        remaining = max(0, limit - current_count)

        return remaining

    async def reset(self, key: str):
        """Reset rate limit for a key"""
        if self.redis is None:
            await self.connect()

        redis_key = f"rate_limit:{key}"
        await self.redis.delete(redis_key)


# Global rate limiter instance
rate_limiter = RateLimiter()
