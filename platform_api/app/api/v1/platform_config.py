"""
平台配置 API 路由 (platform_config.py)

提供平台级别的配置选项，包括爆款类型、品类选项等。

Author: Claude Code
Date: 2026
"""

import json
from fastapi import APIRouter, Depends
from typing import Dict, List, Any
from sqlalchemy import select

from app.utils.response import success_response, ApiResponse
from app.utils.deps import get_token_payload_required
from app.api.v1.creative_seeds import SEED_TYPE_INFO, CATEGORY_OPTIONS
from app.core.database import AsyncSessionLocal
from app.models import ViralType

router = APIRouter()


# 图片尺寸比例选项
IMAGE_SIZE_RATIOS: List[Dict[str, str]] = [
    {"value": "1:1", "label": "正方形 1:1 (2048x2048)", "description": "适合封面、展示类"},
    {"value": "4:3", "label": "横版 4:3 (2304x1728)", "description": "适合美食、产品展示"},
    {"value": "16:9", "label": "宽屏 16:9 (2560x1440)", "description": "适合风景、场景展示"},
    {"value": "3:4", "label": "竖版 3:4 (1728x2304)", "description": "适合穿搭、人物"},
    {"value": "9:16", "label": "长竖版 9:16 (1440x2560)", "description": "适合手机竖屏、短视频封面"},
]

# 内容类型选项
CONTENT_TYPES: List[Dict[str, str]] = [
    {"value": "text", "label": "纯文本", "description": "仅生成文案内容"},
    {"value": "image_text", "label": "图文", "description": "生成图片和文案"},
    {"value": "video_text", "label": "视频", "description": "生成视频和文案"},
]


@router.get("/viral-types", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_viral_types(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取爆款类型选项列表（从数据库读取）

    返回所有可用的爆款类型配置，用于模板创建时的下拉选择。
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ViralType)
            .where(ViralType.status == 'enabled')
            .order_by(ViralType.sort_order)
        )
        viral_types = result.scalars().all()

        # 转换为 API 响应格式
        data = []
        for vt in viral_types:
            item = {
                "value": vt.value,
                "label": vt.label,
                "description": vt.description or "",
            }
            # 解析 keywords JSON
            if vt.keywords:
                try:
                    item["keywords"] = json.loads(vt.keywords)
                except json.JSONDecodeError:
                    item["keywords"] = []
            data.append(item)

        return success_response(data=data, message="获取成功")


@router.get("/creative-seeds/types", response_model=ApiResponse[Dict[str, Any]])
async def get_creative_seed_types(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取创意种子类型选项

    返回种子类型和品类选项，用于创意种子管理。
    """
    return success_response(
        data={
            "seed_types": SEED_TYPE_INFO,
            "categories": CATEGORY_OPTIONS,
        },
        message="获取成功"
    )


@router.get("/image-ratios", response_model=ApiResponse[List[Dict[str, str]]])
async def get_image_size_ratios(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取图片尺寸比例选项

    返回所有可用的图片尺寸比例，用于模板配置。
    """
    return success_response(
        data=IMAGE_SIZE_RATIOS,
        message="获取成功"
    )


@router.get("/content-types", response_model=ApiResponse[List[Dict[str, str]]])
async def get_content_types(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取内容类型选项

    返回所有可用的内容类型，用于模板配置。
    """
    return success_response(
        data=CONTENT_TYPES,
        message="获取成功"
    )


@router.get("/template-options", response_model=ApiResponse[Dict[str, Any]])
async def get_all_template_options(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取模板配置所需的全部选项（一次性获取）

    返回爆款类型、图片比例、内容类型、品类等所有选项，
    用于模板创建/编辑表单的初始化。
    """
    # 从数据库获取爆款类型
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ViralType)
            .where(ViralType.status == 'enabled')
            .order_by(ViralType.sort_order)
        )
        viral_types = result.scalars().all()

        # 转换为 API 响应格式
        viral_types_data = []
        for vt in viral_types:
            item = {
                "value": vt.value,
                "label": vt.label,
                "description": vt.description or "",
            }
            # 解析 keywords JSON
            if vt.keywords:
                try:
                    item["keywords"] = json.loads(vt.keywords)
                except json.JSONDecodeError:
                    item["keywords"] = []
            viral_types_data.append(item)

    return success_response(
        data={
            "viral_types": viral_types_data,
            "image_size_ratios": IMAGE_SIZE_RATIOS,
            "content_types": CONTENT_TYPES,
            "categories": CATEGORY_OPTIONS,
            "seed_types": SEED_TYPE_INFO,
        },
        message="获取成功"
    )