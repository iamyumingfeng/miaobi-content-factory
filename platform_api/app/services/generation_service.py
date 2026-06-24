"""
内容生成服务 (generation_service.py)

提供内容生成相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, and_, func, or_, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import (GenerationItemNotFoundError,
                                 GenerationTaskNotFoundError)
from app.models import (GenerationItem, GenerationItemExecutionLog,
                        GenerationTask, GenerationTaskProgressLog,
                        GenerationTaskSubuser, GenerationTaskTemplate,
                        Material, SubUser,
                        Template)
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


def _is_valid_cos_url(url: str) -> bool:
    """
    检查 COS URL 是否有效（包含有效的 bucket 名称）

    Args:
        url: 待检查的 URL

    Returns:
        bool: URL 是否有效
    """
    if not url:
        return False
    # 已经是本地路径格式，视为有效
    if url.startswith("/cos/"):
        return True
    # 检查是否是无效的 COS URL 格式（缺少 bucket）
    # 格式：https://.cos.{region}.myqcloud.com/...（bucket 为空）
    if url.startswith("https://.") or url.startswith("http://."):
        return False
    return True


# 缓存 StorageService 实例
_storage_service = None


def _get_storage_service():
    """获取缓存的 StorageService 实例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def _process_url(url: str, prefer_url: bool) -> str:
    """
    根据 URL 有效性和配置决定如何处理 URL

    Args:
        url: 原始 URL
        prefer_url: 是否优先使用公网 URL（此参数已废弃，使用 StorageService 的统一逻辑）

    Returns:
        处理后的 URL
    """
    if not url:
        return url
    # 使用 StorageService 的统一转换逻辑
    return _get_storage_service().convert_url(url)


def _process_urls(urls: Optional[List[str]], prefer_url: bool) -> Optional[List[str]]:
    """
    批量处理 URL 列表

    Args:
        urls: URL 列表
        prefer_url: 是否优先使用公网 URL（此参数已废弃）

    Returns:
        处理后的 URL 列表
    """
    if not urls:
        return urls
    storage_service = _get_storage_service()
    return [storage_service.convert_url(url) for url in urls]


def _convert_url_to_local(url: str) -> str:
    """
    将公网 COS URL 转换为本地路径

    Args:
        url: 原始 URL（可能是公网 URL 或本地路径）

    Returns:
        本地路径（如 /cos/...）
    """
    if not url:
        return url
    # 已经是本地路径格式
    if url.startswith("/cos/"):
        return url
    # 匹配公网 URL 格式：https://{bucket}.cos.{region}.myqcloud.com/{path}
    # 或者无效格式：https://.cos.{region}.myqcloud.com/{path}
    pattern = r"^https?://[^/]*\.cos\.[^/]+\.myqcloud\.com/(.+)$"
    match = re.match(pattern, url)
    if match:
        return f"/cos/{match.group(1)}"
    return url


def _convert_urls_to_local(urls: Optional[List[str]]) -> Optional[List[str]]:
    """
    批量转换 URL 列表为本地路径

    Args:
        urls: URL 列表

    Returns:
        转换后的本地路径列表
    """
    if not urls:
        return urls
    return [_convert_url_to_local(url) for url in urls]


def _convert_generation_item_urls(item: GenerationItem) -> GenerationItem:
    """
    转换 GenerationItem 中的所有 URL 字段

    Args:
        item: GenerationItem 对象

    Returns:
        转换后的 GenerationItem 对象
    """
    storage_service = StorageService()

    # 转换文本文件 URL
    if item.text_file_url:
        item.text_file_url = storage_service.convert_url(item.text_file_url)

    # 转换生成的图片 URL 列表
    if item.generated_image_urls_json:
        item.generated_image_urls_json = [
            storage_service.convert_url(url) for url in item.generated_image_urls_json
        ]

    # 转换生成的图片缩略图 URL 列表
    if item.generated_image_thumbnails_json:
        item.generated_image_thumbnails_json = [
            storage_service.convert_url(url)
            for url in item.generated_image_thumbnails_json
        ]

    # 转换生成的视频 URL
    if item.generated_video_url:
        item.generated_video_url = storage_service.convert_url(item.generated_video_url)

    # 转换对标素材的图片 URL 列表
    if item.input_benchmark_images_json:
        item.input_benchmark_images_json = [
            storage_service.convert_url(url) for url in item.input_benchmark_images_json
        ]

    return item


class GenerationService:
    """
    内容生成服务类
    """

    # ============================================
    # 生成任务管理
    # ============================================
    @staticmethod
    async def create_generation_task(
        db: AsyncSession,
        owner_operator_id: int,
        created_by: int,
        name: Optional[str] = None,
        material_id: Optional[int] = None,
        benchmark_material_id: Optional[int] = None,
        model_platform: Optional[str] = None,
        model_id: Optional[str] = None,
        image_model_platform: Optional[str] = None,
        image_model_id: Optional[str] = None,
        model_selection_mode: str = "auto",
        max_concurrency: int = 5,
        variable_values_json: Optional[Dict[str, Any]] = None,
        dedup_rules_json: Optional[Dict[str, Any]] = None,
        template_ids: Optional[List[int]] = None,
        sub_user_ids: Optional[List[int]] = None,
        image_count: Optional[int] = None,
        dedup_enabled: Optional[bool] = None,
        dedup_threshold: Optional[float] = None,
        dedup_retry_count: Optional[int] = None,
        dedup_scope: Optional[List[str]] = None,
        image_dedup_enabled: Optional[bool] = None,
        image_dedup_threshold: Optional[float] = None,
        image_dedup_retry_count: Optional[int] = None,
        image_dedup_scope: Optional[List[str]] = None,
        benchmark_text_enabled: Optional[bool] = False,
        benchmark_image_enabled: Optional[bool] = False,
        benchmark_image_reference_options: Optional[List[str]] = None,
        # V3.0: 图片角色配置
        benchmark_image_roles: Optional[Dict[str, List[str]]] = None,
        template_product_mapping: Optional[Dict[str, str]] = None,
    ) -> GenerationTask:
        """
        创建生成任务
        """
        logger.debug(
            "[Service] create_generation_task | owner=%s | name=%s | material=%s | templates=%s | sub_users=%s",
            owner_operator_id,
            name,
            material_id,
            template_ids,
            sub_user_ids,
        )

        # 创建任务
        task = GenerationTask(
            name=name,
            material_id=material_id,
            benchmark_material_id=benchmark_material_id,
            model_platform=model_platform,
            model_id=model_id,
            image_model_platform=image_model_platform,
            image_model_id=image_model_id,
            model_selection_mode=model_selection_mode,
            max_concurrency=max_concurrency,
            variable_values_json=variable_values_json,
            dedup_rules_json=dedup_rules_json,
            status="pending",
            total_count=0,
            created_by=created_by,
            owner_operator_id=owner_operator_id,
            # 去重配置
            image_count=image_count,
            dedup_enabled=dedup_enabled,
            dedup_threshold=dedup_threshold,
            dedup_retry_count=dedup_retry_count,
            dedup_scope=dedup_scope,
            image_dedup_enabled=image_dedup_enabled,
            image_dedup_threshold=image_dedup_threshold,
            image_dedup_retry_count=image_dedup_retry_count,
            image_dedup_scope=image_dedup_scope,
            # 对标配置
            benchmark_text_enabled=benchmark_text_enabled,
            benchmark_image_enabled=benchmark_image_enabled,
            benchmark_image_reference_options=benchmark_image_reference_options,
            # V3.0: 图片角色配置
            benchmark_image_roles_json=benchmark_image_roles,
            template_product_mapping_json=template_product_mapping,
        )

        db.add(task)
        await db.flush()
        logger.debug("[Service] 任务记录已创建 | task_id=%s", task.id)

        # 添加模板关联
        total_items = 0
        if template_ids:
            for idx, template_id in enumerate(template_ids):
                task_template = GenerationTaskTemplate(
                    task_id=task.id,
                    template_id=template_id,
                    sort_order=idx,
                )
                db.add(task_template)
                logger.debug(
                    "[Service] 任务模板关联已创建 | task_id=%s | template_id=%s | order=%s",
                    task.id,
                    template_id,
                    idx,
                )

            # 添加创作者关联并创建子任务
            if sub_user_ids:
                logger.debug(
                    "[Service] 开始创建子任务 | task_id=%s | template_count=%s | subuser_count=%s",
                    task.id,
                    len(template_ids),
                    len(sub_user_ids),
                )

                # 预先加载所有模板和创作者信息（避免循环查询）
                templates_query = select(Template).where(Template.id.in_(template_ids))
                templates_result = await db.execute(templates_query)
                templates_map = {t.id: t for t in templates_result.scalars().all()}

                sub_users_query = select(SubUser).where(SubUser.id.in_(sub_user_ids))
                sub_users_result = await db.execute(sub_users_query)
                sub_users_map = {su.id: su for su in sub_users_result.scalars().all()}

                # 加载对标素材信息（如果有）
                benchmark_material = None
                if benchmark_material_id:
                    bm_query = (
                        select(Material)
                        .where(Material.id == benchmark_material_id)
                        .options(selectinload(Material.attachments))
                    )
                    bm_result = await db.execute(bm_query)
                    benchmark_material = bm_result.scalar_one_or_none()

                # 获取对标素材的附件URL列表
                benchmark_image_urls = []
                if benchmark_material and benchmark_material.attachments:
                    benchmark_image_urls = [
                        att.file_url
                        for att in benchmark_material.attachments
                        if att.file_type == "image"
                    ]

                for sub_user_id in sub_user_ids:
                    task_subuser = GenerationTaskSubuser(
                        task_id=task.id,
                        sub_user_id=sub_user_id,
                    )
                    db.add(task_subuser)

                    # 获取创作者快照信息
                    sub_user = sub_users_map.get(sub_user_id)
                    sub_user_name = (
                        sub_user.nickname or sub_user.display_name or str(sub_user_id)
                        if sub_user
                        else str(sub_user_id)
                    )
                    sub_user_profile = sub_user.fan_profile if sub_user else None
                    sub_user_positioning = (
                        sub_user.user_positioning if sub_user else None
                    )
                    sub_user_style = sub_user.content_style if sub_user else None

                    # 为每个 (创作者, 模板) 组合创建子任务
                    for template_id in template_ids:
                        template = templates_map.get(template_id)

                        # 构建模板快照信息
                        input_prompt_creativity = (
                            template.description if template else None
                        )
                        input_prompt_instruction = (
                            template.prompt_template if template else None
                        )
                        input_image_size_ratio = (
                            template.image_size_ratio if template else None
                        )
                        input_watermark = (
                            int(template.add_watermark)
                            if template and template.add_watermark is not None
                            else None
                        )

                        # 构建 GenerationItem 的基准参数
                        item_kwargs = {
                            "task_id": task.id,
                            "sub_user_id": sub_user_id,
                            "template_id": template_id,
                            "status": "queued",
                            "distribution_status": "draft",
                            "owner_operator_id": owner_operator_id,
                            "queued_at": datetime.now(),
                            # 创作者快照
                            "sub_user_name": sub_user_name,
                            "input_sub_user_profile": sub_user_profile,
                            "input_sub_user_positioning": sub_user_positioning,
                            "input_sub_user_style": sub_user_style,
                            # 模板快照
                            "input_prompt_creativity": input_prompt_creativity,
                            "input_prompt_instruction": input_prompt_instruction,
                            "input_image_size_ratio": input_image_size_ratio,
                            "input_watermark": input_watermark,
                            # 模型配置（使用任务指定的模型）
                            "model_platform": model_platform,
                            "model_id": model_id,
                            "image_model_platform": image_model_platform,
                            "image_model_id": image_model_id,
                        }

                        # 如果有对标素材，添加对标信息
                        if benchmark_material_id and benchmark_material:
                            item_kwargs.update(
                                {
                                    "input_benchmark_title": benchmark_material.title,
                                    "input_benchmark_content": benchmark_material.content,
                                    "input_benchmark_topic": benchmark_material.topic,
                                    "input_benchmark_images_json": (
                                        benchmark_image_urls
                                        if benchmark_image_urls
                                        else None
                                    ),
                                    "input_benchmark_text_enabled": benchmark_text_enabled,
                                    "input_benchmark_image_enabled": benchmark_image_enabled,
                                    "input_benchmark_image_reference_options": benchmark_image_reference_options,
                                    # V3.0: 图片角色配置
                                    "input_benchmark_image_roles_json": benchmark_image_roles,
                                    "input_template_product_mapping_json": template_product_mapping,
                                }
                            )

                        generation_item = GenerationItem(**item_kwargs)
                        db.add(generation_item)
                        total_items += 1
                logger.debug(
                    "[Service] 子任务创建完成 | task_id=%s | total_items=%s",
                    task.id,
                    total_items,
                )

        # 更新任务统计
        task.total_count = total_items
        task.queued_count = total_items

        # 创建初始进度日志
        progress_log = GenerationTaskProgressLog(
            task_id=task.id,
            queued_count=total_items,
            generating_count=0,
            completed_count=0,
            failed_count=0,
            status="pending",
            progress_message="任务已创建，等待开始",
        )
        db.add(progress_log)

        await db.commit()
        await db.refresh(task)
        logger.info(
            "[Service] 任务创建成功 | task_id=%s | total_items=%s | queued=%s",
            task.id,
            task.total_count,
            task.queued_count,
        )
        return task

    @staticmethod
    async def list_generation_tasks(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filter_operator_id: Optional[int] = None,
    ) -> tuple[List[GenerationTask], int]:
        """
        获取生成任务列表

        Args:
            db: 数据库会话
            owner_operator_id: 创作管理员ID，None表示获取所有数据（超级管理员）
            page: 页码
            limit: 每页数量
            status: 状态筛选
            keyword: 关键词搜索
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            filter_operator_id: 筛选的创作管理员ID（超级管理员使用）
        """
        query = select(GenerationTask).options(
            selectinload(GenerationTask.material),
            selectinload(GenerationTask.owner_operator),
        )

        # 超级管理员可以按创作管理员筛选
        if filter_operator_id is not None:
            query = query.where(GenerationTask.owner_operator_id == filter_operator_id)
        elif owner_operator_id is not None:
            query = query.where(GenerationTask.owner_operator_id == owner_operator_id)

        if status:
            query = query.where(GenerationTask.status == status)

        # 日期筛选
        if start_date:
            query = query.where(GenerationTask.created_at >= start_date)
        if end_date:
            # 结束日期包含当天，所以加一天
            end_datetime = end_date + timedelta(days=1)
            query = query.where(GenerationTask.created_at < end_datetime)

        # 关键词搜索（任务ID、任务名称或素材标题）
        if keyword:
            keyword_filter = or_(
                GenerationTask.id == int(keyword) if keyword.isdigit() else None,
                GenerationTask.name.ilike(f"%{keyword}%"),
                GenerationTask.material.has(Material.title.ilike(f"%{keyword}%")),
            )
            query = query.where(keyword_filter)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(GenerationTask.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        # 转换 material 的附件 URL
        storage_service = StorageService()
        for task in items:
            if task.material and task.material.attachments:
                for attachment in task.material.attachments:
                    if attachment.file_url:
                        attachment.file_url = storage_service.convert_url(
                            attachment.file_url
                        )

        return items, total

    @staticmethod
    async def get_generation_task(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationTask]:
        """
        获取生成任务详情
        """
        from app.models import (GenerationTaskTemplate)

        query = (
            select(GenerationTask)
            .where(GenerationTask.id == task_id)
            .options(
                selectinload(GenerationTask.material).selectinload(
                    Material.attachments
                ),
                selectinload(GenerationTask.benchmark_material).selectinload(
                    Material.attachments
                ),
                selectinload(GenerationTask.task_templates).selectinload(
                    GenerationTaskTemplate.template  # 通过 task_templates 加载关联的 template
                ),
            )
        )

        if owner_operator_id:
            query = query.where(GenerationTask.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        # 转换 material 的附件 URL
        if task and task.material and task.material.attachments:
            storage_service = StorageService()
            for attachment in task.material.attachments:
                if attachment.file_url:
                    attachment.file_url = storage_service.convert_url(
                        attachment.file_url
                    )

        # 转换 benchmark_material 的附件 URL
        if task and task.benchmark_material and task.benchmark_material.attachments:
            storage_service = StorageService()
            for attachment in task.benchmark_material.attachments:
                if attachment.file_url:
                    attachment.file_url = storage_service.convert_url(
                        attachment.file_url
                    )

        return task

    @staticmethod
    async def update_generation_task_status(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: int,
        status: str,
        progress_message: Optional[str] = None,
    ) -> Optional[GenerationTask]:
        """
        更新任务状态
        """
        logger.debug(
            "[Service] update_generation_task_status | task_id=%s | status=%s | message=%s",
            task_id,
            status,
            progress_message,
        )

        result = await db.execute(
            select(GenerationTask).where(
                and_(
                    GenerationTask.id == task_id,
                    GenerationTask.owner_operator_id == owner_operator_id,
                )
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            logger.warning("[Service] 任务不存在 | task_id=%s", task_id)
            raise GenerationTaskNotFoundError()

        old_status = task.status

        # 状态转换验证
        VALID_TASK_TRANSITIONS = {
            "pending": ["processing", "cancelled"],
            "processing": ["completed", "failed", "cancelled"],
            "completed": [],  # 终态：不可转换
            "failed": [
                "processing"
            ],  # 允许重新运行（由 update_generation_item_status 自动触发）
            "cancelled": [],  # 终态：不可转换
        }
        if old_status == status:
            logger.debug(
                "[Service] 任务状态未变化 | task_id=%s | status=%s", task_id, status
            )
        elif status not in VALID_TASK_TRANSITIONS.get(old_status, []):
            logger.warning(
                "[Service] 不允许的任务状态转换 | task_id=%s | %s -> %s",
                task_id,
                old_status,
                status,
            )
            # 不阻止，仅记录日志（因为某些状态由 update_generation_item_status 自动判定）

        task.status = status
        task.updated_at = datetime.now()

        # 设置任务开始时间：当任务从 pending 变为 processing 时
        if old_status == "pending" and status == "processing":
            task.started_at = datetime.now()
            logger.info(
                "[Service] 任务开始时间已记录 | task_id=%s | started_at=%s",
                task_id,
                task.started_at,
            )

        # 设置任务完成时间：当任务变为最终状态时
        if status in ("completed", "failed", "cancelled"):
            task.completed_at = datetime.now()
            logger.info(
                "[Service] 任务完成时间已记录 | task_id=%s | completed_at=%s",
                task_id,
                task.completed_at,
            )

        # 创建进度日志
        progress_log = GenerationTaskProgressLog(
            task_id=task.id,
            queued_count=task.queued_count,
            generating_count=task.generating_count,
            completed_count=task.completed_count,
            failed_count=task.failed_count,
            status=status,
            progress_message=progress_message,
        )
        db.add(progress_log)

        await db.commit()
        await db.refresh(task)
        logger.info(
            "[Service] 任务状态更新 | task_id=%s | %s -> %s | queued=%s | generating=%s | completed=%s | failed=%s",
            task_id,
            old_status,
            status,
            task.queued_count,
            task.generating_count,
            task.completed_count,
            task.failed_count,
        )
        return task

    @staticmethod
    async def cancel_generation_task(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationTask]:
        """
        取消任务
        """
        task = await GenerationService.get_generation_task(
            db, task_id, owner_operator_id
        )
        if not task:
            raise GenerationTaskNotFoundError()

        if task.status not in ["pending", "processing"]:
            raise ValueError("只能取消待处理或处理中的任务")

        # 更新任务状态
        task.status = "cancelled"
        task.updated_at = datetime.now()
        task.completed_at = datetime.now()

        # 取消所有未完成的子任务
        items_result = await db.execute(
            select(GenerationItem).where(
                and_(
                    GenerationItem.task_id == task_id,
                    GenerationItem.status.in_(["queued", "generating", "paused"]),
                )
            )
        )
        for item in items_result.scalars().all():
            if item.status == "queued" and task.queued_count > 0:
                task.queued_count -= 1
            elif item.status == "generating" and task.generating_count > 0:
                task.generating_count -= 1
            elif item.status == "paused" and task.paused_count > 0:
                task.paused_count -= 1
            item.status = "failed"
            item.error_message = "任务已取消"

        # 创建进度日志
        progress_log = GenerationTaskProgressLog(
            task_id=task.id,
            queued_count=task.queued_count,
            generating_count=task.generating_count,
            completed_count=task.completed_count,
            failed_count=task.failed_count,
            status="cancelled",
            progress_message="任务已取消",
        )
        db.add(progress_log)

        await db.commit()
        await db.refresh(task)
        return task

    # ============================================
    # 生成子任务管理
    # ============================================
    @staticmethod
    async def list_generation_items(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
        page: int = 1,
        limit: int = 50,
        status: Optional[str] = None,
        distribution_status: Optional[str] = None,
        sub_user_id: Optional[int] = None,
    ) -> tuple[List[GenerationItem], int]:
        """
        获取生成子任务列表
        """
        # 验证任务所有权
        if owner_operator_id:
            task = await GenerationService.get_generation_task(
                db, task_id, owner_operator_id
            )
            if not task:
                raise GenerationTaskNotFoundError()

        query = (
            select(GenerationItem)
            .options(
                selectinload(GenerationItem.sub_user),
            )
            .where(GenerationItem.task_id == task_id)
        )

        if status:
            query = query.where(GenerationItem.status == status)

        if distribution_status:
            query = query.where(
                GenerationItem.distribution_status == distribution_status
            )

        if sub_user_id:
            query = query.where(GenerationItem.sub_user_id == sub_user_id)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(GenerationItem.created_at.asc())

        result = await db.execute(query)
        items = result.scalars().all()

        # 转换所有 URL
        for item in items:
            _convert_generation_item_urls(item)

        return items, total

    @staticmethod
    async def get_generation_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationItem]:
        """
        获取生成子任务详情（包含 task 关系）
        """
        query = (
            select(GenerationItem)
            .where(GenerationItem.id == item_id)
            .options(selectinload(GenerationItem.task))
        )

        if owner_operator_id:
            query = query.where(GenerationItem.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        item = result.scalar_one_or_none()

        # 转换 URL
        if item:
            _convert_generation_item_urls(item)

        return item

    @staticmethod
    async def update_generation_item_status(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
        status: str = None,
        error_message: Optional[str] = None,
        expected_old_status: Optional[str] = None,
    ) -> Optional[GenerationItem]:
        """
        更新子任务状态

        使用 SQL 原子更新计数器，避免并行任务下的 read-modify-write 竞态。
        核心原则：每个 item 在同一时刻只能属于一个状态计数器，
        状态变更时通过一条 SQL 同时完成「旧状态 -1」和「新状态 +1」。

        Args:
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可操作所有记录）
            expected_old_status: CAS 守卫条件，若指定则仅当 item 当前状态等于此值时才更新，
                                 防止并发场景下同一 item 被多个 worker 同时拾取。
                                 返回 None 表示状态已被其他 worker 改变。
        """
        logger.debug(
            "[Service] update_generation_item_status | item_id=%s | new_status=%s | error=%s | expected_old=%s",
            item_id,
            status,
            error_message[:100] if error_message else None,
            expected_old_status,
        )

        # 构建查询条件：超级管理员不限制 owner_operator_id
        query_conditions = [GenerationItem.id == item_id]
        if owner_operator_id is not None:
            query_conditions.append(
                GenerationItem.owner_operator_id == owner_operator_id
            )
        if expected_old_status is not None:
            query_conditions.append(GenerationItem.status == expected_old_status)

        result = await db.execute(select(GenerationItem).where(and_(*query_conditions)))
        item = result.scalar_one_or_none()
        if not item:
            if expected_old_status is not None:
                # CAS 条件不满足：item 存在但状态已被其他 worker 改变
                logger.info(
                    "[Service] CAS 守卫失败，子任务状态已变更 | item_id=%s | expected=%s",
                    item_id,
                    expected_old_status,
                )
                return None
            # item 确实不存在
            logger.warning("[Service] 子任务不存在 | item_id=%s", item_id)
            raise GenerationItemNotFoundError()

        old_status = item.status
        task_id = item.task_id

        # === 原子更新 GenerationTask 计数器（消除 read-modify-write 竞态） ===
        # 构建一条 SQL：旧状态计数 -1，新状态计数 +1，使用 GREATEST 防止下溢
        # 注意：当 old_status == status 时，同一列需要 net 0（不操作），跳过计数更新
        decrement_map = {
            "queued": GenerationTask.queued_count,
            "generating": GenerationTask.generating_count,
            "completed": GenerationTask.completed_count,
            "failed": GenerationTask.failed_count,
            "paused": GenerationTask.paused_count,
        }

        values = {"updated_at": datetime.now()}

        if old_status == status:
            # 同状态转换（如 failed → failed），计数不变
            pass
        elif old_status in decrement_map and status in decrement_map:
            old_col = decrement_map[old_status]
            new_col = decrement_map[status]
            if old_col.key == new_col.key:
                # 不同状态名但映射到同一列（不应发生，防御性编程）
                pass
            else:
                # 旧状态计数 -1（GREATEST 防止负数），新状态计数 +1
                values[old_col.key] = func.greatest(old_col - 1, 0)
                values[new_col.key] = new_col + 1
        else:
            # 仅单侧有映射
            if old_status in decrement_map:
                col = decrement_map[old_status]
                values[col.key] = func.greatest(col - 1, 0)
            if status in decrement_map:
                col = decrement_map[status]
                values[col.key] = col + 1

        stmt = (
            sa_update(GenerationTask)
            .where(GenerationTask.id == task_id)
            .values(**values)
        )
        await db.execute(stmt)
        await db.flush()

        logger.debug(
            "[Service] 任务计数原子更新 | task_id=%s | old_status=%s -> new_status=%s",
            task_id,
            old_status,
            status,
        )

        # 更新子任务字段
        item.status = status

        # 状态变更时清理错误信息（重试或成功时）
        if status in ("queued", "generating", "completed") and old_status == "failed":
            item.error_message = None
            logger.debug("[Service] 清除旧错误信息 | item_id=%s", item_id)

        if status == "generating":
            item.started_at = datetime.now()
        elif status == "completed":
            item.completed_at = datetime.now()
            item.error_message = None
            # 子任务完成时，设置为待发布状态并更新计数
            item.distribution_status = "pending_publish"
            # 更新任务的待发布计数
            stmt = (
                sa_update(GenerationTask)
                .where(GenerationTask.id == task_id)
                .values(
                    pending_publish_count=GenerationTask.pending_publish_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.execute(stmt)
        elif status == "failed" and error_message:
            item.error_message = error_message
            if old_status != "failed":
                item.retry_count += 1
        item.updated_at = datetime.now()

        # 从当前 session 获取 task 对象（expire 缓存后强制从数据库读取最新值）
        # 注意：先 flush 确保原子更新已执行，然后 expire_all 清除缓存
        await db.flush()
        task_result = await db.execute(
            select(GenerationTask).where(GenerationTask.id == task_id)
        )
        task = task_result.scalar_one_or_none()
        if not task:
            logger.warning(
                "[Service] 关联任务不存在 | item_id=%s | task_id=%s", item_id, task_id
            )
            raise GenerationTaskNotFoundError()

        logger.debug(
            "[Service] 任务统计快照 | task_id=%s | "
            "queued=%s | generating=%s | completed=%s | failed=%s | paused=%s",
            task.id,
            task.queued_count,
            task.generating_count,
            task.completed_count,
            task.failed_count,
            task.paused_count,
        )

        # 检查任务是否完成 - 当没有正在运行或等待的子任务时
        if (
            task.queued_count == 0
            and task.generating_count == 0
            and task.paused_count == 0
        ):
            # 所有子任务都结束了
            now = datetime.now()
            final_status = None
            if task.failed_count > 0:
                # 有失败项 - 任务标记为失败
                task.status = "failed"
                task.completed_at = now
                final_status = "failed"
                logger.info(
                    "[Service] 任务已失败（有子任务失败）| task_id=%s | failed_count=%s | completed_count=%s",
                    task.id,
                    task.failed_count,
                    task.completed_count,
                )
            elif task.completed_count > 0:
                # 全部成功
                task.status = "completed"
                task.completed_at = now
                final_status = "completed"
                logger.info(
                    "[Service] 任务全部完成 | task_id=%s | completed=%s",
                    task.id,
                    task.completed_count,
                )
            else:
                # 全部暂停（无完成无失败），保持 processing 状态
                logger.info(
                    "[Service] 任务无完成项（全部暂停） | task_id=%s | paused=%s",
                    task.id,
                    task.paused_count,
                )

            # 同步更新定时任务执行记录
            if final_status:
                await _sync_scheduled_task_execution(
                    db,
                    task.id,
                    final_status,
                    task.total_count,
                    task.completed_count,
                    task.failed_count,
                    now,
                )
        else:
            # 还有子任务在运行或等待 - 确保任务状态是 processing
            if task.status != "processing":
                old_task_status = task.status
                task.status = "processing"
                logger.info(
                    "[Service] 任务恢复运行状态 | task_id=%s | %s -> processing",
                    task.id,
                    old_task_status,
                )

        # 如果 item 从 completed/failed 重新变为 queued/generating，
        # 不管任务之前是什么状态，都确保任务状态是 processing
        if status in ("queued", "generating") and old_status in ("completed", "failed"):
            if task.status != "processing":
                task.status = "processing"
                logger.info(
                    "[Service] 任务重新运行 | task_id=%s | item_id=%s | %s -> processing",
                    task.id,
                    item_id,
                    old_status,
                )

        # 创建进度日志
        progress_log = GenerationTaskProgressLog(
            task_id=task.id,
            queued_count=task.queued_count,
            generating_count=task.generating_count,
            completed_count=task.completed_count,
            failed_count=task.failed_count,
            status=task.status,
        )
        db.add(progress_log)

        task.updated_at = datetime.now()

        await db.commit()
        # commit 后 item 已持久化，直接返回（不需要 refresh，减少数据库连接）
        logger.info(
            "[Service] 子任务状态更新 | item_id=%s | task_id=%s | %s -> %s | retry_count=%s",
            item_id,
            task.id,
            old_status,
            status,
            item.retry_count,
        )
        return item

    @staticmethod
    async def recalculate_task_counts(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationTask]:
        """
        重新计算任务的统计计数（修复因历史bug导致的计数错误）

        从实际的子任务状态重新统计，确保计数器与真实状态一致。

        Args:
            db: 数据库会话
            task_id: 任务ID
            owner_operator_id: 创作管理员ID

        Returns:
            更新后的任务对象
        """
        logger.info(
            "[Service] recalculate_task_counts | task_id=%s | owner=%s",
            task_id,
            owner_operator_id,
        )

        task = await GenerationService.get_generation_task(
            db, task_id, owner_operator_id
        )
        if not task:
            logger.warning("[Service] 任务不存在 | task_id=%s", task_id)
            return None

        # 获取所有子任务
        page = 1
        all_items = []
        while True:
            items, _ = await GenerationService.list_generation_items(
                db, task_id, owner_operator_id, page=page, limit=500
            )
            if not items:
                break
            all_items.extend(items)
            page += 1

        # 重新统计生成状态
        queued_count = sum(1 for item in all_items if item.status == "queued")
        generating_count = sum(1 for item in all_items if item.status == "generating")
        completed_count = sum(1 for item in all_items if item.status == "completed")
        failed_count = sum(1 for item in all_items if item.status == "failed")
        paused_count = sum(1 for item in all_items if item.status == "paused")

        # 重新统计分发状态
        distributed_count = sum(
            1 for item in all_items if item.distribution_status == "distributed"
        )
        pending_publish_count = sum(
            1
            for item in all_items
            if item.distribution_status in ("distributed", "pending_publish")
        )
        published_count = sum(
            1 for item in all_items if item.distribution_status == "published"
        )

        old_counts = (
            task.queued_count,
            task.generating_count,
            task.completed_count,
            task.failed_count,
            task.paused_count,
            task.pending_publish_count,
            task.published_count,
        )
        new_counts = (
            queued_count,
            generating_count,
            completed_count,
            failed_count,
            paused_count,
            pending_publish_count,
            published_count,
        )

        logger.info(
            "[Service] 重新计算计数 | task_id=%s | old=%s | new=%s | total_items=%s",
            task_id,
            old_counts,
            new_counts,
            len(all_items),
        )

        # 更新生成状态计数
        task.queued_count = queued_count
        task.generating_count = generating_count
        task.completed_count = completed_count
        task.failed_count = failed_count
        task.paused_count = paused_count

        # 更新分发状态计数
        task.distributed_count = distributed_count
        task.pending_publish_count = pending_publish_count
        task.published_count = published_count

        # 更新 total_count 为子任务总数
        task.total_count = len(all_items)

        # 更新任务状态
        if queued_count == 0 and generating_count == 0 and paused_count == 0:
            now = datetime.now()
            if failed_count > 0:
                task.status = "failed"
                # 首次完成/失败时设置 completed_at
                if task.completed_at is None:
                    task.completed_at = now
            elif completed_count > 0:
                task.status = "completed"
                # 首次完成时设置 completed_at
                if task.completed_at is None:
                    task.completed_at = now
            else:
                task.status = "pending"  # 全部暂停，回到初始状态
        else:
            task.status = "processing"

        task.updated_at = datetime.now()
        await db.commit()

        logger.info(
            "[Service] 计数修复完成 | task_id=%s | status=%s | %s",
            task_id,
            task.status,
            new_counts,
        )
        return task

    @staticmethod
    async def attach_live_counts(
        db: AsyncSession,
        tasks: List,
    ) -> None:
        """
        为任务列表实时聚合各状态计数（从 generation_item 表计算，不依赖冗余字段）。

        在每个 task 对象上设置 _live_counts 字典，供 API 层优先使用。
        """
        if not tasks:
            return

        task_ids = [t.id for t in tasks]
        count_stmt = (
            select(
                GenerationItem.task_id,
                func.count().label("total"),
                func.sum(func.cast(GenerationItem.status == "queued", Integer)).label(
                    "queued"
                ),
                func.sum(
                    func.cast(GenerationItem.status == "generating", Integer)
                ).label("generating"),
                func.sum(
                    func.cast(GenerationItem.status == "completed", Integer)
                ).label("completed"),
                func.sum(func.cast(GenerationItem.status == "failed", Integer)).label(
                    "failed"
                ),
                func.sum(func.cast(GenerationItem.status == "paused", Integer)).label(
                    "paused"
                ),
                func.sum(
                    func.cast(
                        GenerationItem.distribution_status.in_(
                            ["distributed", "pending_publish"]
                        ),
                        Integer,
                    )
                ).label("pending_publish"),
                func.sum(
                    func.cast(
                        GenerationItem.distribution_status == "published", Integer
                    )
                ).label("published"),
            )
            .where(GenerationItem.task_id.in_(task_ids))
            .group_by(GenerationItem.task_id)
        )
        count_result = await db.execute(count_stmt)
        count_map = {row.task_id: row for row in count_result.all()}

        default_counts = {
            "total_count": 0,
            "queued_count": 0,
            "generating_count": 0,
            "completed_count": 0,
            "failed_count": 0,
            "paused_count": 0,
            "pending_publish_count": 0,
            "published_count": 0,
        }

        for task in tasks:
            counts = count_map.get(task.id)
            if counts:
                task._live_counts = {
                    "total_count": int(counts.total or 0),
                    "queued_count": int(counts.queued or 0),
                    "generating_count": int(counts.generating or 0),
                    "completed_count": int(counts.completed or 0),
                    "failed_count": int(counts.failed or 0),
                    "paused_count": int(counts.paused or 0),
                    "pending_publish_count": int(counts.pending_publish or 0),
                    "published_count": int(counts.published or 0),
                }
            else:
                task._live_counts = dict(default_counts)

    @staticmethod
    async def check_task_exists(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        检查父任务是否存在

        Args:
            task_id: 任务ID
            owner_operator_id: 创作管理员ID，None 表示不检查 owner

        Returns:
            bool: 任务是否存在
        """
        conditions = [GenerationTask.id == task_id]
        if owner_operator_id is not None:
            conditions.append(GenerationTask.owner_operator_id == owner_operator_id)

        result = await db.execute(
            select(GenerationTask.id).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def delete_orphaned_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        删除孤儿子任务（父任务已不存在）

        Args:
            item_id: 子任务ID
            owner_operator_id: 创作管理员ID

        Returns:
            bool: 是否成功删除
        """
        logger.warning(
            "[Service] delete_orphaned_item: 删除孤儿子任务 | item_id=%s", item_id
        )

        conditions = [GenerationItem.id == item_id]
        if owner_operator_id is not None:
            conditions.append(GenerationItem.owner_operator_id == owner_operator_id)

        result = await db.execute(select(GenerationItem).where(and_(*conditions)))
        item = result.scalar_one_or_none()

        if not item:
            logger.warning(
                "[Service] delete_orphaned_item: 子任务不存在 | item_id=%s", item_id
            )
            return False

        # 删除子任务
        await db.delete(item)
        await db.commit()

        logger.info(
            "[Service] delete_orphaned_item: 孤儿子任务已删除 | item_id=%s", item_id
        )
        return True

    @staticmethod
    async def reset_item_for_regeneration(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationItem]:
        """
        重置子任务以重新生成（统一处理 retry 和 regenerate）

        Args:
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可操作所有记录）

        支持状态：
            - failed: 重试失败任务
            - completed + pending_publish: 重新生成已完成的待发布任务
        """
        logger.debug(
            "[Service] reset_item_for_regeneration | item_id=%s | owner=%s",
            item_id,
            owner_operator_id,
        )

        # 构建查询条件：超级管理员不限制 owner_operator_id
        conditions = [GenerationItem.id == item_id]
        if owner_operator_id is not None:
            conditions.append(GenerationItem.owner_operator_id == owner_operator_id)

        result = await db.execute(select(GenerationItem).where(and_(*conditions)))
        item = result.scalar_one_or_none()
        if not item:
            logger.warning(
                "[Service] reset_item_for_regeneration: 子任务不存在 | item_id=%s",
                item_id,
            )
            raise GenerationItemNotFoundError()

        # 检查允许的状态
        allowed = False
        if item.status == "failed":
            allowed = True
            logger.info(
                "[Service] reset_item_for_regeneration: 重试失败任务 | item_id=%s",
                item_id,
            )
        elif (
            item.status == "completed" and item.distribution_status == "pending_publish"
        ):
            allowed = True
            logger.info(
                "[Service] reset_item_for_regeneration: 重新生成已完成任务 | item_id=%s",
                item_id,
            )
        elif item.status == "queued":
            # 已经是待处理状态，直接返回
            logger.info(
                "[Service] reset_item_for_regeneration: 子任务已是待处理状态 | item_id=%s",
                item_id,
            )
            return item

        if not allowed:
            logger.warning(
                "[Service] reset_item_for_regeneration: 状态不允许重置 | item_id=%s | status=%s | distribution_status=%s",
                item_id,
                item.status,
                item.distribution_status,
            )
            raise ValueError(
                f"无法重置该子任务：状态为 {item.status}，分发状态为 {item.distribution_status}"
            )

        # 清除之前的生成结果（如果有）
        item.generated_title = None
        item.generated_text = None
        item.generated_image_urls_json = None
        item.generated_image_thumbnails_json = None
        item.output_topics = None
        item.aigc_user_image_prompts_json = None
        item.creative_seed_ids_json = None
        item.viral_type = None
        item.dedup_passed = None
        item.dedup_checked_at = None
        item.error_message = None
        item.retry_count = 0
        item.started_at = None
        item.completed_at = None
        item.current_step = None

        # 重置状态为 queued
        item.status = "queued"
        item.updated_at = datetime.now()

        await db.commit()
        await db.refresh(item)

        # 更新父任务状态
        task_id = item.task_id
        await GenerationService.recalculate_task_counts(db, task_id)

        logger.info(
            "[Service] reset_item_for_regeneration: 子任务已重置 | item_id=%s | new_status=%s",
            item_id,
            item.status,
        )
        return item

    # 兼容旧方法的别名
    @staticmethod
    async def retry_failed_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationItem]:
        """重试失败的子任务（兼容旧接口）"""
        return await GenerationService.reset_item_for_regeneration(
            db, item_id, owner_operator_id
        )

    @staticmethod
    async def regenerate_completed_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[GenerationItem]:
        """重新生成已完成的子任务（兼容旧接口）"""
        return await GenerationService.reset_item_for_regeneration(
            db, item_id, owner_operator_id
        )

    @staticmethod
    async def toggle_pause_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
        pause: bool = True,
    ) -> Optional[GenerationItem]:
        """
        暂停/继续子任务

        Args:
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可操作所有记录）
        """
        action = "暂停" if pause else "继续"
        logger.info(
            "[Service] toggle_pause_item: %s子任务 | item_id=%s | owner=%s",
            action,
            item_id,
            owner_operator_id,
        )

        # 构建查询条件：超级管理员不限制 owner_operator_id
        conditions = [GenerationItem.id == item_id]
        if owner_operator_id is not None:
            conditions.append(GenerationItem.owner_operator_id == owner_operator_id)

        # 先查询获取 item 和 task_id
        result = await db.execute(select(GenerationItem).where(and_(*conditions)))
        item = result.scalar_one_or_none()
        if not item:
            logger.warning(
                "[Service] toggle_pause_item: 子任务不存在 | item_id=%s", item_id
            )
            raise GenerationItemNotFoundError()

        old_status = item.status
        task_id = item.task_id

        # 验证状态转换
        if pause:
            if old_status not in ["queued", "generating"]:
                logger.warning(
                    "[Service] toggle_pause_item: 状态不允许暂停 | item_id=%s | status=%s",
                    item_id,
                    old_status,
                )
                raise ValueError("只能暂停队列中或生成中的子任务")
            new_status = "paused"
        else:
            if old_status != "paused":
                logger.warning(
                    "[Service] toggle_pause_item: 状态不允许继续 | item_id=%s | status=%s",
                    item_id,
                    old_status,
                )
                raise ValueError("只能继续已暂停的子任务")
            new_status = "queued"  # 恢复后重新排队，由 Celery task 处理

        logger.info(
            "[Service] toggle_pause_item: 状态变更 | item_id=%s | task_id=%s | %s -> %s",
            item_id,
            task_id,
            old_status,
            new_status,
        )

        # 使用直接的 SQL 更新，减少锁持有时间
        # 1. 先更新 generation_item
        update_item_stmt = (
            sa_update(GenerationItem)
            .where(GenerationItem.id == item_id)
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
        await db.execute(update_item_stmt)

        # 2. 再更新 generation_task 的计数（原子操作）
        decrement_map = {
            "queued": GenerationTask.queued_count,
            "generating": GenerationTask.generating_count,
            "completed": GenerationTask.completed_count,
            "failed": GenerationTask.failed_count,
            "paused": GenerationTask.paused_count,
        }

        task_update_values = {"updated_at": datetime.now()}

        if old_status in decrement_map and new_status in decrement_map:
            old_col = decrement_map[old_status]
            new_col = decrement_map[new_status]
            if old_col.key != new_col.key:
                task_update_values[old_col.key] = func.greatest(old_col - 1, 0)
                task_update_values[new_col.key] = new_col + 1
        elif old_status in decrement_map:
            col = decrement_map[old_status]
            task_update_values[col.key] = func.greatest(col - 1, 0)
        elif new_status in decrement_map:
            col = decrement_map[new_status]
            task_update_values[col.key] = col + 1

        if task_update_values:
            update_task_stmt = (
                sa_update(GenerationTask)
                .where(GenerationTask.id == task_id)
                .values(**task_update_values)
            )
            await db.execute(update_task_stmt)

        # 3. 提交事务
        await db.commit()

        # 4. 重新查询返回
        result = await db.execute(
            select(GenerationItem).where(GenerationItem.id == item_id)
        )
        updated_item = result.scalar_one_or_none()

        logger.info(
            "[Service] toggle_pause_item: 完成 | item_id=%s | old=%s -> new=%s",
            item_id,
            old_status,
            new_status,
        )
        return updated_item

    @staticmethod
    async def batch_retry_items(
        db: AsyncSession,
        item_ids: Optional[List[int]] = None,
        task_id: Optional[int] = None,
        owner_operator_id: Optional[int] = None,
    ) -> List[GenerationItem]:
        """
        批量重试失败的子任务

        Args:
            db: 数据库会话
            item_ids: 要重试的子任务ID列表（可选）
            task_id: 任务ID（当 item_ids 为空时，重试该任务下所有失败项）
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可操作所有记录）
        """
        logger.debug(
            "[Service] batch_retry_items | item_ids=%s | task_id=%s | owner=%s",
            item_ids,
            task_id,
            owner_operator_id,
        )

        if not item_ids and not task_id:
            raise ValueError("必须提供 item_ids 或 task_id")

        # 构建查询条件：超级管理员不限制 owner_operator_id
        if item_ids:
            # 重试指定的子任务
            conditions = [
                GenerationItem.id.in_(item_ids),
                GenerationItem.status == "failed",
            ]
            if owner_operator_id is not None:
                conditions.append(GenerationItem.owner_operator_id == owner_operator_id)
            query = select(GenerationItem).where(and_(*conditions))
        else:
            # 重试指定任务下所有失败的子任务
            conditions = [
                GenerationItem.task_id == task_id,
                GenerationItem.status == "failed",
            ]
            if owner_operator_id is not None:
                conditions.append(GenerationItem.owner_operator_id == owner_operator_id)
            query = select(GenerationItem).where(and_(*conditions))

        result = await db.execute(query)
        items = result.scalars().all()
        logger.info("[Service] batch_retry_items: 找到 %s 个失败子任务", len(items))

        # 重试每个失败的子任务
        retried_items = []
        for item in items:
            logger.debug(
                "[Service] 重试子任务 | item_id=%s | current_status=%s",
                item.id,
                item.status,
            )
            retried_item = await GenerationService.update_generation_item_status(
                db, item.id, owner_operator_id, "queued"
            )
            if retried_item:
                retried_items.append(retried_item)

        await db.commit()
        logger.info(
            "[Service] batch_retry_items: 成功重试 %s 个子任务", len(retried_items)
        )
        return retried_items

    @staticmethod
    async def batch_pause_items(
        db: AsyncSession,
        item_ids: List[int],
        pause: bool,
        owner_operator_id: Optional[int] = None,
    ) -> List[GenerationItem]:
        """
        批量暂停/继续子任务

        Args:
            db: 数据库会话
            item_ids: 要操作的子任务ID列表
            pause: True=暂停, False=继续
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可操作所有记录）
        """
        action = "暂停" if pause else "继续"
        logger.info(
            "[Service] batch_pause_items | item_ids=%s | action=%s | owner=%s | count=%s",
            item_ids,
            action,
            owner_operator_id,
            len(item_ids),
        )

        if not item_ids:
            raise ValueError("必须提供 item_ids")

        new_status = "paused" if pause else "queued"
        allowed_old_statuses = ["queued", "generating"] if pause else ["paused"]

        # 构建查询条件：超级管理员不限制 owner_operator_id
        conditions = [
            GenerationItem.id.in_(item_ids),
            GenerationItem.status.in_(allowed_old_statuses),
        ]
        if owner_operator_id is not None:
            conditions.append(GenerationItem.owner_operator_id == owner_operator_id)

        # 先查询符合条件的子任务及其 task_id
        query = select(
            GenerationItem.id, GenerationItem.task_id, GenerationItem.status
        ).where(and_(*conditions))
        result = await db.execute(query)
        rows = result.all()

        if not rows:
            logger.info("[Service] batch_pause_items: 没有符合条件的子任务")
            return []

        logger.info(
            "[Service] batch_pause_items: 找到 %s 个符合条件的子任务", len(rows)
        )

        # 按 task_id 分组，统计每个状态的变化
        from collections import defaultdict

        task_updates = defaultdict(
            lambda: defaultdict(int)
        )  # task_id -> {old_status: count}
        item_ids_to_update = []

        for row in rows:
            item_id, task_id, old_status = row
            item_ids_to_update.append(item_id)
            task_updates[task_id][old_status] += 1

        # 1. 批量更新 generation_item
        update_item_stmt = (
            sa_update(GenerationItem)
            .where(GenerationItem.id.in_(item_ids_to_update))
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
        await db.execute(update_item_stmt)

        # 2. 批量更新每个 generation_task 的计数
        decrement_map = {
            "queued": GenerationTask.queued_count,
            "generating": GenerationTask.generating_count,
            "completed": GenerationTask.completed_count,
            "failed": GenerationTask.failed_count,
            "paused": GenerationTask.paused_count,
        }

        for task_id, status_counts in task_updates.items():
            task_update_values = {"updated_at": datetime.now()}

            for old_status, count in status_counts.items():
                # 旧状态减 count
                if old_status in decrement_map:
                    old_col = decrement_map[old_status]
                    task_update_values[old_col.key] = func.greatest(old_col - count, 0)

                # 新状态加 count
                if new_status in decrement_map:
                    new_col = decrement_map[new_status]
                    if new_col.key in task_update_values:
                        # 已经有值了，累加
                        task_update_values[new_col.key] = new_col + count
                    else:
                        task_update_values[new_col.key] = new_col + count

            if task_update_values:
                update_task_stmt = (
                    sa_update(GenerationTask)
                    .where(GenerationTask.id == task_id)
                    .values(**task_update_values)
                )
                await db.execute(update_task_stmt)

        # 3. 提交事务
        await db.commit()

        # 4. 重新查询返回
        result = await db.execute(
            select(GenerationItem).where(GenerationItem.id.in_(item_ids_to_update))
        )
        updated_items = result.scalars().all()

        logger.info(
            "[Service] batch_pause_items: 完成 | 处理了 %s 个子任务", len(updated_items)
        )
        return updated_items

    # ============================================
    # 任务字段更新
    # ============================================
    @staticmethod
    async def update_generation_task_fields(
        db: AsyncSession,
        task_id: int,
        update_data: Any,  # GenerationTaskUpdate
        owner_operator_id: Optional[int] = None,
    ) -> GenerationTask:
        """
        更新生成任务的配置字段（模型、去重等）

        仅更新请求中非 None 的字段。
        """

        # 查询任务
        query = select(GenerationTask).where(GenerationTask.id == task_id)
        if owner_operator_id:
            query = query.where(GenerationTask.owner_operator_id == owner_operator_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 逐字段更新（仅更新非 None 字段）
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(task, field):
                setattr(task, field, value)

        await db.commit()
        await db.refresh(task)

        logger.info(
            "[Service] 任务字段更新 | task_id=%s | fields=%s",
            task_id,
            list(update_dict.keys()),
        )

        return task

    # ============================================
    # 进度日志管理
    # ============================================
    @staticmethod
    async def get_task_progress_logs(
        db: AsyncSession,
        task_id: int,
        owner_operator_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[GenerationTaskProgressLog]:
        """
        获取任务进度日志
        """
        # 验证任务所有权
        if owner_operator_id:
            task = await GenerationService.get_generation_task(
                db, task_id, owner_operator_id
            )
            if not task:
                raise GenerationTaskNotFoundError()

        query = select(GenerationTaskProgressLog).where(
            GenerationTaskProgressLog.task_id == task_id
        )
        query = query.order_by(GenerationTaskProgressLog.created_at.desc())
        query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    # ============================================
    # 执行日志管理
    # ============================================
    @staticmethod
    async def create_execution_log(
        db: AsyncSession,
        item_id: int,
        node_name: str,
        node_status: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> GenerationItemExecutionLog:
        """
        创建执行日志
        """
        log = GenerationItemExecutionLog(
            item_id=item_id,
            node_name=node_name,
            node_status=node_status,
            input_data=input_data,
            output_data=output_data,
            error_data=error_data,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def update_execution_log(
        db: AsyncSession,
        log_id: int,
        node_status: Optional[str] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[GenerationItemExecutionLog]:
        """
        更新执行日志
        """
        result = await db.execute(
            select(GenerationItemExecutionLog).where(
                GenerationItemExecutionLog.id == log_id
            )
        )
        log = result.scalar_one_or_none()
        if not log:
            return None

        if node_status is not None:
            log.node_status = node_status
        if output_data is not None:
            log.output_data = output_data
        if error_data is not None:
            log.error_data = error_data
        if duration_ms is not None:
            log.duration_ms = duration_ms
        if completed_at is not None:
            log.completed_at = completed_at

        await db.flush()
        return log

    @staticmethod
    async def get_item_execution_logs(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> List[GenerationItemExecutionLog]:
        """
        获取子任务的执行日志列表
        """
        # 验证子任务所有权
        if owner_operator_id:
            item = await GenerationService.get_generation_item(
                db, item_id, owner_operator_id
            )
            if not item:
                raise GenerationItemNotFoundError()

        query = select(GenerationItemExecutionLog).where(
            GenerationItemExecutionLog.item_id == item_id
        )
        query = query.order_by(GenerationItemExecutionLog.created_at.asc())

        result = await db.execute(query)
        return result.scalars().all()

    # ============================================
    # 发布管理
    # ============================================
    @staticmethod
    async def publish_item(
        db: AsyncSession,
        item_id: int,
        owner_operator_id: Optional[int] = None,
        sub_user_id: Optional[int] = None,
    ) -> GenerationItem:
        """
        标记生成子任务为已发布

        Args:
            db: 数据库会话
            item_id: 子任务ID
            owner_operator_id: 创作管理员ID（权限验证）
            sub_user_id: 创作者ID（创作者只能标记自己的内容）

        Returns:
            更新后的子任务
        """
        logger.debug(
            "[GenerationService] publish_item | item_id=%s | owner=%s | sub_user=%s",
            item_id,
            owner_operator_id,
            sub_user_id,
        )

        # 获取子任务 - 根据调用者角色使用不同的查询逻辑
        if sub_user_id is not None:
            # 创作者只能操作自己的内容，按 sub_user_id 查询
            query = select(GenerationItem).where(
                and_(
                    GenerationItem.id == item_id,
                    GenerationItem.sub_user_id == sub_user_id,
                )
            )
            result = await db.execute(query)
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("生成子任务不存在或无权操作")
        else:
            # 创作管理员或超级管理员，按 owner_operator_id 查询
            item = await GenerationService.get_generation_item(
                db, item_id, owner_operator_id
            )
            if not item:
                raise ValueError("生成子任务不存在")

        # 验证状态 - 只能标记待发布的内容
        if item.distribution_status != "pending_publish":
            raise ValueError("内容不是待发布状态，无法标记为已发布")

        # 更新状态
        item.distribution_status = "published"
        item.confirmed_at = datetime.now()

        # 更新任务的分发统计计数
        task_id = item.task_id
        stmt = (
            sa_update(GenerationTask)
            .where(GenerationTask.id == task_id)
            .values(
                pending_publish_count=func.greatest(
                    GenerationTask.pending_publish_count - 1, 0
                ),
                published_count=GenerationTask.published_count + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await db.execute(stmt)

        await db.commit()
        await db.refresh(item)

        logger.info(
            "[GenerationService] publish_item 成功 | item_id=%s | new_status=%s",
            item_id,
            item.distribution_status,
        )

        return item

    @staticmethod
    async def get_sub_user_items(
        db: AsyncSession,
        sub_user_id: int,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        distribution_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取创作者的内容列表

        Args:
            db: 数据库会话
            sub_user_id: 创作者ID
            page: 页码
            limit: 每页数量
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            distribution_status: 分发状态筛选（pending_publish/published）

        Returns:
            包含 items, total, page, limit 的字典
        """
        logger.debug(
            "[GenerationService] get_sub_user_items | sub_user=%s | page=%s | limit=%s | distribution_status=%s",
            sub_user_id,
            page,
            limit,
            distribution_status,
        )

        # 查询创作者的所有内容项，同时关联任务获取任务名称
        query = (
            select(GenerationItem)
            .options(
                selectinload(GenerationItem.task),
            )
            .where(GenerationItem.sub_user_id == sub_user_id)
        )

        # 日期筛选
        if start_date:
            query = query.where(GenerationItem.created_at >= start_date)
        if end_date:
            # 结束日期包含当天，所以加一天
            end_datetime = end_date + timedelta(days=1)
            query = query.where(GenerationItem.created_at < end_datetime)

        # 分发状态筛选
        if distribution_status:
            query = query.where(
                GenerationItem.distribution_status == distribution_status
            )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(GenerationItem.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        # 转换为响应格式，包含 task_name
        response_items = []
        for item in items:
            prefer_url = get_settings().image_prefer_url
            item_dict = {
                "id": item.id,
                "task_id": item.task_id,
                "task_name": item.task.name if item.task else None,
                "sub_user_id": item.sub_user_id,
                "sub_user_name": item.sub_user_name,
                "template_id": item.template_id,
                "model_platform": item.model_platform,
                "model_id": item.model_id,
                "image_model_platform": item.image_model_platform,
                "image_model_id": item.image_model_id,
                "generated_title": item.generated_title,
                "generated_text": item.generated_text,
                "generated_image_urls_json": _process_urls(
                    item.generated_image_urls_json, prefer_url
                ),
                "generated_image_thumbnails_json": _process_urls(
                    item.generated_image_thumbnails_json, prefer_url
                ),
                "generated_video_url": (
                    _process_url(item.generated_video_url, prefer_url)
                    if item.generated_video_url
                    else None
                ),
                "output_topics": item.output_topics,
                "status": item.status,
                "distribution_status": item.distribution_status,
                "retry_count": item.retry_count,
                "error_message": item.error_message,
                "queued_at": item.queued_at,
                "started_at": item.started_at,
                "completed_at": item.completed_at,
                "distributed_at": item.distributed_at,
                "confirmed_at": item.confirmed_at,
                "execution_started_at": item.execution_started_at,
                "execution_ended_at": item.execution_ended_at,
                "execution_result": item.execution_result,
                "current_step": item.current_step,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            response_items.append(item_dict)

        logger.info(
            "[GenerationService] get_sub_user_items 成功 | sub_user=%s | count=%s | total=%s",
            sub_user_id,
            len(response_items),
            total,
        )

        return {
            "items": response_items,
            "total": total,
            "page": page,
            "limit": limit,
        }


async def _sync_scheduled_task_execution(
    db,
    generation_task_id: int,
    final_status: str,
    total_items: int,
    success_items: int,
    failed_items: int,
    completed_at,
):
    """
    同步定时任务执行记录：当 generation_task 完成时更新对应的 scheduled_task_execution 记录
    """
    import logging

    _logger = logging.getLogger(__name__)

    from sqlalchemy import select

    from app.models.scheduled_task import ScheduledTask
    from app.models.scheduled_task_execution import ScheduledTaskExecution

    try:
        # 查找关联的执行记录
        result = await db.execute(
            select(ScheduledTaskExecution)
            .where(ScheduledTaskExecution.generation_task_id == generation_task_id)
            .order_by(ScheduledTaskExecution.id.desc())
            .limit(1)
        )
        execution = result.scalar_one_or_none()

        if execution:
            execution.status = final_status
            execution.completed_at = completed_at
            execution.success_items = success_items
            execution.failed_items = failed_items
            execution.total_items = total_items

            # 同步更新定时任务的成功/失败计数
            if execution.scheduled_task_id:
                stmt = select(ScheduledTask).where(
                    ScheduledTask.id == execution.scheduled_task_id
                )
                st_result = await db.execute(stmt)
                scheduled_task = st_result.scalar_one_or_none()
                if scheduled_task:
                    if final_status == "completed":
                        scheduled_task.successful_executions += 1
                    elif final_status == "failed":
                        scheduled_task.failed_executions += 1
                    scheduled_task.last_execution_status = final_status
                    scheduled_task.last_execution_at = completed_at

            _logger.info(
                f"[Synchook] 执行记录已同步 | generation_task_id={generation_task_id} | "
                f"status={final_status} | total={total_items} | success={success_items} | failed={failed_items}"
            )
    except Exception as e:
        _logger.error(
            f"[Synchook] 同步执行记录失败 | generation_task_id={generation_task_id} | error={str(e)}"
        )
