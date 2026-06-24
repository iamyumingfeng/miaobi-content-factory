"""
死信队列管理器 (dlq.py)

提供死信队列管理功能，用于处理超过最大重试次数的任务。

Author: Claude Code
Date: 2025
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DLQStatus(str, Enum):
    """死信队列状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class DLQItem:
    """死信队列项目"""

    id: str
    task_id: Optional[int]
    item_id: Optional[int]
    owner_operator_id: int
    platform: Optional[str]
    error_type: str
    error_message: str
    error_stacktrace: Optional[str]
    created_at: str
    retry_count: int
    status: DLQStatus = DLQStatus.PENDING
    payload: Optional[Dict[str, Any]] = None
    last_attempt_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DLQItem":
        """从字典创建"""
        if "status" in data and isinstance(data["status"], str):
            data["status"] = DLQStatus(data["status"])
        return cls(**data)


class DeadLetterQueue:
    """
    死信队列管理器

    使用 Redis 存储和管理死信队列项目。
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = "dlq:",
    ):
        """
        初始化死信队列管理器

        Args:
            redis_url: Redis 连接 URL
            key_prefix: Redis 键前缀
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.key_prefix = key_prefix
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
            await self._redis.close()
            self._redis = None

    def _get_list_key(self) -> str:
        """获取列表键"""
        return f"{self.key_prefix}items"

    def _get_item_key(self, item_id: str) -> str:
        """获取项目键"""
        return f"{self.key_prefix}item:{item_id}"

    async def add(
        self,
        task_id: Optional[int],
        item_id: Optional[int],
        owner_operator_id: int,
        error: Exception,
        platform: Optional[str] = None,
        retry_count: int = 0,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加项目到死信队列

        Args:
            task_id: 任务 ID
            item_id: 子任务 ID
            owner_operator_id: 创作管理员 ID
            error: 异常对象
            platform: 平台名称
            retry_count: 重试次数
            payload: 附加数据

        Returns:
            str: 死信队列项目 ID
        """
        import traceback

        redis_client = await self._get_redis()

        # 生成项目 ID
        dlq_item_id = f"{int(datetime.utcnow().timestamp())}_{task_id or 'no-task'}_{item_id or 'no-item'}"

        # 创建死信队列项目
        dlq_item = DLQItem(
            id=dlq_item_id,
            task_id=task_id,
            item_id=item_id,
            owner_operator_id=owner_operator_id,
            platform=platform,
            error_type=type(error).__name__,
            error_message=str(error),
            error_stacktrace=traceback.format_exc(),
            created_at=datetime.utcnow().isoformat(),
            retry_count=retry_count,
            status=DLQStatus.PENDING,
            payload=payload,
        )

        # 存储到 Redis
        item_key = self._get_item_key(dlq_item_id)
        list_key = self._get_list_key()

        await redis_client.set(item_key, json.dumps(dlq_item.to_dict()))
        await redis_client.lpush(list_key, dlq_item_id)

        logger.info(f"Added item to DLQ: {dlq_item_id}")

        return dlq_item_id

    async def get(self, item_id: str) -> Optional[DLQItem]:
        """
        获取死信队列项目

        Args:
            item_id: 项目 ID

        Returns:
            Optional[DLQItem]: 死信队列项目
        """
        redis_client = await self._get_redis()

        item_key = self._get_item_key(item_id)
        data = await redis_client.get(item_key)

        if not data:
            return None

        return DLQItem.from_dict(json.loads(data))

    async def list(
        self,
        owner_operator_id: Optional[int] = None,
        status: Optional[DLQStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DLQItem]:
        """
        获取死信队列项目列表

        Args:
            owner_operator_id: 可选的创作管理员 ID 过滤
            status: 可选的状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[DLQItem]: 死信队列项目列表
        """
        redis_client = await self._get_redis()

        list_key = self._get_list_key()
        item_ids = await redis_client.lrange(list_key, offset, offset + limit - 1)

        items = []
        for item_id in item_ids:
            item = await self.get(item_id)
            if item:
                if owner_operator_id and item.owner_operator_id != owner_operator_id:
                    continue
                if status and item.status != status:
                    continue
                items.append(item)

        return items

    async def count(
        self,
        owner_operator_id: Optional[int] = None,
        status: Optional[DLQStatus] = None,
    ) -> int:
        """
        获取死信队列项目数量

        Args:
            owner_operator_id: 可选的创作管理员 ID 过滤
            status: 可选的状态过滤

        Returns:
            int: 项目数量
        """
        items = await self.list(owner_operator_id, status, limit=10000)
        return len(items)

    async def update_status(
        self,
        item_id: str,
        status: DLQStatus,
    ) -> bool:
        """
        更新死信队列项目状态

        Args:
            item_id: 项目 ID
            status: 新状态

        Returns:
            bool: 是否成功
        """
        item = await self.get(item_id)
        if not item:
            return False

        redis_client = await self._get_redis()

        item.status = status
        if status == DLQStatus.COMPLETED:
            item.completed_at = datetime.utcnow().isoformat()

        item_key = self._get_item_key(item_id)
        await redis_client.set(item_key, json.dumps(item.to_dict()))

        logger.info(f"Updated DLQ item status: {item_id} -> {status}")

        return True

    async def remove(self, item_id: str) -> bool:
        """
        移除死信队列项目

        Args:
            item_id: 项目 ID

        Returns:
            bool: 是否成功
        """
        redis_client = await self._get_redis()

        item_key = self._get_item_key(item_id)
        list_key = self._get_list_key()

        # 从列表中移除
        await redis_client.lrem(list_key, 0, item_id)

        # 删除项目
        deleted = await redis_client.delete(item_key)

        logger.info(f"Removed DLQ item: {item_id}")

        return deleted > 0

    async def archive(self, item_id: str) -> bool:
        """
        归档死信队列项目

        Args:
            item_id: 项目 ID

        Returns:
            bool: 是否成功
        """
        return await self.update_status(item_id, DLQStatus.ARCHIVED)

    async def clear_archived(self, older_than_days: int = 30) -> int:
        """
        清理已归档的项目

        Args:
            older_than_days: 保留天数

        Returns:
            int: 清理的项目数量
        """
        from datetime import timedelta

        items = await self.list(status=DLQStatus.ARCHIVED, limit=10000)

        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        cleared_count = 0

        for item in items:
            try:
                created_at = datetime.fromisoformat(item.created_at)
                if created_at < cutoff:
                    await self.remove(item.id)
                    cleared_count += 1
            except Exception:
                pass

        logger.info(f"Cleared {cleared_count} archived DLQ items")

        return cleared_count


# 全局死信队列管理器
_dlq_manager: Optional[DeadLetterQueue] = None


def get_dlq_manager() -> DeadLetterQueue:
    """
    获取死信队列管理器单例

    Returns:
        DeadLetterQueue: 死信队列管理器实例
    """
    global _dlq_manager
    if _dlq_manager is None:
        _dlq_manager = DeadLetterQueue()
    return _dlq_manager
