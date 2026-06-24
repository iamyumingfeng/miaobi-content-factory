"""
并发控制组件 (concurrency.py)

提供基于 Redis 的分布式并发计数和控制功能。

Author: Claude Code
Date: 2025
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DistributedConcurrencyLimiter:
    """
    分布式并发限制器

    使用 Redis 实现跨进程/跨机器的并发计数。
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = "concurrency:",
        default_limit: int = 5,
    ):
        """
        初始化分布式并发限制器

        Args:
            redis_url: Redis 连接 URL
            key_prefix: Redis 键前缀
            default_limit: 默认并发限制
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.key_prefix = key_prefix
        self.default_limit = default_limit
        self._redis: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> redis.Redis:
        """获取 Redis 连接"""
        async with self._lock:
            if self._redis is None or self._redis.connection is None:
                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            return self._redis

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None

    def _get_key(self, platform: str) -> str:
        """获取 Redis 键"""
        return f"{self.key_prefix}{platform}"

    async def acquire(
        self,
        platform: str,
        limit: Optional[int] = None,
        timeout: float = 30.0,
    ) -> bool:
        """
        获取并发槽位

        Args:
            platform: 平台名称
            limit: 并发限制，默认使用 default_limit
            timeout: 最大等待时间（秒）

        Returns:
            bool: 是否成功获取槽位
        """
        limit = limit or self.default_limit
        key = self._get_key(platform)

        try:
            redis_client = await self._get_redis()
            start_time = asyncio.get_event_loop().time()

            while True:
                # 使用 INCR 获取当前计数
                current = await redis_client.incr(key)

                if current <= limit:
                    # 设置过期时间，防止死锁
                    await redis_client.expire(key, 3600)  # 1小时过期
                    return True

                # 超过限制，回滚计数
                await redis_client.decr(key)

                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    return False

                # 等待后重试
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to acquire concurrency slot for {platform}: {e}")
            return False

    async def try_acquire(
        self,
        platform: str,
        limit: Optional[int] = None,
    ) -> bool:
        """
        尝试获取并发槽位，不等待

        Args:
            platform: 平台名称
            limit: 并发限制，默认使用 default_limit

        Returns:
            bool: 是否成功获取槽位
        """
        limit = limit or self.default_limit
        key = self._get_key(platform)

        try:
            redis_client = await self._get_redis()
            current = await redis_client.incr(key)

            if current <= limit:
                await redis_client.expire(key, 3600)
                return True

            await redis_client.decr(key)
            return False
        except Exception as e:
            logger.error(f"Failed to try_acquire concurrency slot for {platform}: {e}")
            return False

    async def release(self, platform: str):
        """
        释放并发槽位

        Args:
            platform: 平台名称
        """
        key = self._get_key(platform)

        try:
            redis_client = await self._get_redis()
            current = await redis_client.decr(key)

            # 确保计数不会低于 0
            if current < 0:
                await redis_client.set(key, 0)
        except Exception as e:
            logger.error(f"Failed to release concurrency slot for {platform}: {e}")

    async def get_current_count(self, platform: str) -> int:
        """
        获取当前并发数

        Args:
            platform: 平台名称

        Returns:
            int: 当前并发数
        """
        key = self._get_key(platform)

        try:
            redis_client = await self._get_redis()
            count = await redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get current count for {platform}: {e}")
            return 0

    async def reset(self, platform: str):
        """
        重置平台的并发计数

        Args:
            platform: 平台名称
        """
        key = self._get_key(platform)

        try:
            redis_client = await self._get_redis()
            await redis_client.delete(key)
            logger.info(f"Reset concurrency counter for platform: {platform}")
        except Exception as e:
            logger.error(f"Failed to reset concurrency counter for {platform}: {e}")

    @asynccontextmanager
    async def acquire_context(
        self,
        platform: str,
        limit: Optional[int] = None,
        timeout: float = 30.0,
    ):
        """
        并发控制上下文管理器

        Args:
            platform: 平台名称
            limit: 并发限制
            timeout: 最大等待时间

        Yields:
            bool: 是否成功获取槽位
        """
        acquired = await self.acquire(platform, limit, timeout)
        try:
            yield acquired
        finally:
            if acquired:
                await self.release(platform)


# 全局分布式并发限制器
_concurrency_limiter: Optional[DistributedConcurrencyLimiter] = None


def get_concurrency_limiter() -> DistributedConcurrencyLimiter:
    """
    获取分布式并发限制器单例

    Returns:
        DistributedConcurrencyLimiter: 并发限制器实例
    """
    global _concurrency_limiter
    if _concurrency_limiter is None:
        _concurrency_limiter = DistributedConcurrencyLimiter()
    return _concurrency_limiter
