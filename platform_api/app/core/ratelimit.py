"""
限流组件 (ratelimit.py)

提供令牌桶限流算法和分布式限流功能。

Author: Claude Code
Date: 2025
"""

import time
import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TokenBucketConfig:
    """令牌桶配置"""
    rate: float  # 每秒生成令牌数 (QPS)
    capacity: float  # 桶容量（最大突发量）
    initial_tokens: float = 0.0  # 初始令牌数


class TokenBucket:
    """
    令牌桶限流器

    实现令牌桶算法，用于限制请求速率。
    """

    def __init__(
        self,
        rate: float,
        capacity: float,
        initial_tokens: Optional[float] = None,
    ):
        """
        初始化令牌桶

        Args:
            rate: 每秒生成令牌数 (QPS)
            capacity: 桶容量（最大突发量）
            initial_tokens: 初始令牌数，默认为 capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    async def acquire(
        self,
        tokens: int = 1,
        timeout: float = 30.0,
    ) -> bool:
        """
        获取令牌

        Args:
            tokens: 需要的令牌数
            timeout: 最大等待时间（秒）

        Returns:
            bool: 是否成功获取令牌
        """
        start_time = time.time()

        async with self._lock:
            while True:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

                # 计算需要等待的时间
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate
                wait_time = min(wait_time, 0.1)  # 最多等待100ms
                wait_time = max(wait_time, 0.01)  # 至少等待10ms

                await asyncio.sleep(wait_time)

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌，不等待

        Args:
            tokens: 需要的令牌数

        Returns:
            bool: 是否成功获取令牌
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_available_tokens(self) -> float:
        """获取当前可用令牌数"""
        self._refill()
        return self.tokens


class TokenBucketManager:
    """
    令牌桶管理器

    管理多个平台的令牌桶实例。
    """

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

    async def get_bucket(
        self,
        platform: str,
        config: Optional[TokenBucketConfig] = None,
    ) -> TokenBucket:
        """
        获取或创建平台的令牌桶

        Args:
            platform: 平台名称
            config: 可选的配置，如果不存在则使用默认配置

        Returns:
            TokenBucket: 令牌桶实例
        """
        async with self._lock:
            if platform not in self._buckets:
                if config:
                    bucket = TokenBucket(
                        rate=config.rate,
                        capacity=config.capacity,
                        initial_tokens=config.initial_tokens,
                    )
                else:
                    # 默认配置：QPS=5, 容量=10
                    bucket = TokenBucket(rate=5.0, capacity=10.0)

                self._buckets[platform] = bucket
                logger.info(f"Created token bucket for platform: {platform}")

            return self._buckets[platform]

    def remove_bucket(self, platform: str):
        """移除平台的令牌桶"""
        if platform in self._buckets:
            del self._buckets[platform]
            logger.info(f"Removed token bucket for platform: {platform}")

    def clear_all(self):
        """清除所有令牌桶"""
        self._buckets.clear()
        logger.info("Cleared all token buckets")


# 全局令牌桶管理器
_token_bucket_manager: Optional[TokenBucketManager] = None


def get_token_bucket_manager() -> TokenBucketManager:
    """
    获取令牌桶管理器单例

    Returns:
        TokenBucketManager: 令牌桶管理器实例
    """
    global _token_bucket_manager
    if _token_bucket_manager is None:
        _token_bucket_manager = TokenBucketManager()
    return _token_bucket_manager
