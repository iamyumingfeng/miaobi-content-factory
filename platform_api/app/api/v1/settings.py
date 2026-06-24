"""
系统设置 API 路由 (settings.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.config import get_model_config_manager
from app.core.config import get_settings
from app.core.database import get_async_db
from app.models import ModelConfig, UserDefaultModel
from app.schemas.settings import (ModelConfigCreate, ModelConfigResponse,
                                  ModelConfigUpdate, UserDefaultModelResponse,
                                  UserDefaultModelUpdate)
from app.utils.deps import get_token_payload_required
from app.utils.response import ApiResponse, success_response

router = APIRouter()


class PlatformModelTypesResponse(BaseModel):
    """平台模型类型配置响应"""

    platform_types: Dict[str, List[str]] = {}


@router.get("/model-configs", response_model=ApiResponse[list[ModelConfigResponse]])
async def list_model_configs(
    response: Response,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模型配置列表（超级管理员）
    """
    # 禁用浏览器缓存，确保始终返回最新数据
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    result = await db.execute(
        select(ModelConfig).order_by(ModelConfig.platform, ModelConfig.model_id)
    )
    configs = result.scalars().all()
    return success_response(data=configs, message="获取成功")


@router.get("/model-configs/{id}", response_model=ApiResponse[ModelConfigResponse])
async def get_model_config(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取单个模型配置
    """
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在"
        )
    return success_response(data=config, message="获取成功")


@router.post("/model-configs", response_model=ApiResponse[ModelConfigResponse])
async def create_model_config(
    request: ModelConfigCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建模型配置（超级管理员）
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可操作"
        )

    config = ModelConfig(
        platform=request.platform,
        model_id=request.model_id,
        model_name=request.model_name,
        model_type=request.model_type,
        base_url=request.base_url,
        api_endpoint=request.api_endpoint,
        is_default=request.is_default,
        max_concurrency=request.max_concurrency,
        config_json=request.config_json,
        status=request.status,
        is_system=False,
        created_by=user_id,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    # 刷新模型配置缓存
    config_manager = get_model_config_manager()
    await config_manager.load_all_configs(db, force_refresh=True)

    return success_response(data=config, message="创建成功")


@router.put("/model-configs/{id}", response_model=ApiResponse[ModelConfigResponse])
async def update_model_config(
    id: int,
    request: ModelConfigUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新模型配置（超级管理员）
    """
    user_type = payload.get("user_type")

    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可操作"
        )

    result = await db.execute(select(ModelConfig).where(ModelConfig.id == id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在"
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(config)

    # 刷新模型配置缓存
    config_manager = get_model_config_manager()
    await config_manager.load_all_configs(db, force_refresh=True)

    return success_response(data=config, message="更新成功")


@router.delete("/model-configs/{id}", response_model=ApiResponse[dict])
async def delete_model_config(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除模型配置（超级管理员）
    """
    user_type = payload.get("user_type")

    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可操作"
        )

    result = await db.execute(select(ModelConfig).where(ModelConfig.id == id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="模型配置不存在"
        )

    await db.delete(config)
    await db.commit()

    # 刷新模型配置缓存
    config_manager = get_model_config_manager()
    await config_manager.load_all_configs(db, force_refresh=True)

    return success_response(message="删除成功")


# ==================== 用户默认模型设置 ====================


@router.get(
    "/user-default-models", response_model=ApiResponse[UserDefaultModelResponse]
)
async def get_user_default_models(
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取当前用户的默认模型设置
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 只允许超级管理员和创作管理员设置默认模型
    if user_type not in ["super_admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅超级管理员和创作管理员可操作",
        )

    # 查询用户的设置
    result = await db.execute(
        select(UserDefaultModel).where(
            UserDefaultModel.user_id == user_id, UserDefaultModel.user_type == user_type
        )
    )
    user_settings = result.scalars().all()

    # 构建响应
    response = UserDefaultModelResponse(
        llm_model_config_id=None,
        image_model_config_id=None,
        video_model_config_id=None,
        embedding_model_config_id=None,
        updated_at=None,
    )

    # 找到最新的更新时间
    max_updated_at = None
    for setting in user_settings:
        if setting.model_type == "llm":
            response.llm_model_config_id = setting.model_config_id
        elif setting.model_type == "image":
            response.image_model_config_id = setting.model_config_id
        elif setting.model_type == "video":
            response.video_model_config_id = setting.model_config_id
        elif setting.model_type == "embedding":
            response.embedding_model_config_id = setting.model_config_id

        setting_updated_at = setting.updated_at
        if max_updated_at is None or setting_updated_at > max_updated_at:
            max_updated_at = setting_updated_at

    response.updated_at = max_updated_at

    return success_response(data=response, message="获取成功")


@router.put(
    "/user-default-models", response_model=ApiResponse[UserDefaultModelResponse]
)
async def update_user_default_models(
    request: UserDefaultModelUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新当前用户的默认模型设置
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 只允许超级管理员和创作管理员设置默认模型
    if user_type not in ["super_admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅超级管理员和创作管理员可操作",
        )

    # 需要更新的模型类型配置
    updates = [
        ("llm", request.llm_model_config_id),
        ("image", request.image_model_config_id),
        ("video", request.video_model_config_id),
        ("embedding", request.embedding_model_config_id),
    ]

    # 验证所有提供的 model_config_id 是否有效
    for model_type, model_config_id in updates:
        if model_config_id is not None:
            # 验证模型是否存在、类型匹配且状态为 active
            result = await db.execute(
                select(ModelConfig).where(
                    ModelConfig.id == model_config_id,
                    ModelConfig.model_type == model_type,
                    ModelConfig.status == "active",
                )
            )
            model_config = result.scalar_one_or_none()

            if not model_config:
                model_type_name_map = {
                    "llm": "文本",
                    "image": "图片",
                    "video": "视频",
                    "embedding": "Embedding",
                }
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的{model_type_name_map.get(model_type, model_type)}模型配置ID",
                )

    # 先一次性查询所有现有记录
    result = await db.execute(
        select(UserDefaultModel).where(
            UserDefaultModel.user_id == user_id,
            UserDefaultModel.user_type == user_type,
            UserDefaultModel.model_type.in_(["llm", "image", "video", "embedding"]),
        )
    )
    existing_records = {r.model_type: r for r in result.scalars().all()}

    for model_type, model_config_id in updates:
        if model_type in existing_records:
            # 更新现有记录
            existing = existing_records[model_type]
            existing.model_config_id = model_config_id
            existing.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            new_setting = UserDefaultModel(
                user_id=user_id,
                user_type=user_type,
                model_type=model_type,
                model_config_id=model_config_id,
            )
            db.add(new_setting)

    await db.commit()

    # 返回更新后的设置
    return await get_user_default_models(payload, db)


# ==================== 平台模型类型配置 ====================


@router.get(
    "/platform-model-types", response_model=ApiResponse[PlatformModelTypesResponse]
)
async def get_platform_model_types(
    payload: dict = Depends(get_token_payload_required),
):
    """
    获取平台模型类型配置

    根据 .env 中的配置返回各平台支持的模型类型。
    只有配置了的模型类型才会在设置页面显示对应的分类。
    """
    settings = get_settings()
    platform_types = settings.get_all_platform_model_types()

    return success_response(
        data=PlatformModelTypesResponse(platform_types=platform_types),
        message="获取成功",
    )
