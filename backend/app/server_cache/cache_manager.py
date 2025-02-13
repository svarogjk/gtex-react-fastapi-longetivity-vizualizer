import redis
import pickle
import functools
from typing import Any, Callable, Optional
from app.utils.helpers import logger


class CacheManager:
    _instance = None
    _redis_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._redis_client:
            self._redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=False,  # Keep as binary for pickle
            )

    def memoize(self, timeout: int = 36000, response_filter: Optional[Callable] = None):
        """
        Decorator for caching function results in Redis
        Args:
            timeout: Cache timeout in seconds
            response_filter: Optional function to filter/validate responses
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key = f"{func.__module__}:{func.__name__}:"
                key += ":".join([str(arg) for arg in args])
                key += ":".join([f"{k}={v}" for k, v in sorted(kwargs.items())])

                try:
                    # Try to get from cache
                    cached = self._redis_client.get(key)
                    if cached:
                        result = pickle.loads(cached)
                        if response_filter and not response_filter(result):
                            # If response filter fails, delete cached result
                            self._redis_client.delete(key)
                        else:
                            logger.debug(f"Cache hit for key: {key}")
                            return result

                    # Execute function if not in cache
                    result = await func(*args, **kwargs)

                    # Apply response filter if provided
                    if response_filter and not response_filter(result):
                        logger.warning(f"Response filter failed for key: {key}")
                        return result

                    # Cache the result
                    self._redis_client.setex(key, timeout, pickle.dumps(result))
                    logger.debug(f"Cached result for key: {key}")
                    return result

                except Exception as e:
                    logger.error(f"Cache error for key {key}: {str(e)}")
                    # Execute function without caching on error
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def set(self, key: str, value: Any, timeout: int = 3600):
        """Set a value in cache with timeout"""
        try:
            self._redis_client.setex(key, timeout, pickle.dumps(value))
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            data = self._redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
        return None

    def delete(self, key: str):
        """Delete a key from cache"""
        try:
            self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")


# Initialize cache manager
cache = CacheManager()
