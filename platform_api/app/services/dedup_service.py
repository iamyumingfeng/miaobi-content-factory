"""
去重检测服务 (dedup_service.py)

使用向量嵌入 + 相似度检测，实现内容去重功能。
优化版本：
- 使用独立的 content_embedding 表存储 embedding
- 文案和图片分别去重（文案 vs 文案，图片 vs 图片）
- 对比同一创作管理员下所有创作者的内容
- 完整的使用日志记录

默认阈值为 80%，超过阈值的文案将被判定为重复。

Author: Claude Code
Date: 2026
"""

import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.config import get_model_config_manager
from app.adapters.factory import ModelAdapterFactory
from app.models import ContentEmbedding, GenerationItem

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型枚举"""

    TEXT = "text"
    IMAGE = "image"


@dataclass
class DedupResult:
    """去重检测结果"""

    passed: bool
    max_similarity: float
    references: List[Dict]
    checked_at: str
    content_type: ContentType
    error: Optional[str] = None
    embedding: Optional[List[float]] = None  # 当前内容的 embedding，用于缓存


class DedupService:
    """
    内容去重检测服务（优化版 - 使用独立表）

    使用文本嵌入 + 余弦相似度计算，对生成的文案进行去重检测。
    优化特性：
    - 独立的 content_embedding 表存储所有 embedding
    - 文案和图片分别去重
    - 完整的元数据记录（用户、任务、类型、创建时间）
    - 使用统计（使用次数、最后使用时间）
    - 内容哈希用于快速查找
    """

    # 默认阈值（文案去重建议使用 85-90%，避免结构相似导致的误判）
    DEFAULT_THRESHOLD = 0.90
    # 最大重试次数
    DEFAULT_MAX_RETRIES = 3
    # 最大历史参考数量
    DEFAULT_MAX_REFERENCES = 100

    @classmethod
    async def check_text_duplication(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        text: str,
        threshold: float = DEFAULT_THRESHOLD,
        max_references: int = DEFAULT_MAX_REFERENCES,
    ) -> DedupResult:
        """
                检测文案是否与历史内容重复

                Args:
                    db: 数据库会话
                    item: 当前生成项
                    text: 待检测的文案内容
                    threshold: 相似度阈值，默认 0.8
                    max_references: 最大参考数量，默认 100

        Returns:
                    DedupResult: 去重检测结果
        """
        from datetime import datetime

        checked_at = datetime.utcnow()

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_text_duplication 开始 | owner=%s | text_len=%s | threshold=%s | max_ref=%s",
            item.owner_operator_id,
            len(text),
            threshold,
            max_references,
        )
        logger.info("[Dedup] 待检测文案内容: %s", text[:300] if text else "")

        # 1. 计算内容哈希
        content_hash = cls._compute_content_hash(text)
        logger.info("[Dedup] 内容哈希: %s", content_hash)

        # 2. 获取已有 embedding 或计算新的（延迟保存）
        existing_record, new_embedding = await cls._get_or_create_embedding(
            db, item, ContentType.TEXT, text, content_hash, content_index=0
        )

        # 优先使用已有记录
        if existing_record and existing_record.embedding:
            current_embedding = existing_record.embedding
            exclude_embedding_id = existing_record.id
        elif new_embedding:
            current_embedding = new_embedding
            exclude_embedding_id = None  # 新记录尚未保存
        else:
            logger.warning("[Dedup] 无法获取文案嵌入向量，跳过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.TEXT,
                error="Failed to get text embedding",
            )

        # 3. 获取历史 embedding 记录
        historical_records = await cls._get_historical_embeddings(
            db,
            item.owner_operator_id,
            ContentType.TEXT,
            max_references,
            exclude_embedding_id=exclude_embedding_id,
        )

        if not historical_records:
            logger.info("[Dedup] 无历史文案参考内容，通过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.TEXT,
            )

        # 4. 计算与历史内容的相似度
        references = []
        max_similarity = 0.0
        used_record_ids = []

        for hist_record in historical_records:
            hist_embedding = hist_record.embedding
            if not hist_embedding:
                continue

            # 计算余弦相似度
            similarity = cls._cosine_similarity(current_embedding, hist_embedding)
            if similarity >= threshold:
                references.append(
                    {
                        "embedding_id": hist_record.id,
                        "item_id": hist_record.generation_item_id,
                        "task_id": hist_record.task_id,
                        "similarity": round(similarity, 4),
                        "content_type": "text",
                        "content_preview": hist_record.content_preview or "",
                        "created_at": (
                            hist_record.created_at.isoformat()
                            if hist_record.created_at
                            else None
                        ),
                    }
                )
                max_similarity = max(max_similarity, similarity)
                used_record_ids.append(hist_record.id)

            logger.debug(
                "[Dedup] 文案相似度计算 | embedding_id=%s | similarity=%.4f",
                hist_record.id,
                similarity,
            )

        # 5. 更新历史记录的使用统计
        if used_record_ids:
            await cls._update_usage_stats(db, used_record_ids)

        # 6. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[:5]

        passed = max_similarity < threshold

        result = DedupResult(
            passed=passed,
            max_similarity=round(max_similarity, 4),
            references=references,
            checked_at=checked_at.isoformat(),
            content_type=ContentType.TEXT,
            embedding=new_embedding,  # 返回新计算的 embedding 供延迟保存
        )

        logger.info(
            "[Dedup] 文案检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s",
            passed,
            max_similarity,
            len(references),
        )

        return result

    @classmethod
    async def check_text_duplication_for_subuser(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        text: str,
        threshold: float = DEFAULT_THRESHOLD,
        max_references: int = DEFAULT_MAX_REFERENCES,
        save_embedding: bool = True,
        benchmark_text: Optional[str] = None,
        benchmark_text_enabled: bool = False,
    ) -> DedupResult:
        """
        检测文案是否与该创作者的历史内容重复

        查询该创作者已分发/已发布的历史内容进行去重检测，
        并可选保存当前文案的 embedding 以供后续检测使用。

        Args:
            db: 数据库会话
            item: 当前生成项（用于获取 sub_user_id、owner_operator_id）
            text: 待检测的文案内容
            threshold: 相似度阈值，默认 0.8
            max_references: 最大参考数量，默认 100
            save_embedding: 是否保存当前 embedding，默认 True
            benchmark_text: 对标文案内容（可选）
            benchmark_text_enabled: 对标文案参考开关，默认 False

        Returns:
            DedupResult: 去重检测结果
        """
        from datetime import datetime

        checked_at = datetime.utcnow()
        sub_user_id = item.sub_user_id
        owner_operator_id = item.owner_operator_id

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_text_duplication_for_subuser 开始 | sub_user=%s | owner=%s | text_len=%s | threshold=%s | benchmark_enabled=%s",
            sub_user_id,
            owner_operator_id,
            len(text),
            threshold,
            benchmark_text_enabled,
        )
        logger.info("[Dedup] 待检测文案内容: %s", text[:300] if text else "")

        # 1. 计算内容哈希
        content_hash = cls._compute_content_hash(text)
        logger.info("[Dedup] 内容哈希: %s", content_hash)

        # 2. 计算当前文案的 embedding
        current_embedding = await cls._get_embedding(db, text)
        if not current_embedding:
            logger.warning("[Dedup] 无法获取文案嵌入向量，跳过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.TEXT,
                error="Failed to get text embedding",
            )

        references = []
        max_similarity = 0.0

        # 3. 如果对标文案参考开关打开，先与对标文案比对
        if benchmark_text_enabled and benchmark_text:
            logger.info("[Dedup] 对标文案检测 | benchmark_len=%s", len(benchmark_text))
            benchmark_embedding = await cls._get_embedding(db, benchmark_text)
            if benchmark_embedding:
                benchmark_similarity = cls._cosine_similarity(
                    current_embedding, benchmark_embedding
                )
                logger.info("[Dedup] 与对标文案相似度: %.4f", benchmark_similarity)

                if benchmark_similarity >= threshold:
                    references.append(
                        {
                            "embedding_id": None,
                            "item_id": None,
                            "task_id": None,
                            "similarity": round(benchmark_similarity, 4),
                            "content_type": "benchmark_text",
                            "content_preview": (
                                benchmark_text[:200] if benchmark_text else ""
                            ),
                            "created_at": checked_at.isoformat(),
                            "source": "对标文案",
                        }
                    )
                    max_similarity = max(max_similarity, benchmark_similarity)
                    logger.warning(
                        "[Dedup] 生成文案与对标文案相似度过高 | similarity=%.4f",
                        benchmark_similarity,
                    )
            else:
                logger.warning("[Dedup] 无法获取对标文案嵌入向量")

        # 4. 获取该创作者的历史 embedding 记录（排除当前 item）
        historical_records = await cls._get_subuser_historical_embeddings(
            db,
            sub_user_id,
            owner_operator_id,
            ContentType.TEXT,
            max_references,
            exclude_item_id=item.id if save_embedding else None,
        )

        if historical_records:
            # 5. 计算与历史内容的相似度
            for hist_record in historical_records:
                hist_embedding = hist_record.embedding
                if not hist_embedding:
                    continue

                # 计算余弦相似度
                similarity = cls._cosine_similarity(current_embedding, hist_embedding)
                if similarity >= threshold:
                    references.append(
                        {
                            "embedding_id": hist_record.id,
                            "item_id": hist_record.generation_item_id,
                            "task_id": hist_record.task_id,
                            "similarity": round(similarity, 4),
                            "content_type": "text",
                            "content_preview": hist_record.content_preview or "",
                            "created_at": (
                                hist_record.created_at.isoformat()
                                if hist_record.created_at
                                else None
                            ),
                            "source": "历史内容",
                        }
                    )
                    max_similarity = max(max_similarity, similarity)

                logger.debug(
                    "[Dedup] 创作者文案相似度计算 | embedding_id=%s | similarity=%.4f",
                    hist_record.id,
                    similarity,
                )

        # 6. 如果无历史记录且无对标文案比对
        if not historical_records and not (benchmark_text_enabled and benchmark_text):
            logger.info("[Dedup] 创作者无历史文案且无对标文案，通过检测")

            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.TEXT,
                embedding=(
                    current_embedding if save_embedding else None
                ),  # 返回 embedding 供延迟保存
            )

        # 7. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[:5]

        passed = max_similarity < threshold

        result = DedupResult(
            passed=passed,
            max_similarity=round(max_similarity, 4),
            references=references,
            checked_at=checked_at.isoformat(),
            content_type=ContentType.TEXT,
            embedding=(
                current_embedding if save_embedding else None
            ),  # 返回 embedding 供延迟保存
        )

        logger.info(
            "[Dedup] 创作者文案检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s",
            passed,
            max_similarity,
            len(references),
        )

        return result

    @classmethod
    async def check_text_duplication_with_scope(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        text: str,
        scope: List[str],
        task_id: int,
        task_embeddings_cache: Optional[Dict[int, Tuple[List[float], str]]] = None,
        benchmark_text: Optional[str] = None,
        benchmark_text_enabled: bool = False,
        threshold: float = DEFAULT_THRESHOLD,
        max_references: int = DEFAULT_MAX_REFERENCES,
        save_embedding: bool = True,
    ) -> DedupResult:
        """
        按指定范围检测文案是否重复

        Args:
            db: 数据库会话
            item: 当前生成项
            text: 待检测的文案内容
            scope: 去重范围配置 ["subuser_history", "current_task", "all_history"]
            task_id: 当前任务ID
            task_embeddings_cache: 当前任务已生成内容的 embedding 缓存 {item_id: (embedding, content_preview)}
            benchmark_text: 对标文案内容
            benchmark_text_enabled: 对标文案参考开关
            threshold: 相似度阈值
            max_references: 每个范围的最大参考数量
            save_embedding: 是否保存当前 embedding

        Returns:
            DedupResult: 去重检测结果，包含 embedding 用于缓存
        """
        from datetime import datetime

        checked_at = datetime.utcnow()
        sub_user_id = item.sub_user_id
        owner_operator_id = item.owner_operator_id

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_text_duplication_with_scope 开始 | item_id=%s | sub_user=%s | scope=%s | threshold=%s",
            item.id,
            sub_user_id,
            scope,
            threshold,
        )
        logger.info("[Dedup] 待检测文案内容: %s", text[:200] if text else "")

        # 1. 计算当前文案的 embedding（只计算一次）
        current_embedding = await cls._get_embedding(db, text)
        if not current_embedding:
            logger.warning("[Dedup] 无法获取文案嵌入向量，跳过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.TEXT,
                error="Failed to get text embedding",
            )

        references = []
        max_similarity = 0.0

        # 3. 对标文案检测（如果启用）
        if benchmark_text_enabled and benchmark_text:
            logger.info("[Dedup] 对标文案检测 | benchmark_len=%s", len(benchmark_text))
            benchmark_embedding = await cls._get_embedding(db, benchmark_text)
            if benchmark_embedding:
                benchmark_similarity = cls._cosine_similarity(
                    current_embedding, benchmark_embedding
                )
                logger.info("[Dedup] 与对标文案相似度: %.4f", benchmark_similarity)
                if benchmark_similarity >= threshold:
                    references.append(
                        {
                            "embedding_id": None,
                            "item_id": None,
                            "task_id": None,
                            "similarity": round(benchmark_similarity, 4),
                            "content_type": "benchmark_text",
                            "content_preview": (
                                benchmark_text[:200] if benchmark_text else ""
                            ),
                            "created_at": checked_at.isoformat(),
                            "source": "对标文案",
                        }
                    )
                    max_similarity = max(max_similarity, benchmark_similarity)
                    logger.warning(
                        "[Dedup] 生成文案与对标文案相似度过高 | similarity=%.4f",
                        benchmark_similarity,
                    )

        # 4. 按 scope 配置检测
        for scope_item in scope:
            if scope_item == "subuser_history":
                # 当前创作者历史
                logger.debug(
                    "[Dedup] 检测范围: subuser_history | sub_user_id=%s", sub_user_id
                )
                hist_records = await cls._get_subuser_historical_embeddings(
                    db,
                    sub_user_id,
                    owner_operator_id,
                    ContentType.TEXT,
                    max_references,
                    exclude_item_id=item.id,
                )
                for rec in hist_records:
                    if rec.embedding:
                        sim = cls._cosine_similarity(current_embedding, rec.embedding)
                        if sim >= threshold:
                            references.append(
                                {
                                    "embedding_id": rec.id,
                                    "item_id": rec.generation_item_id,
                                    "task_id": rec.task_id,
                                    "similarity": round(sim, 4),
                                    "content_type": "text",
                                    "content_preview": rec.content_preview or "",
                                    "created_at": (
                                        rec.created_at.isoformat()
                                        if rec.created_at
                                        else None
                                    ),
                                    "source": "当前创作者历史",
                                }
                            )
                            max_similarity = max(max_similarity, sim)
                        logger.debug(
                            "[Dedup] subuser_history 相似度 | embedding_id=%s | sim=%.4f",
                            rec.id,
                            sim,
                        )

            elif scope_item == "current_task":
                # 当前任务所有子任务
                logger.debug(
                    "[Dedup] 检测范围: current_task | task_id=%s | cache_count=%s",
                    task_id,
                    len(task_embeddings_cache or {}),
                )
                if task_embeddings_cache:
                    for other_item_id, (
                        other_emb,
                        other_preview,
                    ) in task_embeddings_cache.items():
                        if other_item_id != item.id:  # 排除当前 item
                            sim = cls._cosine_similarity(current_embedding, other_emb)
                            if sim >= threshold:
                                references.append(
                                    {
                                        "embedding_id": None,
                                        "item_id": other_item_id,
                                        "task_id": task_id,
                                        "similarity": round(sim, 4),
                                        "content_type": "text",
                                        "content_preview": other_preview,
                                        "created_at": checked_at.isoformat(),
                                        "source": "当前任务其他子任务",
                                    }
                                )
                                max_similarity = max(max_similarity, sim)
                            logger.debug(
                                "[Dedup] current_task 相似度 | item_id=%s | sim=%.4f",
                                other_item_id,
                                sim,
                            )

            elif scope_item == "all_history":
                # 所有生成文案历史
                logger.debug(
                    "[Dedup] 检测范围: all_history | owner=%s", owner_operator_id
                )
                hist_records = await cls._get_historical_embeddings(
                    db,
                    owner_operator_id,
                    ContentType.TEXT,
                    max_references,
                    exclude_embedding_id=None,
                )
                for rec in hist_records:
                    if rec.embedding and rec.generation_item_id != item.id:
                        sim = cls._cosine_similarity(current_embedding, rec.embedding)
                        if sim >= threshold:
                            references.append(
                                {
                                    "embedding_id": rec.id,
                                    "item_id": rec.generation_item_id,
                                    "task_id": rec.task_id,
                                    "similarity": round(sim, 4),
                                    "content_type": "text",
                                    "content_preview": rec.content_preview or "",
                                    "created_at": (
                                        rec.created_at.isoformat()
                                        if rec.created_at
                                        else None
                                    ),
                                    "source": "所有历史内容",
                                }
                            )
                            max_similarity = max(max_similarity, sim)
                        logger.debug(
                            "[Dedup] all_history 相似度 | embedding_id=%s | sim=%.4f",
                            rec.id,
                            sim,
                        )

        # 5. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[
            :10
        ]

        passed = max_similarity < threshold

        result = DedupResult(
            passed=passed,
            max_similarity=round(max_similarity, 4),
            references=references,
            checked_at=checked_at.isoformat(),
            content_type=ContentType.TEXT,
            embedding=(
                current_embedding if save_embedding else None
            ),  # 返回 embedding 供延迟保存
        )

        logger.info(
            "[Dedup] 检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s | scope=%s",
            passed,
            max_similarity,
            len(references),
            scope,
        )

        # 调试：打印 references 的 content_preview 长度
        if references:
            for i, ref in enumerate(references[:3]):
                logger.debug(
                    "[Dedup] Reference[%s] | sim=%.4f | preview_len=%s | preview=%s",
                    i,
                    ref.get("similarity", 0),
                    len(ref.get("content_preview", "")),
                    (
                        ref.get("content_preview", "")[:100]
                        if ref.get("content_preview")
                        else None
                    ),
                )

        return result

    @classmethod
    async def _get_subuser_historical_embeddings(
        cls,
        db: AsyncSession,
        sub_user_id: int,
        owner_operator_id: int,
        content_type: ContentType,
        limit: int = 100,
        exclude_item_id: Optional[int] = None,
    ) -> List[ContentEmbedding]:
        """
        获取创作者的历史 embedding 记录

        查询该创作者已分发/已发布状态的历史内容。

        Args:
            db: 数据库会话
            sub_user_id: 创作者ID
            owner_operator_id: 创作管理员ID
            content_type: 内容类型
            limit: 最大数量
            exclude_item_id: 排除的 item ID（通常是当前正在检测的 item）

        Returns:
            ContentEmbedding 记录列表
        """
        from app.models import GenerationItem

        # 查询该创作者已分发/已发布的历史内容
        # distribution_status: 'distributed', 'pending_publish', 'published'
        conditions = [
            GenerationItem.sub_user_id == sub_user_id,
            GenerationItem.owner_operator_id == owner_operator_id,
            GenerationItem.distribution_status.in_(
                ["distributed", "pending_publish", "published"]
            ),
            GenerationItem.generated_text.isnot(None),  # 确保有生成内容
        ]
        if exclude_item_id is not None:
            conditions.append(GenerationItem.id != exclude_item_id)

        subquery = (
            select(GenerationItem.id)
            .where(and_(*conditions))
            .limit(limit * 2)  # 多取一些以防 embedding 记录不存在
        )

        result = await db.execute(subquery)
        item_ids = [row[0] for row in result.fetchall()]

        if not item_ids:
            logger.info("[Dedup] 创作者无历史生成项 | sub_user_id=%s", sub_user_id)
            return []

        # 查询对应的 embedding 记录
        query = (
            select(ContentEmbedding)
            .where(
                and_(
                    ContentEmbedding.generation_item_id.in_(item_ids),
                    ContentEmbedding.content_type == content_type.value,
                    ContentEmbedding.embedding.isnot(None),
                )
            )
            .order_by(ContentEmbedding.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        records = list(result.scalars().all())

        logger.info(
            "[Dedup] 创作者历史 embedding 记录 | sub_user_id=%s | count=%s",
            sub_user_id,
            len(records),
        )
        return records

    @classmethod
    async def check_image_duplication(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        image_urls: List[str],
        image_prompt: Optional[str] = None,
        threshold: float = DEFAULT_THRESHOLD,
        max_references: int = DEFAULT_MAX_REFERENCES,
    ) -> Dict[str, DedupResult]:
        """
        检测图片是否与历史内容重复

        注意：由于图片 embedding 需要视觉模型，这里使用图片提示词作为替代方案
        未来可扩展为真正的图片 embedding

        Args:
            db: 数据库会话
            item: 当前生成项
            image_urls: 待检测的图片 URL 列表
            image_prompt: 图片提示词（用于计算 embedding）
            threshold: 相似度阈值，默认 0.8
            max_references: 最大参考数量，默认 100

        Returns:
            Dict[str, DedupResult]: 每个图片 URL 对应的去重结果
        """
        from datetime import datetime

        results = {}

        # 如果没有图片提示词，使用用户提示词（生图模型不使用系统提示词）
        if not image_prompt:
            image_prompt = item.output_user_image_prompt or ""

        if not image_prompt and not image_urls:
            logger.warning("[Dedup] 无图片提示词或 URL，跳过图片去重")
            return results

        logger.info(
            "[Dedup] 开始图片去重检测 | owner=%s | image_count=%s",
            item.owner_operator_id,
            len(image_urls),
        )

        # 1. 计算图片提示词的哈希
        content_hash = cls._compute_content_hash(image_prompt)

        # 2. 获取已有 embedding 或计算新的（延迟保存）
        existing_record, new_embedding = await cls._get_or_create_embedding(
            db, item, ContentType.IMAGE, image_prompt, content_hash, content_index=0
        )

        # 优先使用已有记录
        if existing_record and existing_record.embedding:
            current_embedding = existing_record.embedding
            exclude_embedding_id = existing_record.id
        elif new_embedding:
            current_embedding = new_embedding
            exclude_embedding_id = None
        else:
            logger.warning("[Dedup] 无法获取图片嵌入向量，跳过检测")
            for url in image_urls:
                results[url] = DedupResult(
                    passed=True,
                    max_similarity=0.0,
                    references=[],
                    checked_at=datetime.utcnow().isoformat(),
                    content_type=ContentType.IMAGE,
                    error="Failed to get image embedding",
                )
            return results

        # 3. 获取历史图片 embedding 记录
        historical_records = await cls._get_historical_embeddings(
            db,
            item.owner_operator_id,
            ContentType.IMAGE,
            max_references,
            exclude_embedding_id=exclude_embedding_id,
        )

        if not historical_records:
            logger.info("[Dedup] 无历史图片参考内容，通过检测")
            for url in image_urls:
                results[url] = DedupResult(
                    passed=True,
                    max_similarity=0.0,
                    references=[],
                    checked_at=datetime.utcnow().isoformat(),
                    content_type=ContentType.IMAGE,
                )
            return results

        # 4. 计算相似度（所有图片共享同一个提示词 embedding）
        references = []
        max_similarity = 0.0
        used_record_ids = []

        for hist_record in historical_records:
            hist_embedding = hist_record.embedding
            if not hist_embedding:
                continue

            similarity = cls._cosine_similarity(current_embedding, hist_embedding)
            if similarity >= threshold:
                references.append(
                    {
                        "embedding_id": hist_record.id,
                        "item_id": hist_record.generation_item_id,
                        "task_id": hist_record.task_id,
                        "similarity": round(similarity, 4),
                        "content_type": "image",
                        "content_preview": hist_record.content_preview or "",
                        "created_at": (
                            hist_record.created_at.isoformat()
                            if hist_record.created_at
                            else None
                        ),
                    }
                )
                max_similarity = max(max_similarity, similarity)
                used_record_ids.append(hist_record.id)

            logger.debug(
                "[Dedup] 图片相似度计算 | embedding_id=%s | similarity=%.4f",
                hist_record.id,
                similarity,
            )

        # 5. 更新历史记录的使用统计
        if used_record_ids:
            await cls._update_usage_stats(db, used_record_ids)

        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[:5]
        passed = max_similarity < threshold

        # 6. 为每个图片 URL 返回相同的结果（因为共享同一个提示词）
        checked_at = datetime.utcnow().isoformat()
        for url in image_urls:
            results[url] = DedupResult(
                passed=passed,
                max_similarity=round(max_similarity, 4),
                references=references,
                checked_at=checked_at,
                content_type=ContentType.IMAGE,
                embedding=new_embedding,  # 返回 embedding 供延迟保存（所有图片共享同一个）
            )

        logger.info(
            "[Dedup] 图片检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s",
            passed,
            max_similarity,
            len(references),
        )

        return results

    @classmethod
    async def _get_or_create_embedding(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        content_type: ContentType,
        content: str,
        content_hash: str,
        content_index: int = 0,
        use_existing_embedding: Optional[List[float]] = None,
    ) -> Tuple[Optional[ContentEmbedding], Optional[List[float]]]:
        """
        获取已有的 embedding 记录，或计算新的 embedding（延迟保存）

        去重检测时只查找已有记录或计算新 embedding，不写入数据库。
        返回 embedding 向量供调用方在主事务提交后批量保存。

        Args:
            db: 数据库会话
            item: 生成项
            content_type: 内容类型
            content: 内容（文案或图片提示词）
            content_hash: 内容哈希
            content_index: 内容索引（多张图片时使用）
            use_existing_embedding: 使用已有的 embedding 向量（不重新计算）

        Returns:
            Tuple[Optional[ContentEmbedding], Optional[List[float]]]:
                - 已存在的记录（或 None）
                - 新计算的 embedding 向量（需要延迟保存，或 None）
        """
        # 1. 先尝试通过内容哈希查找（快速路径）
        query = (
            select(ContentEmbedding)
            .where(
                and_(
                    ContentEmbedding.owner_operator_id == item.owner_operator_id,
                    ContentEmbedding.content_type == content_type.value,
                    ContentEmbedding.content_hash == content_hash,
                )
            )
            .order_by(ContentEmbedding.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            logger.debug("[Dedup] 通过哈希找到已存在的 embedding | id=%s", existing.id)
            return existing, None  # 已存在，无需保存

        # 2. 计算新的 embedding（或使用提供的）
        if use_existing_embedding is not None:
            embedding = use_existing_embedding
        else:
            embedding = await cls._get_embedding(db, content)

        if not embedding:
            logger.warning("[Dedup] 无法计算 embedding")
            return None, None

        logger.debug(
            "[Dedup] 计算新 embedding | type=%s | hash=%s",
            content_type.value,
            content_hash[:16],
        )
        # 返回 None 表示记录不存在，同时返回 embedding 供延迟保存
        return None, embedding

    @classmethod
    async def batch_save_embeddings(
        cls,
        db: AsyncSession,
        embeddings_data: List[Dict[str, Any]],
    ) -> int:
        """
        批量保存 embedding 记录（使用独立session避免锁冲突）

        使用独立的数据库session进行embedding保存，避免与主事务产生锁冲突。

        Args:
            db: 数据库会话（用于获取engine，不直接使用）
            embeddings_data: embedding 数据列表，每项包含：
                - item: GenerationItem
                - content_type: ContentType
                - content: str
                - content_hash: str
                - embedding: List[float]
                - content_index: int (可选，默认 0)

        Returns:
            成功保存的数量
        """
        from datetime import datetime, timezone

        from app.core.database import async_session_maker

        if not embeddings_data:
            return 0

        # 使用独立的session进行批量保存，避免锁冲突
        saved_count = 0
        batch_size = 10  # 每批保存10条，减少锁持有时间

        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i : i + batch_size]

            # 创建独立的session
            async with async_session_maker() as independent_session:
                try:
                    for data in batch:
                        try:
                            item = data["item"]
                            content_type = data["content_type"]
                            content = data["content"]
                            content_hash = data["content_hash"]
                            embedding = data["embedding"]
                            content_index = data.get("content_index", 0)

                            content_preview = (
                                content[:500] if len(content) > 500 else content
                            )

                            record = ContentEmbedding(
                                owner_operator_id=item.owner_operator_id,
                                generation_item_id=item.id,
                                task_id=item.task_id,
                                content_type=content_type.value,
                                content_index=content_index,
                                embedding=embedding,
                                content_preview=content_preview,
                                content_hash=content_hash,
                                used_for_dedup_count=0,
                                created_at=datetime.now(timezone.utc),
                            )

                            independent_session.add(record)
                            saved_count += 1

                        except Exception as e:
                            logger.error(
                                "[Dedup] 批量保存 embedding 单项失败 | error=%s",
                                str(e)[:100],
                            )

                    await independent_session.commit()
                    logger.debug(
                        "[Dedup] 批量保存 embedding 批次完成 | batch=%s-%s | count=%s",
                        i,
                        i + len(batch),
                        len(batch),
                    )

                except Exception as e:
                    logger.error(
                        "[Dedup] 批量保存 embedding 提交失败 | batch=%s | error=%s",
                        i,
                        str(e)[:200],
                    )
                    await independent_session.rollback()
                    # 失败后继续下一批

        logger.info("[Dedup] 批量保存 embedding 完成 | total_count=%s", saved_count)
        return saved_count

    @classmethod
    async def _save_content_embedding(
        cls,
        db: AsyncSession,
        item: GenerationItem,
        content_type: ContentType,
        content: str,
        content_hash: str,
        embedding: List[float],
        content_index: int = 0,
    ) -> Optional[ContentEmbedding]:
        """
        保存单个 embedding 记录（使用独立session避免锁冲突）

        使用独立的数据库session进行embedding保存，避免与主事务产生锁冲突。

        Args:
            db: 数据库会话（用于获取engine，不直接使用）
            item: 生成项
            content_type: 内容类型
            content: 内容文本
            content_hash: 内容哈希
            embedding: embedding 向量
            content_index: 内容索引

        Returns:
            创建的 ContentEmbedding 记录
        """
        from datetime import datetime, timezone

        from app.core.database import async_session_maker

        content_preview = content[:500] if len(content) > 500 else content

        # 使用独立的session进行保存，避免锁冲突
        async with async_session_maker() as independent_session:
            try:
                record = ContentEmbedding(
                    owner_operator_id=item.owner_operator_id,
                    generation_item_id=item.id,
                    task_id=item.task_id,
                    content_type=content_type.value,
                    content_index=content_index,
                    embedding=embedding,
                    content_preview=content_preview,
                    content_hash=content_hash,
                    used_for_dedup_count=0,
                    created_at=datetime.now(timezone.utc),
                )

                independent_session.add(record)
                await independent_session.commit()
                await independent_session.refresh(record)

                logger.info(
                    "[Dedup] 保存 embedding 记录成功 | id=%s | item_id=%s | type=%s",
                    record.id,
                    item.id,
                    content_type.value,
                )

                return record

            except Exception as e:
                logger.error("[Dedup] 保存 embedding 失败 | error=%s", str(e)[:200])
                await independent_session.rollback()
                return None

    @classmethod
    async def _get_historical_embeddings(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        content_type: ContentType,
        limit: int = 100,
        exclude_embedding_id: Optional[int] = None,
    ) -> List[ContentEmbedding]:
        """
        获取历史 embedding 记录

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            content_type: 内容类型
            limit: 最大数量
            exclude_embedding_id: 排除的 embedding ID

        Returns:
            ContentEmbedding 记录列表
        """
        query = (
            select(ContentEmbedding)
            .where(
                and_(
                    ContentEmbedding.owner_operator_id == owner_operator_id,
                    ContentEmbedding.content_type == content_type.value,
                )
            )
            .order_by(ContentEmbedding.created_at.desc())
            .limit(limit)
        )

        if exclude_embedding_id:
            query = query.where(ContentEmbedding.id != exclude_embedding_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def _update_usage_stats(
        cls,
        db: AsyncSession,
        embedding_ids: List[int],
    ) -> None:
        """
        更新 embedding 记录的使用统计（使用独立session避免锁冲突）

        Args:
            db: 数据库会话（用于获取engine，不直接使用）
            embedding_ids: embedding ID 列表
        """
        from datetime import datetime, timezone

        from app.core.database import async_session_maker

        if not embedding_ids:
            return

        # 使用独立的session进行更新，避免锁冲突
        async with async_session_maker() as independent_session:
            try:
                stmt = (
                    update(ContentEmbedding)
                    .where(ContentEmbedding.id.in_(embedding_ids))
                    .values(
                        used_for_dedup_count=ContentEmbedding.used_for_dedup_count + 1,
                        last_used_at=datetime.now(timezone.utc),
                    )
                )
                await independent_session.execute(stmt)
                await independent_session.commit()
                logger.debug("[Dedup] 更新使用统计 | count=%s", len(embedding_ids))
            except Exception as e:
                logger.warning("[Dedup] 更新使用统计失败: %s", e)
                await independent_session.rollback()

    @classmethod
    def _compute_content_hash(cls, content: str) -> str:
        """
        计算内容的 SHA256 哈希

        Args:
            content: 内容字符串

        Returns:
            哈希字符串
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    async def _get_embedding(cls, db: AsyncSession, text: str) -> Optional[List[float]]:
        """
        获取文本的嵌入向量

        使用多模态 embedding 模型进行向量计算（统一使用多模态接口）。

        Args:
            db: 数据库会话
            text: 待嵌入的文本

        Returns:
            嵌入向量列表，失败时返回 None
        """
        try:
            model_config_manager = get_model_config_manager()
            await model_config_manager.load_all_configs(db)

            # 使用专门的 embedding 模型
            result = await model_config_manager.get_default_config_with_platform(
                db, model_type="embedding"
            )
            if not result:
                logger.warning("[Dedup] 无法获取 embedding 模型配置")
                return None

            config, platform = result
            adapter = ModelAdapterFactory.create_adapter(platform, config)

            # 从配置中获取模型 ID
            model_id = config.model_id
            logger.info(
                "[Dedup] 使用 embedding 模型 | platform=%s | model_id=%s",
                platform,
                model_id,
            )

            # 统一使用多模态接口（支持纯文本输入）
            if hasattr(adapter, "get_multimodal_embedding"):
                return await adapter.get_multimodal_embedding(
                    text=text, model_id=model_id
                )
            elif hasattr(adapter, "get_embedding"):
                # 回退到普通 embedding 方法
                return await adapter.get_embedding(text, model_id=model_id)
            elif hasattr(adapter, "embedding"):
                return await adapter.embedding(text, model_id=model_id)
            else:
                logger.warning("[Dedup] 适配器不支持 embedding | platform=%s", platform)
                return None

        except Exception as e:
            logger.error(f"[Dedup] 获取嵌入向量失败: {e}")
            return None

    @classmethod
    async def _get_image_embedding(
        cls, db: AsyncSession, image_url: str
    ) -> Optional[List[float]]:
        """
        获取图片的嵌入向量（多模态 embedding）

        使用多模态 embedding 模型获取图片的向量表示。

        Args:
            db: 数据库会话
            image_url: 图片 URL（支持公网 URL 或 Base64 data URI）

        Returns:
            嵌入向量列表，失败时返回 None
        """
        try:
            from app.services.storage_service import get_storage_service

            model_config_manager = get_model_config_manager()
            await model_config_manager.load_all_configs(db)

            # 转换图片 URL 为公网可访问的 URL（重要：百炼 API 需要公网 URL）
            storage_service = get_storage_service()

            # 处理图片 URL，优先使用 Base64 避免网络访问问题
            # 百炼 qwen3-vl-embedding 限制图片 ≤ 5MB（5070KB），需要压缩
            processed_url, processed_base64 = (
                await storage_service.process_reference_image(
                    image_url,
                    prefer_url=False,  # 优先使用 Base64
                    no_compression=False,  # 允许压缩以适配 embedding API 大小限制
                    max_size_bytes=4
                    * 1024
                    * 1024,  # 限制 4MB，留余量给 embedding API 的 5MB 限制
                )
            )

            # 使用处理后的图片（优先 Base64）
            final_image = processed_base64 if processed_base64 else processed_url
            if not final_image:
                final_image = image_url  # 回退到原始 URL

            logger.info(
                f"[Dedup] 图片URL处理完成 | original={image_url[:80]}... | final_type={'Base64' if final_image.startswith('data:') else 'URL'}"
            )

            # 使用专门的 embedding 模型（百炼支持多模态）
            result = await model_config_manager.get_default_config_with_platform(
                db, model_type="embedding"
            )
            if not result:
                logger.warning("[Dedup] 无法获取 embedding 模型配置")
                return None

            config, platform = result
            adapter = ModelAdapterFactory.create_adapter(platform, config)

            # 从配置中获取模型 ID
            model_id = config.model_id
            logger.info(
                "[Dedup] 使用 embedding 模型 | platform=%s | model_id=%s",
                platform,
                model_id,
            )

            # 检查适配器是否支持多模态 embedding
            if hasattr(adapter, "get_image_embedding"):
                return await adapter.get_image_embedding(final_image, model_id=model_id)
            elif hasattr(adapter, "get_multimodal_embedding"):
                return await adapter.get_multimodal_embedding(
                    image_url=final_image, model_id=model_id
                )
            else:
                logger.warning(
                    "[Dedup] 适配器不支持图片 embedding | platform=%s", platform
                )
                return None

        except Exception as e:
            logger.error(f"[Dedup] 获取图片嵌入向量失败: {e}", exc_info=True)
            return None

    @classmethod
    async def check_image_visual_similarity(
        cls,
        db: AsyncSession,
        generated_image_url: str,
        benchmark_image_urls: Optional[List[str]] = None,
        threshold: float = 0.85,
    ) -> DedupResult:
        """
        检测生成图片与对标图片的视觉相似度

        使用多模态向量计算图片间的相似度，判断生成图片是否过于接近对标图片。
        当相似度超过阈值时，建议调整提示词重新生成。

        Args:
            db: 数据库会话
            generated_image_url: 生成的图片 URL
            benchmark_image_urls: 对标图片 URL 列表（可选）
            threshold: 相似度阈值，默认 0.85（图片相似度阈值通常高于文本）

        Returns:
            DedupResult: 相似度检测结果
        """
        from datetime import datetime

        checked_at = datetime.utcnow()

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_image_visual_similarity 开始 | img_url=%s | benchmark_count=%s | threshold=%s",
            generated_image_url[:60] if generated_image_url else None,
            len(benchmark_image_urls) if benchmark_image_urls else 0,
            threshold,
        )

        # 1. 获取生成图片的 embedding
        generated_embedding = await cls._get_image_embedding(db, generated_image_url)
        if not generated_embedding:
            logger.warning("[Dedup] 无法获取生成图片嵌入向量，跳过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.IMAGE,
                error="Failed to get generated image embedding",
            )

        references = []
        max_similarity = 0.0

        # 2. 与对标图片比对
        if benchmark_image_urls:
            for idx, bench_url in enumerate(benchmark_image_urls):
                logger.info(
                    "[Dedup] 对标图片检测 | bench_idx=%s | url=%s",
                    idx + 1,
                    bench_url[:60] if bench_url else None,
                )

                bench_embedding = await cls._get_image_embedding(db, bench_url)
                if bench_embedding:
                    similarity = cls._cosine_similarity(
                        generated_embedding, bench_embedding
                    )
                    logger.info(
                        "[Dedup] 与对标图片相似度 | idx=%s | sim=%.4f",
                        idx + 1,
                        similarity,
                    )

                    if similarity >= threshold:
                        references.append(
                            {
                                "embedding_id": None,
                                "item_id": None,
                                "task_id": None,
                                "similarity": round(similarity, 4),
                                "content_type": "benchmark_image",
                                "content_preview": bench_url[:200] if bench_url else "",
                                "created_at": checked_at.isoformat(),
                                "source": f"对标图片{idx + 1}",
                            }
                        )
                        max_similarity = max(max_similarity, similarity)
                        logger.warning(
                            "[Dedup] 生成图片与对标图片相似度过高 | idx=%s | sim=%.4f",
                            idx + 1,
                            similarity,
                        )
                else:
                    logger.warning("[Dedup] 无法获取对标图片嵌入向量 | idx=%s", idx + 1)

        # 3. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[:5]

        passed = max_similarity < threshold

        result = DedupResult(
            passed=passed,
            max_similarity=round(max_similarity, 4),
            references=references,
            checked_at=checked_at.isoformat(),
            content_type=ContentType.IMAGE,
            embedding=generated_embedding,  # 返回 embedding 用于缓存
        )

        logger.info(
            "[Dedup] 图片视觉相似度检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s",
            passed,
            max_similarity,
            len(references),
        )

        return result

    @classmethod
    async def check_image_duplication_with_scope(
        cls,
        db: AsyncSession,
        generated_image_url: str,
        item: GenerationItem,
        scope: List[str],
        task_id: int,
        task_image_embeddings_cache: Optional[Dict[int, Dict[int, List[float]]]] = None,
        benchmark_images: Optional[List[str]] = None,
        benchmark_image_enabled: bool = False,
        threshold: float = 0.8,
        max_references_per_scope: int = 50,
    ) -> DedupResult:
        """
        按指定范围检测图片是否重复

        Args:
            db: 数据库会话
            generated_image_url: 生成的图片 URL
            item: 当前生成项
            scope: 去重范围配置 ["subuser_image_history", "current_task_images", "all_image_history"]
            task_id: 当前任务ID
            task_image_embeddings_cache: 当前任务已生成图片的 embedding 缓存 {item_id: {image_index: embedding}}
            benchmark_images: 对标图片 URL 列表
            benchmark_image_enabled: 对标图片参考开关
            threshold: 相似度阈值（高于此值认为相似）
            max_references_per_scope: 每个范围的最大参考数量

        Returns:
            DedupResult: 图片去重检测结果，包含 embedding 用于缓存
        """
        from datetime import datetime

        checked_at = datetime.utcnow()
        sub_user_id = item.sub_user_id
        owner_operator_id = item.owner_operator_id

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_image_duplication_with_scope 开始 | item_id=%s | sub_user=%s | scope=%s | threshold=%s",
            item.id,
            sub_user_id,
            scope,
            threshold,
        )
        logger.info(
            "[Dedup] 生成图片URL: %s",
            generated_image_url[:80] if generated_image_url else None,
        )

        # 1. 获取生成图片的 embedding（只计算一次）
        generated_embedding = await cls._get_image_embedding(db, generated_image_url)
        if not generated_embedding:
            logger.warning("[Dedup] 无法获取生成图片嵌入向量，跳过检测")
            return DedupResult(
                passed=True,
                max_similarity=0.0,
                references=[],
                checked_at=checked_at.isoformat(),
                content_type=ContentType.IMAGE,
                error="Failed to get generated image embedding",
            )

        references = []
        max_similarity = 0.0

        # 2. 对标图片检测（如果启用）
        if benchmark_image_enabled and benchmark_images:
            logger.info(
                "[Dedup] 对标图片检测 | benchmark_count=%s", len(benchmark_images)
            )
            for idx, bench_url in enumerate(benchmark_images):
                bench_embedding = await cls._get_image_embedding(db, bench_url)
                if bench_embedding:
                    similarity = cls._cosine_similarity(
                        generated_embedding, bench_embedding
                    )
                    logger.info(
                        "[Dedup] 与对标图片相似度 | idx=%s | sim=%.4f",
                        idx + 1,
                        similarity,
                    )

                    if similarity >= threshold:
                        references.append(
                            {
                                "embedding_id": None,
                                "item_id": None,
                                "task_id": None,
                                "similarity": round(similarity, 4),
                                "content_type": "benchmark_image",
                                "content_preview": bench_url[:200] if bench_url else "",
                                "created_at": checked_at.isoformat(),
                                "source": f"对标图片{idx + 1}",
                            }
                        )
                        max_similarity = max(max_similarity, similarity)
                        logger.warning(
                            "[Dedup] 生成图片与对标图片相似度过高 | idx=%s | sim=%.4f",
                            idx + 1,
                            similarity,
                        )

        # 3. 按 scope 配置检测
        for scope_item in scope:
            if scope_item == "subuser_image_history":
                # 当前创作者历史图片
                logger.debug(
                    "[Dedup] 图片检测范围: subuser_image_history | sub_user_id=%s",
                    sub_user_id,
                )
                hist_records = await cls._get_subuser_historical_embeddings(
                    db,
                    sub_user_id,
                    owner_operator_id,
                    ContentType.IMAGE,
                    max_references_per_scope,
                    exclude_item_id=item.id,
                )
                for rec in hist_records:
                    if rec.embedding:
                        sim = cls._cosine_similarity(generated_embedding, rec.embedding)
                        if sim >= threshold:
                            references.append(
                                {
                                    "embedding_id": rec.id,
                                    "item_id": rec.generation_item_id,
                                    "task_id": rec.task_id,
                                    "similarity": round(sim, 4),
                                    "content_type": "image",
                                    "content_preview": rec.content_preview or "",
                                    "created_at": (
                                        rec.created_at.isoformat()
                                        if rec.created_at
                                        else None
                                    ),
                                    "source": "当前创作者历史图片",
                                }
                            )
                            max_similarity = max(max_similarity, sim)
                        logger.debug(
                            "[Dedup] subuser_image_history 相似度 | embedding_id=%s | sim=%.4f",
                            rec.id,
                            sim,
                        )

            elif scope_item == "current_task_images":
                # 当前任务所有子任务的图片
                logger.debug(
                    "[Dedup] 图片检测范围: current_task_images | task_id=%s | cache_count=%s",
                    task_id,
                    len(task_image_embeddings_cache or {}),
                )
                if task_image_embeddings_cache:
                    for (
                        other_item_id,
                        image_embeddings,
                    ) in task_image_embeddings_cache.items():
                        if other_item_id != item.id:  # 排除当前 item
                            for img_idx, other_emb in image_embeddings.items():
                                sim = cls._cosine_similarity(
                                    generated_embedding, other_emb
                                )
                                if sim >= threshold:
                                    references.append(
                                        {
                                            "embedding_id": None,
                                            "item_id": other_item_id,
                                            "task_id": task_id,
                                            "similarity": round(sim, 4),
                                            "content_type": "image",
                                            "content_preview": f"任务内其他子任务图片{img_idx}",
                                            "created_at": checked_at.isoformat(),
                                            "source": f"当前任务子任务{other_item_id}图片{img_idx}",
                                        }
                                    )
                                    max_similarity = max(max_similarity, sim)
                                logger.debug(
                                    "[Dedup] current_task_images 相似度 | item_id=%s | img_idx=%s | sim=%.4f",
                                    other_item_id,
                                    img_idx,
                                    sim,
                                )

            elif scope_item == "all_image_history":
                # 所有历史图片
                logger.debug(
                    "[Dedup] 图片检测范围: all_image_history | owner=%s",
                    owner_operator_id,
                )
                hist_records = await cls._get_historical_embeddings(
                    db,
                    owner_operator_id,
                    ContentType.IMAGE,
                    max_references_per_scope,
                    exclude_embedding_id=None,
                )
                for rec in hist_records:
                    if rec.embedding and rec.generation_item_id != item.id:
                        sim = cls._cosine_similarity(generated_embedding, rec.embedding)
                        if sim >= threshold:
                            references.append(
                                {
                                    "embedding_id": rec.id,
                                    "item_id": rec.generation_item_id,
                                    "task_id": rec.task_id,
                                    "similarity": round(sim, 4),
                                    "content_type": "image",
                                    "content_preview": rec.content_preview or "",
                                    "created_at": (
                                        rec.created_at.isoformat()
                                        if rec.created_at
                                        else None
                                    ),
                                    "source": "所有历史图片",
                                }
                            )
                            max_similarity = max(max_similarity, sim)
                        logger.debug(
                            "[Dedup] all_image_history 相似度 | embedding_id=%s | sim=%.4f",
                            rec.id,
                            sim,
                        )

        # 4. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[
            :10
        ]

        passed = max_similarity < threshold

        result = DedupResult(
            passed=passed,
            max_similarity=round(max_similarity, 4),
            references=references,
            checked_at=checked_at.isoformat(),
            content_type=ContentType.IMAGE,
            embedding=generated_embedding,  # 返回 embedding 用于缓存
        )

        logger.info(
            "[Dedup] 图片去重检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s | scope=%s",
            passed,
            max_similarity,
            len(references),
            scope,
        )

        return result

    @classmethod
    def _cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            余弦相似度（0-1之间）
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    @classmethod
    async def check_duplication(
        cls,
        db: AsyncSession,
        owner_operator_id: int,
        text: str,
        threshold: float = DEFAULT_THRESHOLD,
        exclude_item_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        兼容旧接口的去重检测方法

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID
            text: 待检测的文案内容
            threshold: 相似度阈值
            exclude_item_ids: 排除的子任务ID列表

        Returns:
            Dict: 包含 passed, similarity, references 的字典
        """
        from datetime import datetime

        logger.info("[Dedup] ===========================================")
        logger.info(
            "[Dedup] check_duplication 开始 | owner=%s | text_len=%s | threshold=%s | exclude_count=%s",
            owner_operator_id,
            len(text),
            threshold,
            len(exclude_item_ids) if exclude_item_ids else 0,
        )

        # 文案内容日志（前200字符）
        text_preview = text[:200] if text else ""
        logger.info(
            "[Dedup] 待检测文案内容: %s%s",
            text_preview,
            "..." if len(text) > 200 else "",
        )

        datetime.utcnow()

        # 1. 计算内容哈希
        content_hash = cls._compute_content_hash(text)
        logger.info("[Dedup] 内容哈希: %s", content_hash)

        # 2. 获取已有 embedding 或计算新的（延迟保存）
        # 创建一个临时的 GenerationItem 用于 embedding 存储
        from app.models import GenerationItem

        temp_item = GenerationItem(
            id=0,  # 临时 ID
            owner_operator_id=owner_operator_id,
            task_id=None,
            sub_user_id=None,
        )
        existing_record, new_embedding = await cls._get_or_create_embedding(
            db, temp_item, ContentType.TEXT, text, content_hash, content_index=0
        )

        # 优先使用已有记录
        if existing_record and existing_record.embedding:
            current_embedding = existing_record.embedding
            exclude_embedding_id = existing_record.id
        elif new_embedding:
            current_embedding = new_embedding
            exclude_embedding_id = None
        else:
            logger.warning("[Dedup] 无法获取文案嵌入向量，跳过检测")
            logger.info("[Dedup] ===========================================\n")
            return {
                "passed": True,
                "similarity": 0.0,
                "references": [],
            }

        # 3. 获取历史 embedding 记录
        historical_records = await cls._get_historical_embeddings(
            db,
            owner_operator_id,
            ContentType.TEXT,
            cls.DEFAULT_MAX_REFERENCES,
            exclude_embedding_id=exclude_embedding_id,
        )

        if not historical_records:
            logger.info("[Dedup] 无历史文案参考内容，通过检测")
            logger.info("[Dedup] ===========================================\n")
            return {
                "passed": True,
                "similarity": 0.0,
                "references": [],
            }

        # 4. 计算与历史内容的相似度
        references = []
        max_similarity = 0.0
        used_record_ids = []

        for hist_record in historical_records:
            hist_embedding = hist_record.embedding
            if not hist_embedding:
                continue

            similarity = cls._cosine_similarity(current_embedding, hist_embedding)
            if similarity >= threshold:
                references.append(
                    {
                        "embedding_id": hist_record.id,
                        "item_id": hist_record.generation_item_id,
                        "task_id": hist_record.task_id,
                        "similarity": round(similarity, 4),
                        "content_type": "text",
                        "content_preview": hist_record.content_preview or "",
                        "created_at": (
                            hist_record.created_at.isoformat()
                            if hist_record.created_at
                            else None
                        ),
                    }
                )
                max_similarity = max(max_similarity, similarity)
                used_record_ids.append(hist_record.id)

            logger.debug(
                "[Dedup] 文案相似度计算 | embedding_id=%s | similarity=%.4f",
                hist_record.id,
                similarity,
            )

        # 5. 更新历史记录的使用统计
        if used_record_ids:
            await cls._update_usage_stats(db, used_record_ids)

        # 6. 排序并限制数量
        references = sorted(references, key=lambda x: x["similarity"], reverse=True)[:5]

        passed = max_similarity < threshold

        logger.info(
            "[Dedup] 文案检测完成 | passed=%s | max_similarity=%.4f | ref_count=%s",
            passed,
            max_similarity,
            len(references),
        )
        logger.info("[Dedup] ===========================================\n")

        return {
            "passed": passed,
            "similarity": round(max_similarity, 4),
            "references": references,
        }
