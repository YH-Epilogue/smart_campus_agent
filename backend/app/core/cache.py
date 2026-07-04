"""
Cache module: Redis cache with in-memory fallback
"""
import json
import time
from typing import Any, Optional


class MemoryCache:
    """Simple in-memory cache with TTL"""
    def __init__(self):
        self._store = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._store[key]
            del self._ttl[key]
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        self._store[key] = value
        self._ttl[key] = time.time() + ttl

    def delete(self, key: str):
        self._store.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        self._store.clear()
        self._ttl.clear()


class CacheManager:
    """Cache manager with Redis backend and memory fallback"""
    def __init__(self):
        self._redis = None
        self._memory = MemoryCache()
        self._try_connect_redis()

    def _try_connect_redis(self):
        try:
            import redis
            self._redis = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._redis.ping()
            print("[Cache] Redis connected")
        except Exception:
            print("[Cache] Redis not available, using memory cache")
            self._redis = None

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                value = self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        self._memory.set(key, value, ttl)

    def delete(self, key: str):
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory.delete(key)

    def clear(self):
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass
        self._memory.clear()


# Global cache instance
cache = CacheManager()
