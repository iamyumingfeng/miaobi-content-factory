"""
异步 Embedding 保存服务 (async_embedding_service.py)

在分阶段架构下，embedding 保存采用单条异步模式：
- 去重检测后直接异步保存
- 无需批量处理
- 自动重试机制

Author: Claude Code
Date: 2026-05-10
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentEmbedding
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingSaveRequest:
    """Embedding 保存请求"""
    item_id: int
    owner_operator_id: int
    task_id: int
    content_type: str  # "text" or "image"
    content: str
    content_hash: str
    embedding: List[float]
    content_index: int = 0
    max_retries: int = 3


class AsyncEmbeddingService:
    """
    异步 Embedding 保存服务

    在分阶段架构下，embedding 保存简化为单条异步模式：
    - 去重检测后直接调用 save_embedding_async
    - 自动重试（指数退避）
    - 不阻塞主流程
    """

    # 重试配置
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5  # 秒
    MAX_RETRY_DELAY = 10.0  # 秒

    @classmethod
    async def save_embedding_async(
        cls,
        request: EmbeddingSaveRequest,
    ) -> bool:
        """
        异步保存单个 embedding（带重试）

        在分阶段架构中，此方法在去重检测后直接调用，
        使用独立 session，不与主事务竞争。

        Args:
            request: Embedding 保存请求

        Returns:
            是否保存成功
        """
        for retry in range(request.max_retries):
            try:
                async with async_session_maker() as db:
                    content_preview = request.content[:500] if len(request.content) > 500 else request.content

                    record = ContentEmbedding(
                        owner_operator_id=request.owner_operator_id,
                        generation_item_id=request.item_id,
                        task_id=request.task_id,
                        content_type=request.content_type,
                        content_index=request.content_index,
                        embedding=request.embedding,
                        content_preview=content_preview,
                        content_hash=request.content_hash,
                        used_for_dedup_count=0,
                        created_at=datetime.now(timezone.utc),
                    )

                    db.add(record)
                    await db.commit()

                    logger.debug("[AsyncEmbedding] 保存成功 | item_id=%s | type=%s",
                               request.item_id, request.content_type)
                    return True

            except Exception as e:
                error_str = str(e)
                is_lock_timeout = "Lock wait timeout" in error_str or "1205" in error_str

                if is_lock_timeout and retry < request.max_retries - 1:
                    # 指数退避重试
                    delay = min(cls.BASE_RETRY_DELAY * (2 ** retry), cls.MAX_RETRY_DELAY)
                    logger.warning("[AsyncEmbedding] 锁超时，%s秒后重试 (%s/%s) | item_id=%s",
                                 delay, retry + 1, request.max_retries, request.item_id)
                    await asyncio.sleep(delay)
                else:
                    logger.error("[AsyncEmbedding] 保存失败 | item_id=%s | error=%s",
                                request.item_id, error_str[:200])
                    return False

        return False