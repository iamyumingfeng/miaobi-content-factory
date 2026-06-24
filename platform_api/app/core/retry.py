"""
重试策略组件 (retry.py)

提供可重试错误判断、指数退避延迟计算等功能。

Author: Claude Code
Date: 2025
"""

import random
import asyncio
import logging
from typing import Optional, Set, Type
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryStrategy:
    """
    重试策略类

    提供可重试错误判断和延迟计算功能。
    """

    # 可重试的 HTTP 状态码
    RETRYABLE_HTTP_STATUS_CODES: Set[int] = {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }

    # 可重试的异常类型
    RETRYABLE_EXCEPTIONS: Set[Type[Exception]] = {
        aiohttp.ClientError,
        aiohttp.ServerTimeoutError,
        aiohttp.ClientConnectionError,
        asyncio.TimeoutError,
        ConnectionError,
        TimeoutError,
    }

    @classmethod
    def is_retryable(
        cls,
        error: Exception,
        http_status_code: Optional[int] = None,
    ) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象
            http_status_code: 可选的 HTTP 状态码

        Returns:
            bool: 是否可重试
        """
        # 检查 HTTP 状态码
        if http_status_code and http_status_code in cls.RETRYABLE_HTTP_STATUS_CODES:
            return True

        # 检查异常类型
        for exc_type in cls.RETRYABLE_EXCEPTIONS:
            if isinstance(error, exc_type):
                return True

        # 检查异常消息中的关键词
        error_msg = str(error).lower()
        retryable_keywords = [
            "timeout",
            "timed out",
            "connection",
            "unavailable",
            "temporary",
            "rate limit",
            "too many",
            "server error",
            "500",
            "502",
            "503",
            "504",
        ]

        for keyword in retryable_keywords:
            if keyword in error_msg:
                return True

        return False

    @classmethod
    def get_delay(
        cls,
        attempt: int,
        config: Optional[RetryConfig] = None,
    ) -> float:
        """
        计算指数退避延迟

        Args:
            attempt: 重试次数（从 0 开始）
            config: 重试配置

        Returns:
            float: 延迟时间（秒）
        """
        config = config or RetryConfig()

        # 指数退避计算
        delay = config.base_delay * (config.exponential_base ** attempt)

        # 限制最大延迟
        delay = min(delay, config.max_delay)

        # 添加随机抖动
        if config.jitter:
            # 抖动范围：0.5x - 1.5x
            jitter_factor = 0.5 + random.random()
            delay = delay * jitter_factor

        return delay

    @classmethod
    def should_retry(
        cls,
        attempt: int,
        error: Exception,
        config: Optional[RetryConfig] = None,
        http_status_code: Optional[int] = None,
    ) -> bool:
        """
        判断是否应该重试

        Args:
            attempt: 当前重试次数（从 0 开始）
            error: 异常对象
            config: 重试配置
            http_status_code: 可选的 HTTP 状态码

        Returns:
            bool: 是否应该重试
        """
        config = config or RetryConfig()

        # 检查是否超过最大重试次数
        if attempt >= config.max_retries:
            return False

        # 检查错误是否可重试
        return cls.is_retryable(error, http_status_code)


class RetryableError(Exception):
    """可重试错误"""
    pass


class NonRetryableError(Exception):
    """不可重试错误"""
    pass


class MaxRetriesExceededError(Exception):
    """超过最大重试次数"""

    def __init__(
        self,
        message: str,
        last_error: Optional[Exception] = None,
        total_attempts: int = 0,
    ):
        super().__init__(message)
        self.last_error = last_error
        self.total_attempts = total_attempts


# 默认重试配置
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)

# 保守重试配置（用于敏感操作）
CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=2.5,
    jitter=True,
)

# 快速重试配置（用于非关键操作）
FAST_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=1.5,
    jitter=True,
)
