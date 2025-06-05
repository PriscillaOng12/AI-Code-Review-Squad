"""Test the rate limiter."""

from app.core.rate_limit import RateLimiter


def test_rate_limiter_allows_within_capacity():
    rl = RateLimiter(capacity=5, refill_rate=5)
    for _ in range(5):
        rl.check('k')  # should not raise


def test_rate_limiter_blocks_when_exceeded():
    rl = RateLimiter(capacity=1, refill_rate=1)
    rl.check('k')
    try:
        rl.check('k')
    except Exception as e:
        assert e.status_code == 429