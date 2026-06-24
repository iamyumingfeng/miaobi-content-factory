"""
内容生成 API 路由 (generation.py)

Author: Claude Code
Date: 2025
"""

import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime

from app.core.database import get_async_db
from app.core.config import get_settings
from app.utils.response import success_response, ApiResponse
from app.schemas import PaginatedResponse
from app.utils.deps import get_token_payload_required
from app.services.generation_service import GenerationService, _process_urls, _process_url
from app.schemas.generation import (
    GenerationTaskCreate,
    GenerationTaskUpdate,
    GenerationTaskResponse,
    GenerationItemResponse,
    GenerationItemDetailResponse,
    GenerationTaskProgressLogResponse,
    BatchRetryRequest,
    BatchPauseRequest,
    ExecutionLogResponse,
    DebugRerunRequest,
    MaterialBrief,
    TemplateInfo,
    DebugGeneratePromptsRequest,
    DebugGeneratePromptsResponse,
    DebugGenerateTextRequest,
    DebugGenerateTextResponse,
    DebugGenerateImagesRequest,
    DebugGenerateImagesResponse,
    SubUserItemsListResponse,
)
from app.adapters.params import TextGenParams, ImageGenParams

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 生成任务管理
# ============================================
@router.get("/tasks", response_model=ApiResponse[PaginatedResponse[GenerationTaskResponse]])
async def list_generation_tasks(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（超级管理员使用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取生成任务列表
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选，创作管理员忽略该参数
    filter_operator_id = operator_id if is_super_admin and operator_id else None

    items, total = await GenerationService.list_generation_tasks(
        db,
        owner_operator_id=owner_operator_id,
        page=page,
        limit=limit,
        status=status,
        keyword=keyword,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        filter_operator_id=filter_operator_id,
    )

    # 实时聚合各状态计数（从 generation_item 表计算，确保待发布等数据准确）
    await GenerationService.attach_live_counts(db, items)

    # 手动构建响应，提取关联对象的名称
    response_items = []
    for task in items:
        # 计算任务总耗时
        end_time = task.completed_at if task.completed_at else datetime.utcnow()
        duration_seconds = int((end_time - task.created_at).total_seconds())
        # 优先使用实时聚合计数（_live_counts），回退到冗余字段
        _lc = getattr(task, '_live_counts', {})

        response_items.append(
            GenerationTaskResponse(
                id=task.id,
                name=task.name,
                material_id=task.material_id,
                benchmark_material_id=task.benchmark_material_id,
                model_platform=task.model_platform,
                model_id=task.model_id,
                image_model_platform=task.image_model_platform,
                image_model_id=task.image_model_id,
                model_selection_mode=task.model_selection_mode,
                max_concurrency=task.max_concurrency,
                variable_values_json=task.variable_values_json,
                dedup_rules_json=task.dedup_rules_json,
                status=task.status,
                total_count=_lc.get('total_count', task.total_count or 0),
                queued_count=_lc.get('queued_count', task.queued_count or 0),
                generating_count=_lc.get('generating_count', task.generating_count or 0),
                completed_count=_lc.get('completed_count', task.completed_count or 0),
                failed_count=_lc.get('failed_count', task.failed_count or 0),
                paused_count=_lc.get('paused_count', task.paused_count or 0),
                distributed_count=_lc.get('distributed_count', getattr(task, 'distributed_count', 0) or 0),
                pending_publish_count=_lc.get('pending_publish_count', task.pending_publish_count or 0),
                published_count=_lc.get('published_count', task.published_count or 0),
                created_by=task.created_by,
                owner_admin_id=task.owner_operator_id,
                owner_admin_name=task.owner_operator.nickname if task.owner_operator else None,
                created_at=task.created_at,
                updated_at=task.updated_at,
                duration_seconds=duration_seconds,
                # 去重配置（从数据库读取实际值）
                image_count=task.image_count,
                dedup_enabled=task.dedup_enabled,
                dedup_threshold=task.dedup_threshold,
                dedup_retry_count=task.dedup_retry_count,
                dedup_scope=task.dedup_scope,
                image_dedup_enabled=task.image_dedup_enabled,
                image_dedup_threshold=task.image_dedup_threshold,
                image_dedup_retry_count=task.image_dedup_retry_count,
                image_dedup_scope=task.image_dedup_scope,
                # 对标配置（从数据库读取实际值）
                benchmark_text_enabled=task.benchmark_text_enabled,
                benchmark_image_enabled=task.benchmark_image_enabled,
                benchmark_image_reference_options=task.benchmark_image_reference_options,
                benchmark_image_roles_json=task.benchmark_image_roles_json,
                template_product_mapping_json=task.template_product_mapping_json,
            )
        )

    return success_response(
        data=PaginatedResponse(
            items=response_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total > 0 else 0,
        ),
        message="获取成功"
    )


@router.post("/tasks", response_model=ApiResponse[GenerationTaskResponse])
async def create_generation_task(
    request: GenerationTaskCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建生成任务

    - 仅创作管理员可创建生成任务
    - 超级管理员不能创建任务（需要通过特定创作管理员创建）
    """
    import json
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建生成任务，请由创作管理员操作"
        )

    owner_operator_id = int(payload.get("sub"))
    created_by = owner_operator_id

    logger.info("[API] 开始创建生成任务 | owner=%s | name=%s | templates=%s | sub_users=%s",
                owner_operator_id, request.name, request.template_ids, request.sub_user_ids)
    logger.info("[API] 请求数据: %s", json.dumps(request.model_dump(), ensure_ascii=False))

    try:
        task = await GenerationService.create_generation_task(
            db,
            owner_operator_id=owner_operator_id,
            created_by=created_by,
            name=request.name,
            material_id=request.material_id,
            benchmark_material_id=request.benchmark_material_id,
            model_platform=request.model_platform,
            model_id=request.model_id,
            image_model_platform=request.image_model_platform,
            image_model_id=request.image_model_id,
            model_selection_mode=request.model_selection_mode,
            max_concurrency=request.max_concurrency,
            variable_values_json=request.variable_values_json,
            dedup_rules_json=request.dedup_rules_json,
            template_ids=request.template_ids,
            sub_user_ids=request.sub_user_ids,
            # 去重配置（若未显式设置且 scope 为空，则推断为关闭）
            image_count=request.image_count,
            dedup_enabled=request.dedup_enabled if request.dedup_enabled is not None else False,
            dedup_threshold=request.dedup_threshold,
            dedup_retry_count=request.dedup_retry_count,
            dedup_scope=request.dedup_scope,
            image_dedup_enabled=request.image_dedup_enabled if request.image_dedup_enabled is not None else False,
            image_dedup_threshold=request.image_dedup_threshold,
            image_dedup_retry_count=request.image_dedup_retry_count,
            image_dedup_scope=request.image_dedup_scope,
            # 对标配置
            benchmark_text_enabled=request.benchmark_text_enabled,
            benchmark_image_enabled=request.benchmark_image_enabled,
            benchmark_image_reference_options=request.benchmark_image_reference_options,
            # V3.0: 图片角色配置
            benchmark_image_roles=request.benchmark_image_roles_json,
            template_product_mapping=request.template_product_mapping_json,
        )
        logger.info("[API] GenerationService.create_generation_task 执行成功")
    except Exception as e:
        import traceback
        logger.error("[API] 创建任务时发生异常: %s\n%s", str(e), traceback.format_exc())
        raise

    logger.info("[API] 任务创建成功 | task_id=%s | owner=%s | total_items=%s | queued=%s",
                task.id, owner_operator_id, task.total_count, task.queued_count)

    # 自动触发 Celery 任务
    from app.tasks.generation_tasks import start_generation_task
    logger.info("[API] 分发 Celery 启动任务 | task_id=%s", task.id)
    start_generation_task.delay(task.id, owner_operator_id)
    logger.info("[API] Celery 启动任务已入队 | task_id=%s", task.id)

    # 手动构建响应（不访问关系属性）
    response_data = GenerationTaskResponse(
        id=task.id,
        name=task.name,
        material_id=task.material_id,
        benchmark_material_id=task.benchmark_material_id,
        model_platform=task.model_platform,
        model_id=task.model_id,
        image_model_platform=task.image_model_platform,
        image_model_id=task.image_model_id,
        model_selection_mode=task.model_selection_mode,
        max_concurrency=task.max_concurrency,
        variable_values_json=task.variable_values_json,
        dedup_rules_json=task.dedup_rules_json,
        status=task.status,
        total_count=task.total_count,
        queued_count=task.queued_count,
        generating_count=task.generating_count,
        completed_count=task.completed_count,
        failed_count=task.failed_count,
        paused_count=task.paused_count,
        distributed_count=task.distributed_count,
        pending_publish_count=task.pending_publish_count,
        published_count=task.published_count,
        created_by=task.created_by,
        owner_admin_id=task.owner_operator_id,
        owner_admin_name=None,  # 创建时暂不加载关系
        created_at=task.created_at,
        updated_at=task.updated_at,
        # 去重配置（从数据库读取实际值）
        image_count=task.image_count,
        dedup_enabled=task.dedup_enabled,
        dedup_threshold=task.dedup_threshold,
        dedup_retry_count=task.dedup_retry_count,
        dedup_scope=task.dedup_scope,
        image_dedup_enabled=task.image_dedup_enabled,
        image_dedup_threshold=task.image_dedup_threshold,
        image_dedup_retry_count=task.image_dedup_retry_count,
        image_dedup_scope=task.image_dedup_scope,
        # 对标配置（从数据库读取实际值）
        benchmark_text_enabled=task.benchmark_text_enabled,
        benchmark_image_enabled=task.benchmark_image_enabled,
        benchmark_image_reference_options=task.benchmark_image_reference_options,
        benchmark_image_roles_json=task.benchmark_image_roles_json,
        template_product_mapping_json=task.template_product_mapping_json,
    )

    return success_response(data=response_data, message="创建成功")


@router.get("/tasks/{id}", response_model=ApiResponse[GenerationTaskResponse])
async def get_generation_task(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取生成任务详情
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    task = await GenerationService.get_generation_task(
        db, id, owner_operator_id=owner_operator_id
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生成任务不存在"
        )

    # 实时聚合各状态计数（从 generation_item 表计算，确保待发布等数据准确）
    await GenerationService.attach_live_counts(db, [task])

    # 构建素材简要信息
    def build_material_brief(material) -> Optional[MaterialBrief]:
        if not material:
            return None
        thumbnails = []
        if material.attachments:
            for att in material.attachments:
                if att.thumbnail_url:
                    thumbnails.append(att.thumbnail_url)
                elif att.file_type == "image":
                    thumbnails.append(att.file_url)
        return MaterialBrief(
            id=material.id,
            title=material.title,
            content_type=material.content_type,
            content=getattr(material, 'content', None),
            topic=getattr(material, 'topic', None),
            thumbnails=thumbnails[:6] if thumbnails else None,
        )

    # 构建模板简要信息
    def build_template_info(template, attachments=None, platform_name=None,
                          seed_names=None, viral_type_label=None) -> Optional[TemplateInfo]:
        if not template:
            return None
        thumbnails = []
        if attachments:
            for att in attachments:
                if att.thumbnail_url:
                    thumbnails.append(att.thumbnail_url)
                elif att.file_type == "image":
                    thumbnails.append(att.file_url)
        seed_names = seed_names or {}
        return TemplateInfo(
            id=template.id,
            name=template.name,
            description=template.description,
            prompt_template=template.prompt_template,
            thumbnails=thumbnails[:6] if thumbnails else None,
            image_size_ratio=getattr(template, 'image_size_ratio', None),
            add_watermark=getattr(template, 'add_watermark', None),
            platform_name=platform_name,
            viral_type=getattr(template, 'viral_type', None),
            viral_type_label=viral_type_label,
            opening_seed_name=seed_names.get("opening"),
            emotion_seed_name=seed_names.get("emotion"),
            ending_seed_name=seed_names.get("ending"),
            product_selling_points=getattr(template, 'product_selling_points', None),
        )

    # 获取模板信息（从 task_templates 中获取第一个模板）
    template_id = None
    template_info = None
    if task.task_templates:
        # 按 sort_order 排序，取第一个模板
        sorted_templates = sorted(task.task_templates, key=lambda x: x.sort_order)
        if sorted_templates and sorted_templates[0].template:
            first_template = sorted_templates[0].template
            template_id = first_template.id
            # 加载模板附件
            from app.models import TemplateAttachment, TemplatePlatform, CreativeSeed, ViralType as ViralTypeModel
            from sqlalchemy import select
            attachments_result = await db.execute(
                select(TemplateAttachment).where(TemplateAttachment.template_id == first_template.id)
                .order_by(TemplateAttachment.sort_order.asc())
            )
            attachments = attachments_result.scalars().all()
            # 获取平台名称（避免 lazy load 触发 MissingGreenlet 错误）
            platform_name = None
            if first_template.platform_id:
                platform_result = await db.execute(
                    select(TemplatePlatform.name).where(TemplatePlatform.id == first_template.platform_id)
                )
                platform_name = platform_result.scalar_one_or_none()
            # 解析创意种子名称
            seed_names = {}
            for seed_type, seed_id in [
                ("opening", getattr(first_template, 'opening_seed_id', None)),
                ("emotion", getattr(first_template, 'emotion_seed_id', None)),
                ("ending", getattr(first_template, 'ending_seed_id', None)),
            ]:
                if seed_id and seed_id != 'auto':
                    try:
                        sid = int(seed_id)
                        seed_result = await db.execute(
                            select(CreativeSeed.name).where(CreativeSeed.id == sid)
                        )
                        seed_name = seed_result.scalar_one_or_none()
                        if seed_name:
                            seed_names[seed_type] = seed_name
                    except (ValueError, TypeError):
                        pass
                elif seed_id == 'auto':
                    seed_names[seed_type] = '随机选择'
            # 解析爆款类型名称
            viral_type_label = None
            viral_type_value = getattr(first_template, 'viral_type', None)
            if viral_type_value:
                if viral_type_value == 'auto':
                    viral_type_label = '随机选择'
                else:
                    vt_result = await db.execute(
                        select(ViralTypeModel.label).where(ViralTypeModel.value == viral_type_value)
                    )
                    vt_label = vt_result.scalar_one_or_none()
                    viral_type_label = vt_label or viral_type_value
            template_info = build_template_info(
                first_template, attachments, platform_name,
                seed_names=seed_names, viral_type_label=viral_type_label,
            )

    material_info = build_material_brief(task.material)
    benchmark_material_info = build_material_brief(task.benchmark_material)

    # 计算任务总耗时（秒）
    end_time = task.completed_at if task.completed_at else datetime.utcnow()
    duration_seconds = int((end_time - task.created_at).total_seconds())
    # 优先使用实时聚合计数（_live_counts），回退到冗余字段
    _lc = getattr(task, '_live_counts', {})

    response_data = GenerationTaskResponse(
        id=task.id,
        name=task.name,
        material_id=task.material_id,
        benchmark_material_id=task.benchmark_material_id,
        model_platform=task.model_platform,
        model_id=task.model_id,
        image_model_platform=task.image_model_platform,
        image_model_id=task.image_model_id,
        model_selection_mode=task.model_selection_mode,
        max_concurrency=task.max_concurrency,
        variable_values_json=task.variable_values_json,
        dedup_rules_json=task.dedup_rules_json,
        status=task.status,
        total_count=_lc.get('total_count', task.total_count or 0),
        queued_count=_lc.get('queued_count', task.queued_count or 0),
        generating_count=_lc.get('generating_count', task.generating_count or 0),
        completed_count=_lc.get('completed_count', task.completed_count or 0),
        failed_count=_lc.get('failed_count', task.failed_count or 0),
        paused_count=_lc.get('paused_count', task.paused_count or 0),
        distributed_count=_lc.get('distributed_count', getattr(task, 'distributed_count', 0) or 0),
        pending_publish_count=_lc.get('pending_publish_count', task.pending_publish_count or 0),
        published_count=_lc.get('published_count', task.published_count or 0),
        created_by=task.created_by,
        owner_admin_id=task.owner_operator_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        template_id=template_id,
        template_info=template_info,
        material_info=material_info,
        benchmark_material_info=benchmark_material_info,
        duration_seconds=duration_seconds,
        completed_at=task.completed_at,
        # 去重配置（从数据库读取实际值）
        image_count=task.image_count,
        dedup_enabled=task.dedup_enabled,
        dedup_threshold=task.dedup_threshold,
        dedup_retry_count=task.dedup_retry_count,
        dedup_scope=task.dedup_scope,
        image_dedup_enabled=task.image_dedup_enabled,
        image_dedup_threshold=task.image_dedup_threshold,
        image_dedup_retry_count=task.image_dedup_retry_count,
        image_dedup_scope=task.image_dedup_scope,
        # 对标配置（从数据库读取实际值）
        benchmark_text_enabled=task.benchmark_text_enabled,
        benchmark_image_enabled=task.benchmark_image_enabled,
        benchmark_image_reference_options=task.benchmark_image_reference_options,
        benchmark_image_roles_json=task.benchmark_image_roles_json,
        template_product_mapping_json=task.template_product_mapping_json,
    )

    return success_response(data=response_data, message="获取成功")


@router.post("/tasks/{id}/cancel", response_model=ApiResponse[GenerationTaskResponse])
async def cancel_generation_task(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    取消生成任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    try:
        task = await GenerationService.cancel_generation_task(
            db, task_id=id, owner_operator_id=owner_operator_id
        )
        # 计算任务总耗时
        end_time = task.completed_at if task.completed_at else datetime.utcnow()
        duration_seconds = int((end_time - task.created_at).total_seconds())

        # 手动构建响应（不访问关系属性）
        response_data = GenerationTaskResponse(
            id=task.id,
            name=task.name,
            material_id=task.material_id,
            benchmark_material_id=task.benchmark_material_id,
            model_platform=task.model_platform,
            model_id=task.model_id,
            model_selection_mode=task.model_selection_mode,
            max_concurrency=task.max_concurrency,
            variable_values_json=task.variable_values_json,
            dedup_rules_json=task.dedup_rules_json,
            status=task.status,
            total_count=task.total_count,
            queued_count=task.queued_count,
            generating_count=task.generating_count,
            completed_count=task.completed_count,
            failed_count=task.failed_count,
            paused_count=task.paused_count,
            distributed_count=task.distributed_count,
            pending_publish_count=task.pending_publish_count,
            published_count=task.published_count,
            created_by=task.created_by,
            owner_admin_id=task.owner_operator_id,
            owner_admin_name=None,  # 取消时暂不加载关系
            created_at=task.created_at,
            updated_at=task.updated_at,
            duration_seconds=duration_seconds,
        )
        return success_response(data=response_data, message="取消成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/tasks/{id}/recalculate", response_model=ApiResponse[GenerationTaskResponse])
async def recalculate_task_counts(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重新计算任务统计计数（修复因历史bug导致的计数错误）

    从实际的子任务状态重新统计，确保计数器与真实状态一致。
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[API] recalculate_task_counts | task_id=%s | owner=%s", id, owner_operator_id)

    try:
        task = await GenerationService.recalculate_task_counts(
            db, id, owner_operator_id=owner_operator_id
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        response_data = GenerationTaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            benchmark_material_id=task.benchmark_material_id,
            template_id=task.template_id,
            material_id=task.material_id,
            dedup_config_json=task.dedup_config_json,
            content_type=task.content_type,
            model_platform=task.model_platform,
            model_id=task.model_id,
            model_selection_mode=task.model_selection_mode,
            max_concurrency=task.max_concurrency,
            variable_values_json=task.variable_values_json,
            dedup_rules_json=task.dedup_rules_json,
            status=task.status,
            total_count=task.total_count,
            queued_count=task.queued_count,
            generating_count=task.generating_count,
            completed_count=task.completed_count,
            failed_count=task.failed_count,
            paused_count=task.paused_count,
            distributed_count=task.distributed_count,
            pending_publish_count=task.pending_publish_count,
            published_count=task.published_count,
            created_by=task.created_by,
            owner_admin_id=task.owner_operator_id,
            owner_admin_name=None,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        return success_response(data=response_data, message="计数已修复")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/tasks/{id}/progress-logs", response_model=ApiResponse[list[GenerationTaskProgressLogResponse]])
async def get_task_progress_logs(
    id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取任务进度日志
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logs = await GenerationService.get_task_progress_logs(
        db, id, owner_operator_id=owner_operator_id, limit=limit
    )
    return success_response(data=logs, message="获取成功")


@router.patch("/tasks/{id}", response_model=ApiResponse[GenerationTaskResponse])
async def update_generation_task(
    id: int,
    request: GenerationTaskUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新生成任务配置（模型、去重等）

    仅更新请求中提供的字段，未提供的字段保持不变。
    修改即自动保存。
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    try:
        task = await GenerationService.update_generation_task_fields(
            db, id, request, owner_operator_id=owner_operator_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # 刷新实时计数
    await GenerationService.attach_live_counts(db, [task])

    response_data = dict(
        id=task.id,
        name=task.name,
        material_id=task.material_id,
        benchmark_material_id=task.benchmark_material_id,
        model_platform=task.model_platform,
        model_id=task.model_id,
        image_model_platform=task.image_model_platform,
        image_model_id=task.image_model_id,
        model_selection_mode=task.model_selection_mode,
        status=task.status,
        total_count=task.total_count,
        queued_count=task.queued_count,
        generating_count=task.generating_count,
        completed_count=task.completed_count,
        failed_count=task.failed_count,
        paused_count=task.paused_count,
        distributed_count=task.distributed_count,
        pending_publish_count=task.pending_publish_count,
        published_count=task.published_count,
        dedup_enabled=task.dedup_enabled,
        dedup_threshold=task.dedup_threshold,
        dedup_retry_count=task.dedup_retry_count,
        image_dedup_enabled=task.image_dedup_enabled,
        image_dedup_threshold=task.image_dedup_threshold,
        image_dedup_retry_count=task.image_dedup_retry_count,
        max_concurrency=task.max_concurrency,
        created_at=task.created_at.isoformat() if task.created_at else None,
        updated_at=task.updated_at.isoformat() if task.updated_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )
    return success_response(data=response_data, message="更新成功")


# ============================================
# 生成子任务管理
# ============================================
@router.get("/tasks/{id}/items", response_model=ApiResponse[PaginatedResponse[GenerationItemResponse]])
async def list_generation_items(
    id: int,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    distribution_status: Optional[str] = Query(None, description="分发状态筛选"),
    sub_user_id: Optional[int] = Query(None, description="创作者筛选"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取生成任务的子任务列表
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] list_generation_items | task_id=%s | owner=%s | page=%s | limit=%s | "
                 "status_filter=%s | distribution_status=%s | sub_user_id=%s",
                 id, owner_operator_id, page, limit, status, distribution_status, sub_user_id)

    items, total = await GenerationService.list_generation_items(
        db,
        task_id=id,
        owner_operator_id=owner_operator_id,
        page=page,
        limit=limit,
        status=status,
        distribution_status=distribution_status,
        sub_user_id=sub_user_id,
    )

    # 统计各状态数量
    status_counts = {}
    for item in items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    logger.debug("[API] 子任务列表 | task_id=%s | total=%s | returned=%s | status_breakdown=%s",
                 id, total, len(items), status_counts)

    # 填充 sub_user_name
    for item in items:
        if item.sub_user:
            item.sub_user_name = item.sub_user.nickname or item.sub_user.display_name or str(item.sub_user_id)

    # 处理图片 URL
    settings = get_settings()
    prefer_url = settings.image_prefer_url
    for item in items:
        if item.generated_image_urls_json:
            item.generated_image_urls_json = _process_urls(item.generated_image_urls_json, prefer_url)
        if item.generated_image_thumbnails_json:
            item.generated_image_thumbnails_json = _process_urls(item.generated_image_thumbnails_json, prefer_url)
        if item.generated_video_url:
            item.generated_video_url = _process_url(item.generated_video_url, prefer_url)

    return success_response(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total > 0 else 0,
        ),
        message="获取成功"
    )


@router.get("/items/{id}", response_model=ApiResponse[GenerationItemResponse])
async def get_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取生成子任务详情
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    item = await GenerationService.get_generation_item(
        db, id, owner_operator_id=owner_operator_id
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生成子任务不存在"
        )

    # 处理图片 URL
    settings = get_settings()
    prefer_url = settings.image_prefer_url
    if item.generated_image_urls_json:
        item.generated_image_urls_json = _process_urls(item.generated_image_urls_json, prefer_url)
    if item.generated_image_thumbnails_json:
        item.generated_image_thumbnails_json = _process_urls(item.generated_image_thumbnails_json, prefer_url)
    if item.generated_video_url:
        item.generated_video_url = _process_url(item.generated_video_url, prefer_url)

    return success_response(data=item, message="获取成功")


@router.get("/items/{id}/detail", response_model=ApiResponse[GenerationItemDetailResponse])
async def get_generation_item_detail(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取生成子任务完整详情（含输入/输出内容）
    """
    from app.models import GenerationItemExecutionLog, GenerationTask, TemplateAttachment, MaterialAttachment

    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    item = await GenerationService.get_generation_item(
        db, id, owner_operator_id=owner_operator_id
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生成子任务不存在"
        )

    # 加载创作者名称
    sub_user_name = None
    if item.sub_user_id:
        from app.models import SubUser
        from sqlalchemy import select as sa_select
        from sqlalchemy.orm import selectinload
        su_result = await db.execute(
            sa_select(SubUser).where(SubUser.id == item.sub_user_id)
        )
        sub_user = su_result.scalar_one_or_none()
        if sub_user:
            sub_user_name = sub_user.nickname or sub_user.display_name or str(sub_user.id)

    # 加载模板附件图片
    template_images = []
    template_obj = None
    if item.template_id:
        # 加载模板对象
        from app.models import Template
        tpl_result = await db.execute(
            sa_select(Template).where(Template.id == item.template_id)
        )
        template_obj = tpl_result.scalar_one_or_none()
        
        # 加载模板附件
        att_result = await db.execute(
            sa_select(TemplateAttachment)
            .where(TemplateAttachment.template_id == item.template_id)
            .order_by(TemplateAttachment.sort_order.asc())
        )
        for att in att_result.scalars().all():
            if att.thumbnail_url:
                template_images.append(att.thumbnail_url)
            elif att.file_type == "image":
                template_images.append(att.file_url)

    # 加载素材对标信息
    benchmark_material = None
    benchmark_images = []
    if item.task_id:
        task_result = await db.execute(
            sa_select(GenerationTask).where(GenerationTask.id == item.task_id)
        )
        task = task_result.scalar_one_or_none()
        if task and task.benchmark_material_id:
            from app.models import Material
            mat_result = await db.execute(
                sa_select(Material).where(Material.id == task.benchmark_material_id)
            )
            benchmark_material = mat_result.scalar_one_or_none()
            if benchmark_material:
                mat_att_result = await db.execute(
                    sa_select(MaterialAttachment)
                    .where(MaterialAttachment.material_id == benchmark_material.id)
                    .order_by(MaterialAttachment.sort_order.asc())
                )
                for att in mat_att_result.scalars().all():
                    if att.thumbnail_url:
                        benchmark_images.append(att.thumbnail_url)
                    elif att.file_type == "image":
                        benchmark_images.append(att.file_url)

    # 构建水印布尔值
    watermark_val = item.input_watermark
    watermark_bool = bool(watermark_val) if watermark_val is not None else None
    
    # 加载创意种子名称
    opening_seed_name = None
    emotion_seed_name = None
    ending_seed_name = None
    if template_obj:
        from app.models import CreativeSeed
        # 开头模式
        if template_obj.opening_seed_id and template_obj.opening_seed_id != "auto":
            try:
                seed_id = int(template_obj.opening_seed_id)
                seed_result = await db.execute(
                    sa_select(CreativeSeed).where(CreativeSeed.id == seed_id)
                )
                seed = seed_result.scalar_one_or_none()
                if seed:
                    opening_seed_name = seed.name
            except (ValueError, TypeError):
                pass
        # 情感基调
        if template_obj.emotion_seed_id and template_obj.emotion_seed_id != "auto":
            try:
                seed_id = int(template_obj.emotion_seed_id)
                seed_result = await db.execute(
                    sa_select(CreativeSeed).where(CreativeSeed.id == seed_id)
                )
                seed = seed_result.scalar_one_or_none()
                if seed:
                    emotion_seed_name = seed.name
            except (ValueError, TypeError):
                pass
        # 结尾模式
        if template_obj.ending_seed_id and template_obj.ending_seed_id != "auto":
            try:
                seed_id = int(template_obj.ending_seed_id)
                seed_result = await db.execute(
                    sa_select(CreativeSeed).where(CreativeSeed.id == seed_id)
                )
                seed = seed_result.scalar_one_or_none()
                if seed:
                    ending_seed_name = seed.name
            except (ValueError, TypeError):
                pass

    settings = get_settings()
    prefer_url = settings.image_prefer_url

    response_data = GenerationItemDetailResponse(
        id=item.id,
        task_id=item.task_id,
        sub_user_id=item.sub_user_id,
        sub_user_name=sub_user_name,
        template_id=item.template_id,
        model_platform=item.model_platform,
        model_id=item.model_id,
        image_model_platform=item.image_model_platform,
        image_model_id=item.image_model_id,
        generated_title=item.generated_title,
        generated_text=item.generated_text,
        text_file_url=_process_url(item.text_file_url, prefer_url) if item.text_file_url else None,
        generated_image_urls_json=_process_urls(item.generated_image_urls_json, prefer_url) or [],
        generated_image_thumbnails_json=_process_urls(item.generated_image_thumbnails_json, prefer_url) or [],
        generated_video_url=_process_url(item.generated_video_url, prefer_url) if item.generated_video_url else None,
        output_topics=item.output_topics,
        status=item.status,
        retry_count=item.retry_count,
        error_message=item.error_message,
        distribution_status=item.distribution_status,
        queued_at=item.queued_at,
        started_at=item.started_at,
        completed_at=item.completed_at,
        distributed_at=item.distributed_at,
        confirmed_at=item.confirmed_at,
        input_prompt_creativity=item.input_prompt_creativity,
        input_prompt_instruction=item.input_prompt_instruction,
        input_template_images_json=_process_urls(template_images, prefer_url) if template_images else None,
        input_image_size_ratio=item.input_image_size_ratio,
        input_watermark=watermark_bool,
        input_template_name=template_obj.name if template_obj else None,
        input_viral_type=template_obj.viral_type if template_obj else None,
        input_product_selling_points=template_obj.product_selling_points if template_obj else None,
        input_opening_seed_name=opening_seed_name,
        input_emotion_seed_name=emotion_seed_name,
        input_ending_seed_name=ending_seed_name,
        input_benchmark_title=benchmark_material.title if benchmark_material else item.input_benchmark_title,
        input_benchmark_content=benchmark_material.content if benchmark_material else item.input_benchmark_content,
        input_benchmark_topic=benchmark_material.topic if benchmark_material else item.input_benchmark_topic,
        input_benchmark_images_json=_process_urls(benchmark_images, prefer_url) if benchmark_images else None,
        input_sub_user_profile=item.input_sub_user_profile,
        input_sub_user_positioning=item.input_sub_user_positioning,
        input_sub_user_style=item.input_sub_user_style,
        output_system_text_prompt=item.output_system_text_prompt,
        output_user_text_prompt=item.output_user_text_prompt,
        output_user_image_prompt=item.output_user_image_prompt,
        final_prompt=item.final_prompt,
        execution_started_at=item.execution_started_at,
        execution_ended_at=item.execution_ended_at,
        execution_result=item.execution_result,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )

    return success_response(data=response_data, message="获取成功")


@router.post("/items/{id}/retry", response_model=ApiResponse[GenerationItemResponse])
async def retry_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重试失败的生成子任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] retry_generation_item | item_id=%s | owner=%s", id, owner_operator_id)
    try:
        item = await GenerationService.retry_failed_item(
            db, item_id=id, owner_operator_id=owner_operator_id
        )
        logger.info("[API] 子任务重试成功 | item_id=%s | owner=%s | new_status=%s", id, owner_operator_id, item.status)

        # 分发 Celery 任务
        from app.tasks.generation_tasks import process_generation_item_phased
        process_generation_item_phased.delay(id, owner_operator_id)
        logger.info("[API] 重试 Celery 任务已分发 | item_id=%s", id)

        return success_response(data=item, message="重试成功")
    except Exception as e:
        logger.warning("[API] 子任务重试失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/{id}/regenerate", response_model=ApiResponse[GenerationItemResponse])
async def regenerate_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重新生成已完成的子任务（待发布状态）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] regenerate_generation_item | item_id=%s | owner=%s", id, owner_operator_id)
    try:
        item = await GenerationService.regenerate_completed_item(
            db, item_id=id, owner_operator_id=owner_operator_id
        )
        logger.info("[API] 子任务重新生成成功 | item_id=%s | owner=%s | new_status=%s", id, owner_operator_id, item.status)

        # 分发 Celery 任务
        from app.tasks.generation_tasks import process_generation_item_phased
        process_generation_item_phased.delay(id, owner_operator_id)
        logger.info("[API] 重新生成 Celery 任务已分发 | item_id=%s", id)

        return success_response(data=item, message="重新生成任务已提交")
    except Exception as e:
        logger.warning("[API] 子任务重新生成失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/batch-retry", response_model=ApiResponse[list[GenerationItemResponse]])
async def batch_retry_generation_items(
    request: BatchRetryRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量重试失败的生成子任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] batch_retry | item_ids=%s | task_id=%s | owner=%s",
                 request.item_ids, request.task_id, owner_operator_id)
    try:
        items = await GenerationService.batch_retry_items(
            db,
            item_ids=request.item_ids,
            task_id=request.task_id,
            owner_operator_id=owner_operator_id,
        )

        logger.info("[API] 批量重试成功 | owner=%s | count=%s", owner_operator_id, len(items))

        # 分发 Celery 任务
        from app.tasks.generation_tasks import process_generation_item_phased
        for item in items:
            process_generation_item_phased.delay(item.id, owner_operator_id)
            logger.debug("[API] 重试任务已分发 | item_id=%s", item.id)

        return success_response(data=items, message=f"成功重试 {len(items)} 个子任务")
    except Exception as e:
        logger.warning("[API] 批量重试失败 | owner=%s | error=%s", owner_operator_id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/{id}/pause", response_model=ApiResponse[GenerationItemResponse])
async def pause_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    暂停生成子任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] pause_generation_item | item_id=%s | owner=%s", id, owner_operator_id)
    try:
        item = await GenerationService.toggle_pause_item(
            db, item_id=id, owner_operator_id=owner_operator_id, pause=True
        )
        logger.info("[API] 子任务已暂停 | item_id=%s | owner=%s | new_status=%s", id, owner_operator_id, item.status)
        return success_response(data=item, message="暂停成功")
    except Exception as e:
        logger.warning("[API] 暂停子任务失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/{id}/resume", response_model=ApiResponse[GenerationItemResponse])
async def resume_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    继续生成子任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] resume_generation_item | item_id=%s | owner=%s", id, owner_operator_id)
    try:
        item = await GenerationService.toggle_pause_item(
            db, item_id=id, owner_operator_id=owner_operator_id, pause=False
        )
        logger.info("[API] 子任务已继续 | item_id=%s | owner=%s | new_status=%s", id, owner_operator_id, item.status)

        # 继续时重新分发 Celery 任务
        from app.tasks.generation_tasks import process_generation_item_phased
        process_generation_item_phased.delay(id, owner_operator_id)
        logger.info("[API] 继续 Celery 任务已分发 | item_id=%s", id)

        return success_response(data=item, message="继续成功")
    except Exception as e:
        logger.warning("[API] 继续子任务失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/batch-pause", response_model=ApiResponse[list[GenerationItemResponse]])
async def batch_pause_generation_items(
    request: BatchPauseRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量暂停/继续生成子任务
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    action = "暂停" if request.pause else "继续"
    logger.debug("[API] batch_pause | action=%s | item_ids=%s | owner=%s", action, request.item_ids, owner_operator_id)

    try:
        if not request.item_ids:
            raise ValueError("必须提供 item_ids")

        items = await GenerationService.batch_pause_items(
            db,
            item_ids=request.item_ids,
            pause=request.pause,
            owner_operator_id=owner_operator_id,
        )

        logger.info("[API] 批量%s | owner=%s | 请求=%s | 实际处理=%s", action, owner_operator_id, len(request.item_ids), len(items))

        # 继续时重新分发 Celery 任务
        if not request.pause:
            from app.tasks.generation_tasks import process_generation_item_phased
            for item in items:
                process_generation_item_phased.delay(item.id, owner_operator_id)
                logger.debug("[API] 继续任务已分发 | item_id=%s", item.id)

        return success_response(data=items, message=f"成功{action} {len(items)} 个子任务")
    except Exception as e:
        logger.warning("[API] 批量%s失败 | owner=%s | error=%s", action, owner_operator_id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================
# 执行日志管理
# ============================================
@router.get("/items/{id}/execution-logs", response_model=ApiResponse[list[ExecutionLogResponse]])
async def get_item_execution_logs(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取子任务的执行日志列表
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] get_item_execution_logs | item_id=%s | owner=%s", id, owner_operator_id)
    try:
        logs = await GenerationService.get_item_execution_logs(
            db, item_id=id, owner_operator_id=owner_operator_id
        )

        # 汇总各节点状态
        node_summary = {}
        response_logs = []
        for log in logs:
            node_summary[log.node_name] = log.node_status
            response_logs.append({
                "id": log.id,
                "item_id": log.item_id,
                "node_name": log.node_name,
                "node_status": log.node_status.value if hasattr(log.node_status, 'value') else log.node_status,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "error_data": log.error_data,
                "duration_ms": log.duration_ms,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "created_at": log.created_at,
            })

        logger.debug("[API] 执行日志列表 | item_id=%s | count=%s | nodes=%s", id, len(logs), node_summary)
        return success_response(data=response_logs, message="获取成功")
    except Exception as e:
        logger.warning("[API] 获取执行日志失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# 调试重跑
# ============================================
@router.post("/items/{id}/debug-rerun", response_model=ApiResponse[GenerationItemResponse])
async def debug_rerun_item(
    id: int,
    request: DebugRerunRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    调试重跑子任务

    支持覆盖提示词、模型平台和模型ID，重新执行指定子任务。
    """
    from app.tasks.generation_tasks import debug_rerun_generation_item

    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.debug("[API] debug_rerun_item | item_id=%s | owner=%s | prompt_override=%s | platform_override=%s | model_override=%s",
                 id, owner_operator_id,
                 (request.prompt_override[:50] + "...") if request.prompt_override else None,
                 request.model_platform_override, request.model_id_override)

    try:
        # 验证子任务存在
        item = await GenerationService.get_generation_item(db, id, owner_operator_id)
        if not item:
            logger.warning("[API] debug_rerun_item: 子任务不存在 | item_id=%s", id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生成子任务不存在"
            )

        logger.info("[API] debug_rerun_item: 重置子任务状态 | item_id=%s | old_status=%s", id, item.status)

        # 先设置覆盖参数（不触发状态机）
        if request.prompt_override:
            item.final_prompt = request.prompt_override
            logger.debug("[API] debug_rerun_item: 覆盖提示词 | item_id=%s | len=%s", id, len(request.prompt_override))
        if request.model_platform_override:
            item.model_platform = request.model_platform_override
            logger.debug("[API] debug_rerun_item: 覆盖平台 | item_id=%s | platform=%s", id, request.model_platform_override)
        if request.model_id_override:
            item.model_id = request.model_id_override
            logger.debug("[API] debug_rerun_item: 覆盖模型 | item_id=%s | model_id=%s", id, request.model_id_override)

        # 通过 update_generation_item_status 重置状态（正确更新任务统计计数）
        # update_generation_item_status 内部会 commit
        item = await GenerationService.update_generation_item_status(
            db, item_id=id, owner_operator_id=owner_operator_id, status="queued"
        )
        # debug 重跑视为全新尝试，重置错误信息和重试计数
        item.error_message = None
        item.retry_count = 0
        item.queued_at = datetime.utcnow()
        item.started_at = None
        item.completed_at = None
        await db.commit()
        await db.refresh(item)

        # 异步执行重跑
        logger.info("[API] debug_rerun_item: 分发 Celery 任务 | item_id=%s | owner=%s", id, owner_operator_id)
        debug_rerun_generation_item.delay(
            item_id=id,
            owner_operator_id=owner_operator_id,
            prompt_override=request.prompt_override,
            model_platform_override=request.model_platform_override,
            model_id_override=request.model_id_override,
        )

        return success_response(data=item, message="调试重跑已启动")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("[API] debug_rerun_item 失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================
# 调试模式 - 提示词/文案/图片生成
# ============================================

@router.post("/debug/generate-text", response_model=ApiResponse[DebugGenerateTextResponse])
async def debug_generate_text(
    request: DebugGenerateTextRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    调试模式：仅生成文案（不保存到数据库）
    """
    from app.adapters.factory import ModelAdapterFactory
    from app.adapters.config import get_model_config_manager
    from app.models import GenerationItem

    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[API] debug_generate_text | item_id=%s | owner=%s", request.item_id, owner_operator_id)

    try:
        # 获取子任务
        item = await GenerationService.get_generation_item(db, request.item_id, owner_operator_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生成子任务不存在"
            )

        # 确定使用的模型配置
        model_platform = request.model_platform_override or item.model_platform
        model_id = request.model_id_override or item.model_id

        # 获取系统提示词和用户提示词
        system_prompt = request.system_prompt_override or item.output_system_text_prompt or ""
        user_prompt = request.user_prompt_override or item.output_user_text_prompt or ""

        if not system_prompt or not user_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少提示词，请先生成提示词"
            )

        # 获取模型配置（强制刷新以确保拿到最新的认证配置）
        model_config_manager = get_model_config_manager()
        await model_config_manager.load_all_configs(db, force_refresh=True)

        if not model_platform or not model_id:
            # 自动选择模型
            result = await model_config_manager.get_default_config_with_platform(db, model_type="llm")
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有可用的文本模型"
                )
            config, platform = result
            model_platform = platform
            model_id = config.model_id
        else:
            # 使用指定模型 - 查找匹配的配置
            configs = await model_config_manager.get_configs_by_platform(db, model_platform)
            config = None
            for cfg in configs:
                if cfg.model_id == model_id:
                    config = cfg
                    break
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型配置不存在: {model_platform}/{model_id}"
                )
            platform = model_platform

        # 创建模型适配器并生成文案
        adapter = ModelAdapterFactory.create_adapter(platform, config)
        extra_params = config.extra_params or {}
        text_params = TextGenParams(
            model_id=config.model_id,
            max_tokens=extra_params.get("max_tokens", 32000),
            temperature=extra_params.get("temperature", 0.7),
            top_p=extra_params.get("top_p", 0.8),
            enable_thinking=(platform.lower() == "bailian") and extra_params.get("enable_thinking", True),
        )

        # 在调用之前完成变量替换
        variable_values = item.task.variable_values_json or {}
        formatted_user = adapter.format_prompt(user_prompt, variable_values)
        formatted_system = adapter.format_prompt(system_prompt, variable_values) if system_prompt else None

        result = await adapter.generate_text(
            user_prompt=formatted_user,
            system_prompt=formatted_system,
            params=text_params,
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "文案生成失败"
            )

        # 尝试解析结果 (期望是 JSON 格式，包含 title, content, topics)
        import json
        import re
        try:
            # 清理可能的 markdown 代码块标记
            text = result.text.strip()
            # 移除 ```json 和 ``` 标记
            if text.startswith("```"):
                # 匹配 ```json 或 ``` 开头
                text = re.sub(r'^```(?:json)?\s*\n?', '', text)
                # 移除结尾的 ```
                text = re.sub(r'\n?```\s*$', '', text)
                text = text.strip()

            parsed = json.loads(text)
            title = parsed.get("title", "")
            content = parsed.get("content", result.text)
            topics = parsed.get("topics", [])
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试按行解析
            lines = result.text.strip().split("\n")
            title = lines[0] if lines else ""
            content = "\n".join(lines[1:]) if len(lines) > 1 else result.text
            topics = []

        response = DebugGenerateTextResponse(
            title=title,
            content=content,
            topics=topics,
            image_prompts=parsed.get("image_prompts", [])
        )

        logger.info("[API] debug_generate_text 成功 | item_id=%s", request.item_id)
        return success_response(data=response, message="文案生成成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("[API] debug_generate_text 失败 | error=%s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/debug/generate-images", response_model=ApiResponse[DebugGenerateImagesResponse])
async def debug_generate_images(
    request: DebugGenerateImagesRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    调试模式：仅生成图片（不保存到数据库）
    """
    from app.adapters.factory import ModelAdapterFactory
    from app.adapters.config import get_model_config_manager
    from app.models import GenerationItem

    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    logger.info("[API] debug_generate_images | item_id=%s | owner=%s", request.item_id, owner_operator_id)

    try:
        # 获取子任务
        item = await GenerationService.get_generation_item(db, request.item_id, owner_operator_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生成子任务不存在"
            )

        # 确定使用的模型配置
        model_platform = request.model_platform_override or item.model_platform
        model_id = request.model_id_override or item.model_id

        # 获取用户提示词（生图模型不使用系统提示词，每条 image_prompt 自包含完整创作指导）
        user_prompts = request.user_prompts_override or item.aigc_user_image_prompts_json or []

        # 确定生成图片数量
        # 注意：如果 request.image_count_override 是 0，应该使用 len(user_prompts) 或 1
        if request.image_count_override is not None and request.image_count_override > 0:
            image_count = request.image_count_override
        else:
            image_count = len(user_prompts) if user_prompts else 1

        logger.info("[API] debug_generate_images | user_prompts count=%s | image_count=%s",
                   len(user_prompts), image_count)

        if not user_prompts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少图片用户提示词，请先生成提示词"
            )

        # 获取模型配置（强制刷新以确保拿到最新的认证配置）
        model_config_manager = get_model_config_manager()
        await model_config_manager.load_all_configs(db, force_refresh=True)

        if not model_platform or not model_id:
            # 自动选择模型
            result = await model_config_manager.get_default_config_with_platform(db, model_type="image")
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有可用的图片模型"
                )
            config, platform = result
            model_platform = platform
            model_id = config.model_id
        else:
            # 使用指定模型 - 查找匹配的配置
            configs = await model_config_manager.get_configs_by_platform(db, model_platform)
            config = None
            for cfg in configs:
                if cfg.model_id == model_id:
                    config = cfg
                    break
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"模型配置不存在: {model_platform}/{model_id}"
                )
            platform = model_platform

        # 创建模型适配器并生成图片
        adapter = ModelAdapterFactory.create_adapter(platform, config)

        # 诊断日志：输出认证相关信息（用于排查认证失败问题）
        logger.info("[API] debug_generate_images | 模型适配器已创建 | platform=%s | model_id=%s | api_key=%s | extra_params_keys=%s",
                   platform, config.model_id,
                   "present" if config.api_key else "MISSING",
                   list(config.extra_params.keys()) if config.extra_params else [])
        # 对可灵平台额外输出关键参数状态
        if platform == "kling":
            logger.info("[API] debug_generate_images | [Kling诊断] access_key_id=%s | access_key_secret=%s",
                       "present" if config.extra_params.get("access_key_id") else "MISSING",
                       "present" if config.extra_params.get("access_key_secret") else "MISSING")

        # 获取参考图片（区分对标图和产品图）
        # 注意：前端传入的是混合列表，后端需要从 item 中获取配置来区分
        task = None  # 初始化，避免 UnboundLocalError
        
        # 如果前端传入参考图片覆盖，优先使用前端的列表
        # 前端已经正确构造：先产品图，后对标图
        if request.reference_image_urls_override is not None:
            override_urls = request.reference_image_urls_override
            logger.info("[API] debug_generate_images | 使用前端传入的参考图片 | count=%s", len(override_urls))
            
            # 从 item 配置获取数量信息来分割
            # 注意：input_template_product_mapping_json 存储的是产品名称，不是图片数量
            # 需要从 input_template_images_json 获取实际的产品图数量
            n_product_config = len(item.input_template_images_json or [])
            n_benchmark_config = len(item.input_benchmark_images_json or [])
            
            # 如果没有产品图配置，尝试从模板附件加载
            if n_product_config == 0 and item.template_id:
                from app.models import TemplateAttachment
                att_result = await db.execute(
                    select(TemplateAttachment).where(TemplateAttachment.template_id == item.template_id)
                )
                attachments = att_result.scalars().all()
                n_product_config = sum(1 for a in attachments if a.file_type == "image")
            
            logger.info("[API] debug_generate_images | 配置数量 | product=%s | benchmark=%s", 
                       n_product_config, n_benchmark_config)
            
            # 分割列表：先产品图，后对标图
            if n_product_config > 0:
                product_urls = override_urls[:n_product_config]
                benchmark_urls = override_urls[n_product_config:]
            elif n_benchmark_config > 0:
                # 如果只有对标图配置，全部当作对标图
                benchmark_urls = override_urls
                product_urls = []
            else:
                # 没有配置信息，简单策略：前2张是产品图，其余是对标图
                n_product = min(2, len(override_urls))
                product_urls = override_urls[:n_product]
                benchmark_urls = override_urls[n_product:]
            
            logger.info("[API] debug_generate_images | 前端图片分割 | product=%s | benchmark=%s",
                       len(product_urls), len(benchmark_urls))
        else:
            # 从 item 配置获取对标图和产品图
            # 对标图（用于构图/场景/风格参考）
            benchmark_urls = []
            if item.input_benchmark_image_enabled and item.input_benchmark_images_json:
                benchmark_urls = item.input_benchmark_images_json
                logger.info("[API] debug_generate_images | 对标图 | count=%s", len(benchmark_urls))
            
            # 产品图（用于主体外观参考）- 从模板附件加载（与正式任务一致）
            product_urls = []
            if item.template_id:
                from app.models import Template
                from sqlalchemy.orm import selectinload
                template_query = select(Template).options(
                    selectinload(Template.attachments)
                ).where(Template.id == item.template_id)
                template_result = await db.execute(template_query)
                template = template_result.scalar_one_or_none()
                if template and template.attachments:
                    product_urls = [
                        att.file_url for att in template.attachments
                        if att.file_type == "image"
                    ]
                    logger.info("[API] debug_generate_images | 模板产品图已加载 | count=%s", len(product_urls))

        # 获取图片尺寸配置（优先用子任务级别，回退到任务级别）
        image_size_ratio = item.input_image_size_ratio
        # 将整数转换为布尔值（数据库存储为1/0，但API需要true/false）
        add_watermark = bool(item.input_watermark) if item.input_watermark is not None else True

        # 解析对标图角色配置（可能是 dict 或 list 格式）
        bench_roles_list = []
        if item.input_benchmark_image_roles_json:
            roles_data = item.input_benchmark_image_roles_json
            if isinstance(roles_data, dict):
                # 字典格式：键为 "benchmark_1", "benchmark_2" 等
                # 需要按索引顺序提取并转换为描述文本
                for i in range(len(benchmark_urls)):
                    # 尝试两种键格式：benchmark_N 和 数字索引
                    key1 = f"benchmark_{i + 1}"
                    key2 = str(i)
                    key3 = i
                    
                    role_tags = roles_data.get(key1) or roles_data.get(key2) or roles_data.get(key3, [])
                    
                    # 将角色标签转换为描述文本
                    if role_tags and isinstance(role_tags, list):
                        # 角色标签映射
                        role_map = {
                            "composition": "构图",
                            "scene": "场景",
                            "style": "风格"
                        }
                        descriptions = [role_map.get(tag, tag) for tag in role_tags]
                        if descriptions:
                            role_desc = "、".join(descriptions)
                            bench_roles_list.append({"description": role_desc})
                        else:
                            bench_roles_list.append({})
                    else:
                        bench_roles_list.append({})
                        
                logger.info("[API] debug_generate_images | 对标图角色配置 | count=%s | roles=%s",
                           len(bench_roles_list), [r.get("description", "") for r in bench_roles_list])
            elif isinstance(roles_data, list):
                bench_roles_list = roles_data

        # 处理参考图片：转换为 Base64（与正式任务一致）
        from app.services.storage_service import StorageService
        storage_service = StorageService()

        benchmark_b64_list = []
        for url in benchmark_urls:
            _, b64 = await storage_service.process_reference_image(
                url, prefer_url=False, max_size_bytes=4 * 1024 * 1024
            )
            if b64:
                benchmark_b64_list.append(b64)

        product_b64_list = []
        for url in product_urls:
            _, b64 = await storage_service.process_reference_image(
                url, prefer_url=False, max_size_bytes=4 * 1024 * 1024
            )
            if b64:
                product_b64_list.append(b64)

        logger.info("[API] debug_generate_images | 参考图转换完成 | benchmark=%s | product=%s",
                   len(benchmark_b64_list), len(product_b64_list))

        logger.info("[API] debug_generate_images | 图片尺寸配置 | size_ratio=%s | image_count=%s | benchmark=%s | product=%s",
                   image_size_ratio, image_count, len(benchmark_b64_list), len(product_b64_list))

        # =======================================================
        # 从这里开始：完全复制正式生成的参数处理逻辑
        # 参考：platform_api/app/services/generation_phases.py 的 _generate_images
        # =======================================================
        from app.adapters.params import SUPPORTED_RATIOS
        import random

        # 尺寸参数：只传比例，各适配器自行转换
        adapter_kwargs = {}
        if image_size_ratio and image_size_ratio in SUPPORTED_RATIOS:
            adapter_kwargs["size"] = image_size_ratio

        # 水印参数
        if platform_lower == "volcano":
            adapter_kwargs["watermark"] = add_watermark
        elif platform_lower == "bailian":
            adapter_kwargs["watermark"] = add_watermark
        elif platform_lower == "zhipu":
            adapter_kwargs["watermark_enabled"] = add_watermark
        elif platform_lower == "kling":
            adapter_kwargs["watermark_info"] = add_watermark

        # 传递 model_id 参数
        adapter_kwargs["model_id"] = config.model_id

        logger.info("[API] debug_generate_images | adapter_kwargs=%s", {
            k: v for k, v in adapter_kwargs.items()
            if k not in ["reference_image_urls"]
        })

        # ===== 生成每张图片（与正式任务一致：对标图循环取，产品图随机取）=====
        image_urls = []
        thumbnail_urls = []

        for idx, user_prompt in enumerate(user_prompts[:image_count]):
            # 构建参考图列表（与正式任务 generation_phases.py 一致）
            selected_refs = []
            n_benchmark = 0
            n_product = 0
            benchmark_role_text = ""

            # 对标图：按索引顺序循环取，每张生成图用一张不同的对标图
            if benchmark_b64_list:
                bench_idx = idx % len(benchmark_b64_list)
                selected_refs.append(benchmark_b64_list[bench_idx])
                n_benchmark = 1
                # 取对应对标图的角色要求
                if bench_idx < len(bench_roles_list) and bench_roles_list[bench_idx]:
                    role_info = bench_roles_list[bench_idx]
                    if isinstance(role_info, dict):
                        roledesc = role_info.get("description", "")
                    else:
                        roledesc = ""
                    if roledesc:
                        # 清理角色描述中的敏感词
                        roledesc = re.sub(r'(人物|角色|人像|人脸|肖像)', '主体', roledesc, flags=re.IGNORECASE)
                        benchmark_role_text = f"第1张（对标图）：请重点参考其{roledesc}，该图片主体产品不作为生成对象"

            # 产品图：随机取 2 张
            if product_b64_list:
                n_product = min(2, len(product_b64_list))
                if n_product > 1:
                    sampled = random.sample(product_b64_list, n_product)
                else:
                    sampled = [random.choice(product_b64_list)]
                selected_refs.extend(sampled)

            # 构建增强 prompt（从生图模型视角描述参考图用途）
            enhanced_prompt = user_prompt
            extra_parts = []
            if benchmark_role_text:
                extra_parts.append(f"【参考图说明】\n{benchmark_role_text}")
            if n_benchmark > 0 and n_product > 0:
                extra_parts.append("第2张、第3张为产品参考图，参考其主体外观，保持主体的轮廓、比例、样式、色彩、纹理、材质、细节等")
            if extra_parts:
                enhanced_prompt = f"{user_prompt}\n\n" + "\n".join(extra_parts)

            logger.info("[API] debug_generate_images | 生成图片 %d/%d | 对标图索引=%s | 产品图=%s张",
                       idx + 1, len(user_prompts[:image_count]),
                       (idx % len(benchmark_b64_list)) + 1 if benchmark_b64_list else 0,
                       n_product)

            # 设置参考图参数
            selected_refs = selected_refs if selected_refs else None

            logger.info("[API] debug_generate_images | 生成图片 %d/%d | has_refs=%s",
                       idx + 1, len(user_prompts[:image_count]),
                       bool(selected_refs))

            # 构建 ImageGenParams，从 config 读取配置
            extra_params = config.extra_params or {}
            image_params = ImageGenParams(
                model_id=config.model_id,
                count=1,
                ratio=image_size_ratio or "3:4",
                quality=extra_params.get("quality", "high"),
                watermark=add_watermark,
                reference_images=selected_refs,
            )

            # 调用图片生成
            try:
                result = await adapter.generate_image(
                    prompt=enhanced_prompt,
                    params=image_params,
                )
            except Exception as gen_error:
                logger.error("[API] debug_generate_images | 图片生成异常 | idx=%s | error=%s | error_type=%s",
                           idx, str(gen_error), type(gen_error).__name__)
                continue

            if result.success and result.image_urls:
                image_urls.extend(result.image_urls)
                # thumbnail_urls 属性可能不存在，使用 getattr 安全访问
                if hasattr(result, 'thumbnail_urls') and result.thumbnail_urls:
                    thumbnail_urls.extend(result.thumbnail_urls)
            elif not result.success:
                logger.warning("[API] debug_generate_images | 图片生成失败 | idx=%s | error=%s",
                             idx, result.error_message or "unknown error")

        response = DebugGenerateImagesResponse(
            image_urls=image_urls,
            reference_image_urls=benchmark_urls + product_urls if (benchmark_urls or product_urls) else None
        )

        logger.info("[API] debug_generate_images 成功 | item_id=%s | count=%s", request.item_id, len(image_urls))
        return success_response(data=response, message="图片生成成功")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("[API] debug_generate_images 失败 | error=%s | error_type=%s\n%s",
                    str(e), type(e).__name__, traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sub-user-items", response_model=ApiResponse[SubUserItemsListResponse])
async def get_sub_user_items(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    distribution_status: Optional[str] = Query(None, description="分发状态筛选（pending_publish/published）"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创作者获取自己的内容列表
    """
    user_type = payload.get("user_type")

    # 只有创作者可以调用这个接口
    if user_type != "sub_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创作者可以访问此接口"
        )

    sub_user_id = int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass

    logger.debug("[API] get_sub_user_items | sub_user=%s | page=%s | limit=%s | distribution_status=%s",
                 sub_user_id, page, limit, distribution_status)

    try:
        result = await GenerationService.get_sub_user_items(
            db,
            sub_user_id=sub_user_id,
            page=page,
            limit=limit,
            distribution_status=distribution_status,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        logger.info("[API] 获取创作者内容列表成功 | sub_user=%s | count=%s",
                    sub_user_id, len(result["items"]))
        return success_response(data=result)
    except Exception as e:
        logger.warning("[API] 获取创作者内容列表失败 | sub_user=%s | error=%s", sub_user_id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/items/{id}/publish", response_model=ApiResponse[GenerationItemResponse])
async def publish_generation_item(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创作者标记生成内容为已发布
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 创作者只能标记自己的内容
    sub_user_id = None
    if user_type == "sub_user":
        sub_user_id = int(payload.get("sub"))

    logger.debug("[API] publish_generation_item | item_id=%s | owner=%s | sub_user=%s",
                 id, owner_operator_id, sub_user_id)

    try:
        item = await GenerationService.publish_item(
            db,
            item_id=id,
            owner_operator_id=owner_operator_id,
            sub_user_id=sub_user_id
        )
        logger.info("[API] 子任务已标记为已发布 | item_id=%s | owner=%s", id, owner_operator_id)
        return success_response(data=item, message="发布成功")
    except Exception as e:
        logger.warning("[API] 标记发布失败 | item_id=%s | error=%s", id, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
