"""
AIGC趋势分析 API (trend_analysis.py)

提供趋势分析相关的 API 端点。

Author: Claude Code
Date: 2025
"""

import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.utils.deps import get_token_payload_required
from app.utils.response import success_response, ApiResponse
from app.schemas.trend_analysis import (
    TimeDimension,
    CompareType,
    ContentType,
    GenerationTrendResponse,
    DistributionTrendResponse,
    PublishTrendResponse,
    OperatorTrendResponse,
    TrendDataPoint,
    ComparisonData,
    OperatorTrendItem,
    TrendAnalysisFilterOptions,
)
from app.services.trend_analysis_service import TrendAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/generation", response_model=ApiResponse[GenerationTrendResponse])
async def get_generation_trend(
    start_date: Optional[str] = Query(None, description="统计开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="统计结束日期（YYYY-MM-DD）"),
    dimension: TimeDimension = Query(TimeDimension.DAY, description="时间维度：day/week/month"),
    compare_type: CompareType = Query(CompareType.NONE, description="对比类型：none/chain/year"),
    content_type: ContentType = Query(ContentType.ALL, description="内容类型：all/image_text/video"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（仅超级管理员）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取内容生成趋势

    - start_date: 统计开始日期（YYYY-MM-DD）
    - end_date: 统计结束日期（YYYY-MM-DD）
    - dimension: 时间维度 (day/week/month)
    - compare_type: 对比类型 (none/chain/year)
    - content_type: 内容类型 (all/image_text/video)
    - operator_id: 筛选创作管理员ID（仅超级管理员可用）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选
    filter_operator_id = operator_id if is_super_admin and operator_id else None

    logger.info("[TrendAnalysis API] get_generation_trend | user_type=%s | owner=%s | start=%s | end=%s | dim=%s | compare=%s",
                user_type, owner_operator_id, parsed_start_date, parsed_end_date, dimension, compare_type)

    result = await TrendAnalysisService.get_generation_trend(
        db=db,
        owner_admin_id=owner_operator_id,
        is_super_admin=is_super_admin,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        dimension=dimension.value,
        compare_type=compare_type.value,
        content_type=content_type.value,
        filter_operator_id=filter_operator_id
    )

    # 构建响应
    compare_data = None
    if result.get("compare"):
        compare_data = ComparisonData(**result["compare"])

    return success_response(
        data=GenerationTrendResponse(
            data=[TrendDataPoint(**item) for item in result["data"]],
            total=result["total"],
            avg_daily=result["avg_daily"],
            max_daily=result["max_daily"],
            compare=compare_data
        ),
        message="获取成功"
    )


@router.get("/distribution", response_model=ApiResponse[DistributionTrendResponse])
async def get_distribution_trend(
    start_date: Optional[str] = Query(None, description="统计开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="统计结束日期（YYYY-MM-DD）"),
    dimension: TimeDimension = Query(TimeDimension.DAY, description="时间维度：day/week/month"),
    compare_type: CompareType = Query(CompareType.NONE, description="对比类型：none/chain/year"),
    content_type: ContentType = Query(ContentType.ALL, description="内容类型：all/image_text/video"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（仅超级管理员）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取内容分发趋势

    - start_date: 统计开始日期（YYYY-MM-DD）
    - end_date: 统计结束日期（YYYY-MM-DD）
    - dimension: 时间维度 (day/week/month)
    - compare_type: 对比类型 (none/chain/year)
    - content_type: 内容类型 (all/image_text/video)
    - operator_id: 筛选创作管理员ID（仅超级管理员可用）
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选
    filter_operator_id = operator_id if is_super_admin and operator_id else None

    logger.info("[TrendAnalysis API] get_distribution_trend | user_type=%s | owner=%s | start=%s | end=%s | dim=%s | compare=%s",
                user_type, owner_operator_id, parsed_start_date, parsed_end_date, dimension, compare_type)

    result = await TrendAnalysisService.get_distribution_trend(
        db=db,
        owner_admin_id=owner_operator_id,
        is_super_admin=is_super_admin,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        dimension=dimension.value,
        compare_type=compare_type.value,
        content_type=content_type.value,
        filter_operator_id=filter_operator_id
    )

    # 构建响应
    distributed_compare = None
    published_compare = None
    if result.get("distributed_compare"):
        distributed_compare = ComparisonData(**result["distributed_compare"])
    if result.get("published_compare"):
        published_compare = ComparisonData(**result["published_compare"])

    return success_response(
        data=DistributionTrendResponse(
            data=[TrendDataPoint(**item) for item in result["data"]],
            total_distributed=result["total_distributed"],
            total_published=result["total_published"],
            distribution_rate=result["distribution_rate"],
            publish_rate=result["publish_rate"],
            distributed_compare=distributed_compare,
            published_compare=published_compare
        ),
        message="获取成功"
    )


@router.get("/publish", response_model=ApiResponse[PublishTrendResponse])
async def get_publish_trend(
    start_date: Optional[str] = Query(None, description="统计开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="统计结束日期（YYYY-MM-DD）"),
    dimension: TimeDimension = Query(TimeDimension.DAY, description="时间维度：day/week/month"),
    compare_type: CompareType = Query(CompareType.NONE, description="对比类型：none/chain/year"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（仅超级管理员）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取内容发布趋势（合并生成和发布趋势）

    - 管理员视角：按 owner_operator_id 统计生成和发布
    - 创作者视角：按 sub_user_id 统计接收和发布

    - start_date: 统计开始日期（YYYY-MM-DD）
    - end_date: 统计结束日期（YYYY-MM-DD）
    - dimension: 时间维度 (day/week/month)
    - compare_type: 对比类型 (none/chain/year)
    - operator_id: 筛选创作管理员ID（仅超级管理员可用）
    """
    user_type = payload.get("user_type")
    user_id = int(payload.get("sub"))

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选
    filter_operator_id = operator_id if user_type == "super_admin" and operator_id else None

    logger.info("[TrendAnalysis API] get_publish_trend | user_type=%s | user_id=%s | start=%s | end=%s | dim=%s | compare=%s",
                user_type, user_id, parsed_start_date, parsed_end_date, dimension, compare_type)

    result = await TrendAnalysisService.get_publish_trend(
        db=db,
        user_type=user_type,
        user_id=user_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        dimension=dimension.value,
        compare_type=compare_type.value,
        filter_operator_id=filter_operator_id
    )

    # 构建响应
    generated_compare = None
    published_compare = None
    if result.get("generated_compare"):
        generated_compare = ComparisonData(**result["generated_compare"])
    if result.get("published_compare"):
        published_compare = ComparisonData(**result["published_compare"])

    return success_response(
        data=PublishTrendResponse(
            data=[TrendDataPoint(**item) for item in result["data"]],
            total_generated=result["total_generated"],
            total_published=result["total_published"],
            success_rate=result["success_rate"],
            generated_compare=generated_compare,
            published_compare=published_compare
        ),
        message="获取成功"
    )


@router.get("/operators", response_model=ApiResponse[OperatorTrendResponse])
async def get_operator_trend(
    start_date: Optional[str] = Query(None, description="统计开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="统计结束日期（YYYY-MM-DD）"),
    operator_id: Optional[int] = Query(None, description="筛选创作管理员ID（仅超级管理员）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取各创作管理员的生成趋势（仅超级管理员可用）

    - start_date: 统计开始日期（YYYY-MM-DD）
    - end_date: 统计结束日期（YYYY-MM-DD）
    - operator_id: 筛选创作管理员ID
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if not is_super_admin:
        return success_response(data=OperatorTrendResponse(data=[]), message="获取成功")

    owner_operator_id = None

    # 解析日期参数
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    # 超级管理员可以使用 operator_id 筛选
    filter_operator_id = operator_id if operator_id else None

    logger.info("[TrendAnalysis API] get_operator_trend | owner=%s | start=%s | end=%s",
                owner_operator_id, parsed_start_date, parsed_end_date)

    result = await TrendAnalysisService.get_operator_trend(
        db=db,
        owner_admin_id=owner_operator_id,
        is_super_admin=is_super_admin,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        filter_operator_id=filter_operator_id
    )

    return success_response(
        data=OperatorTrendResponse(
            data=[OperatorTrendItem(**item) for item in result]
        ),
        message="获取成功"
    )


@router.get("/filter-options", response_model=ApiResponse[TrendAnalysisFilterOptions])
async def get_filter_options(
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取趋势分析筛选选项

    返回可用的创作管理员列表、内容类型选项、时间维度选项等
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if not is_super_admin:
        return success_response(
            data=TrendAnalysisFilterOptions(
                operators=[],
                content_types=[
                    {"value": "all", "label": "全部"},
                    {"value": "image_text", "label": "图文"},
                    {"value": "video", "label": "视频"}
                ],
                dimensions=[
                    {"value": "day", "label": "按天"},
                    {"value": "week", "label": "按周"},
                    {"value": "month", "label": "按月"}
                ]
            ),
            message="获取成功"
        )

    result = await TrendAnalysisService.get_filter_options(db)

    return success_response(
        data=TrendAnalysisFilterOptions(**result),
        message="获取成功"
    )