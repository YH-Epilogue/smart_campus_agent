"""
缓存模块 — 带内存降级的双层缓存系统

优先使用 Redis 作为缓存后端；若 Redis 不可用则自动降级为内存缓存。
所有 get/set/delete 操作同时写入两层，读取时优先读 Redis，失败时 fallback 到内存。
适用于开发环境（无 Redis）和生产环境（有 Redis）的无缝切换。
"""
import json
import time
from typing import Any, Optional


class MemoryCache:
    """基于字典的内存缓存，支持 TTL 过期淘汰"""
    def __init__(self):
        self._store = {}   # key -> value
        self._ttl = {}     # key -> 过期时间戳（Unix 时间）

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，已过期则删除并返回 None"""
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._store[key]
            del self._ttl[key]
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值，默认 TTL 为 300 秒（5 分钟）"""
        self._store[key] = value
        self._ttl[key] = time.time() + ttl

    def delete(self, key: str):
        """删除指定缓存项，key 不存在时静默忽略"""
        self._store.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        """清空全部缓存"""
        self._store.clear()
        self._ttl.clear()


class CacheManager:
    """双层缓存管理器：Redis 优先，内存兜底"""
    def __init__(self):
        self._redis = None
        self._memory = MemoryCache()
        self._try_connect_redis()

    def _try_connect_redis(self):
        """
        尝试连接本地 Redis，2 秒超时。
        连接失败时静默降级，不会阻塞应用启动。
        """
        try:
            import redis
            self._redis = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._redis.ping()  # 验证连接可用性
            print("[Cache] Redis connected")
        except Exception:
            print("[Cache] Redis not available, using memory cache")
            self._redis = None

    def get(self, key: str) -> Optional[Any]:
        """优先从 Redis 读取，失败则 fallback 到内存缓存"""
        if self._redis:
            try:
                value = self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        return self._memory.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        """同时写入 Redis（如可用）和内存缓存，确保双层数据一致"""
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        self._memory.set(key, value, ttl)

    def delete(self, key: str):
        """同时从 Redis 和内存缓存中删除指定 key"""
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory.delete(key)

    def clear(self):
        """清空全部缓存（Redis 使用 flushdb，内存直接清字典）"""
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass
        self._memory.clear()


# 全局缓存实例，应用内通过 from ..cache import cache 引用
cache = CacheManager()
