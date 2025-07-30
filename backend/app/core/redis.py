"""
Redis client configuration and caching utilities.
"""

import json
import pickle
from typing import Any, Optional, Union
import aioredis
from app.core.config import settings

"""
Redis client configuration and caching utilities.
"""

import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.core.config import settings

"""
Redis client configuration and caching utilities.
"""

import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.core.config import settings

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=False,
        max_connections=20,
    )


class RedisCache:
    """Redis caching utility class."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        try:
            serialized_value = pickle.dumps(value)
            return await self.redis.setex(key, expire, serialized_value)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(await self.redis.delete(key))
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value.decode('utf-8'))
        except Exception:
            return None
    
    async def set_json(self, key: str, value: dict, expire: int = 3600) -> bool:
        """Set JSON value in cache."""
        try:
            json_value = json.dumps(value)
            return await self.redis.setex(key, expire, json_value)
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache."""
        return await self.redis.incrby(key, amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        return await self.redis.expire(key, seconds)


# Global cache instance
cache: Optional[RedisCache] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client


async def get_cache() -> RedisCache:
    """Get cache instance."""
    if cache is None:
        raise RuntimeError("Redis cache not initialized")
    return cache


async def close_redis():
    """Close Redis connection."""
    if redis_client:
        await redis_client.close()


# Cache key generators
def make_cache_key(*args: Union[str, int]) -> str:
    """Generate cache key from arguments."""
    return ":".join(str(arg) for arg in args)


def review_cache_key(review_id: str) -> str:
    """Generate cache key for review."""
    return make_cache_key("review", review_id)


def agent_response_cache_key(review_id: str, agent_type: str) -> str:
    """Generate cache key for agent response."""
    return make_cache_key("agent_response", review_id, agent_type)


def file_analysis_cache_key(file_hash: str, agent_type: str) -> str:
    """Generate cache key for file analysis."""
    return make_cache_key("file_analysis", file_hash, agent_type)


def repository_cache_key(repo_id: str) -> str:
    """Generate cache key for repository."""
    return make_cache_key("repository", repo_id)
