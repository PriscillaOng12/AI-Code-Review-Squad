"""Simple rate limiting per API key/tenant using token bucket algorithm."""

import time
from typing import Dict
from fastapi import HTTPException, status


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, TokenBucket] = {}

    def check(self, key: str) -> None:
        bucket = self.buckets.setdefault(key, TokenBucket(self.capacity, self.refill_rate))
        if not bucket.consume():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")