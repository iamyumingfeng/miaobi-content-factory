"""
素材管理 API 路由 (materials.py)

Author: Claude Code
Date: 2025
"""

import io
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_async_db
from app.utils.response import success_response, ApiResponse
from app.schemas import PaginatedResponse
from app.utils.deps import get_token_payload_required
from app.services.material_service import MaterialService
from app.services.storage_service import get_storage_service, StorageService
from app.schemas.materials import (
    MaterialCategoryCreate,
    MaterialCategoryUpdate,
    MaterialCategoryResponse,
    MaterialTagCreate,
    MaterialTagUpdate,
    MaterialTagResponse,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialCopyRequest,
    MaterialAttachmentCreate,
    MaterialAttachmentResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# 批量操作请求模型
# ============================================
class BatchDeleteRequest(BaseModel):
    material_ids: List[int]


class BatchStatusRequest(BaseModel):
    material_ids: List[int]
    status: str  # "available" or "disabled"


class BatchCopyRequest(BaseModel):
    material_ids: List[int]
    new_titles: Optional[dict] = None  # {"1": "新标题1", "2": "新标题2"}
    target_operator_id: Optional[int] = None  # 超级管理员用：复制到指定管理员名下
    target_platform_id: int  # 目标平台
    target_category_id: int  # 目标分类
    target_tag_ids: List[int]  # 复制后设置的目标标签（必填）


class TransferRequest(BaseModel):
    target_operator_id: int


class BatchTransferRequest(BaseModel):
    material_ids: List[int]
    target_operator_id: int


class MigrateTagRequest(BaseModel):
    target_tag_id: int


class BatchMigrateRequest(BaseModel):
    material_ids: List[int]
    target_tag_id: int
    source_tag_id: Optional[int] = None


class BatchTransferRequest(BaseModel):
    """批量素材迁移请求（超级管理员专用）"""
    material_ids: List[int]
    target_operator_id: int
    target_platform_id: int  # 目标平台
    target_category_id: int  # 目标分类
    target_tag_ids: List[int]  # 目标标签（必填）


# ============================================
# 素材分类管理（3级结构：平台 -> 分类 -> 标签）
# ============================================
@router.get("/categories", response_model=ApiResponse[list])
async def list_material_categories(
    platform_id: Optional[int] = Query(None, description="平台ID筛选"),
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材分类列表

    - 超级管理员：可查看所有分类，或通过owner_operator_id筛选
    - 创作管理员：只能查看自己的分类
    """
    from app.services.material_service import MaterialService
    
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    categories = await MaterialService.list_material_categories(
        db, owner_operator_id=filter_owner_id, platform_id=platform_id
    )
    
    # 加载统计信息
    result = []
    for cat in categories:
        tag_count = await MaterialService.count_tags_by_category(db, cat.id)
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color": cat.color,
            "platform_id": cat.material_platform_id,
            "sort_order": cat.sort_order,
            "tag_count": tag_count,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
        })
    
    return success_response(data=result, message="获取成功")


@router.post("/categories", response_model=ApiResponse[dict])
async def create_material_category(
    request: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建素材分类

    - 仅创作管理员可创建分类
    """
    from app.services.material_service import MaterialService
    
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建分类，请由创作管理员操作"
        )
    
    current_user_id = int(payload.get("sub"))
    
    category = await MaterialService.create_material_category(
        db,
        name=request["name"],
        material_platform_id=request["platform_id"],
        owner_operator_id=current_user_id,
        created_by=current_user_id,
        description=request.get("description"),
        color=request.get("color"),
        sort_order=request.get("sort_order", 0),
    )
    
    return success_response(data={
        "id": category.id,
        "name": category.name,
        "platform_id": category.material_platform_id,
    }, message="创建成功")


@router.put("/categories/{id}", response_model=ApiResponse[dict])
async def update_material_category(
    id: int,
    request: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新素材分类
    """
    from app.services.material_service import MaterialService
    
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    
    category = await MaterialService.update_material_category(
        db,
        category_id=id,
        owner_operator_id=None if is_super_admin else current_user_id,
        **{k: v for k, v in request.items() if v is not None}
    )
    
    return success_response(data={
        "id": category.id,
        "name": category.name,
    }, message="更新成功")


@router.delete("/categories/{id}")
async def delete_material_category(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除素材分类（同时删除分类下的所有标签）
    """
    from app.services.material_service import MaterialService
    
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    
    await MaterialService.delete_material_category(
        db, id, None if is_super_admin else current_user_id
    )
    return success_response(message="删除成功")


@router.get("/categories/{id}/stats", response_model=ApiResponse[dict])
async def get_material_category_stats(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材分类统计信息（素材数量、标签数量）
    """
    from app.services.material_service import MaterialService
    
    stats = await MaterialService.get_category_stats(db, id)
    return success_response(data=stats, message="获取成功")


# ============================================
# 素材标签管理（更新为3级结构）
# ============================================
@router.get("/tags", response_model=ApiResponse[list[MaterialTagResponse]])
async def list_material_tags(
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用）"),
    category_id: Optional[int] = Query(None, description="分类ID，传具体ID查询该分类下的标签"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材标签列表（3级结构）

    - 超级管理员：可查看所有标签，或通过owner_operator_id筛选特定管理员的标签
    - 创作管理员：只能查看自己的标签
    - 3级结构：category_id 查询该分类下的标签
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    tags = await MaterialService.list_material_tags(
        db, owner_operator_id=filter_owner_id, category_id=category_id
    )
    return success_response(data=tags, message="获取成功")


@router.get("/tag-summary")
async def get_material_tag_summary(
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取标签统计摘要

    返回：
    - total: 素材总数
    - no_tag_count: 无标签素材数量
    - tag_counts: { tag_id: count } 各标签素材数量
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    summary = await MaterialService.get_tag_summary(db, owner_operator_id=filter_owner_id)
    return success_response(data=summary, message="获取成功")


@router.post("/tags", response_model=ApiResponse[MaterialTagResponse])
async def create_material_tag(
    request: MaterialTagCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建素材标签

    - 创作管理员：可创建自己的素材标签
    - 超级管理员：可创建标签并指定所属创作管理员
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能新增平台或标签，请由创作管理员操作"
        )
    
    owner_operator_id = current_user_id
    created_by = current_user_id

    tag = await MaterialService.create_material_tag(
        db,
        name=request.name,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
        description=request.description,
        color=request.color,
        category_id=request.category_id,
    )
    return success_response(data=tag, message="创建成功")


@router.put("/tags/{id}", response_model=ApiResponse[MaterialTagResponse])
async def update_material_tag(
    id: int,
    request: MaterialTagUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新素材标签

    - 超级管理员：可更新所有标签
    - 创作管理员：只能更新自己的标签
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    try:
        tag = await MaterialService.update_material_tag(
            db,
            tag_id=id,
            owner_operator_id=None if is_super_admin else current_user_id,
            is_super_admin=is_super_admin,
            **request.model_dump(exclude_unset=True),
        )
        return success_response(data=tag, message="更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/tags/{id}")
async def delete_material_tag(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除素材标签

    - 超级管理员：可删除所有标签
    - 创作管理员：只能删除自己的标签
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    try:
        await MaterialService.delete_material_tag(db, id, None if is_super_admin else current_user_id, is_super_admin=is_super_admin)
        return success_response(data=None, message="删除成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/tags/{id}/stats")
async def get_material_tag_stats(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取标签统计信息

    - 返回标签下的素材数量
    - 超级管理员：可查看所有标签统计
    - 创作管理员：只能查看自己标签的统计
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 验证标签权限
    tag = await MaterialService.get_material_tag(
        db, id, None if is_super_admin else current_user_id
    )
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在"
        )

    material_count = await MaterialService.count_materials_by_tag(db, id)
    material_ids = await MaterialService.get_material_ids_by_tag(db, id)

    return success_response(
        data={
            "tag_id": id,
            "tag_name": tag.name,
            "material_count": material_count,
            "material_ids": material_ids,
        },
        message="获取成功"
    )


@router.post("/tags/{id}/migrate")
async def migrate_tag_materials(
    id: int,
    request: MigrateTagRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    迁移标签下的所有素材到目标标签

    - 超级管理员：可迁移任何标签的素材
    - 创作管理员：只能迁移自己标签的素材到目标标签
    - 目标标签必须与源标签属于同一管理员
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 获取源标签
    source_tag = await MaterialService.get_material_tag(
        db, id, None if is_super_admin else current_user_id
    )
    if not source_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源标签不存在"
        )

    # 获取目标标签
    target_tag = await MaterialService.get_material_tag(
        db, request.target_tag_id, None if is_super_admin else current_user_id
    )
    if not target_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标标签不存在"
        )

    # 检查是否属于同一管理员（超级管理员除外）
    if not is_super_admin and source_tag.owner_operator_id != target_tag.owner_operator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能迁移到同一管理员的其他标签"
        )

    # 执行迁移
    migrated_count = await MaterialService.migrate_tag_materials(db, id, request.target_tag_id)

    return success_response(
        data={
            "source_tag_id": id,
            "target_tag_id": request.target_tag_id,
            "migrated_count": migrated_count,
        },
        message=f"成功迁移 {migrated_count} 个素材"
    )


@router.post("/batch-migrate-tags")
async def batch_migrate_materials(
    request: BatchMigrateRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量迁移素材到目标标签

    - 超级管理员：可迁移任何素材到任何标签
    - 创作管理员：只能将自己的素材迁移到目标标签
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if not request.material_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要迁移的素材"
        )

    # 获取目标标签
    target_tag = await MaterialService.get_material_tag(
        db, request.target_tag_id, None if is_super_admin else current_user_id
    )
    if not target_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标标签不存在"
        )

    # 验证素材权限（非超级管理员需要验证）
    if not is_super_admin:
        for material_id in request.material_ids:
            material = await MaterialService.get_material(db, material_id, current_user_id)
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"素材 {material_id} 不存在或无权限操作"
                )

    # 执行批量迁移
    migrated_count = await MaterialService.batch_migrate_materials(
        db,
        material_ids=request.material_ids,
        target_tag_id=request.target_tag_id,
        source_tag_id=request.source_tag_id,
    )

    return success_response(
        data={
            "target_tag_id": request.target_tag_id,
            "migrated_count": migrated_count,
        },
        message=f"成功迁移 {migrated_count} 个素材"
    )


@router.post("/batch-transfer")
async def batch_transfer_materials(
    request: BatchTransferRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量迁移素材到目标管理员（超级管理员专用）

    将选中的素材完整迁移（含图片附件）到指定目标管理员，并设置新标签。
    迁移后原素材将被删除。

    限制：
    - 仅超级管理员可调用
    - 单次最多迁移 100 个素材
    """
    user_type = payload.get("user_type")

    # 权限校验：仅超级管理员可用
    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅超级管理员可使用此功能"
        )

    # 参数校验
    if not request.material_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要迁移的素材"
        )

    if len(request.material_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次最多迁移 100 个素材"
        )

    # target_tag_ids 为空列表时表示无标签，不强制要求

    # 执行批量迁移
    result = await MaterialService.batch_transfer_materials(
        db,
        material_ids=request.material_ids,
        target_operator_id=request.target_operator_id,
        target_tag_ids=request.target_tag_ids,
    )

    return success_response(
        data=result,
        message=f"成功迁移 {result['success_count']} 个素材，失败 {result['failed_count']} 个"
    )


# ============================================
# 素材管理
# ============================================
def build_tag_response(tag):
    """构建标签响应数据（统一复用）"""
    tag_dict = {
        "id": tag.id,
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "category_id": tag.category_id,
        "is_system": tag.is_system,
        "created_by": tag.created_by,
        "created_at": tag.created_at,
        "updated_at": tag.updated_at,
    }
    if tag.category:
        tag_dict["category"] = {
            "id": tag.category.id,
            "name": tag.category.name,
            "description": tag.category.description,
            "color": tag.category.color,
            "material_platform_id": tag.category.material_platform_id,
            "created_at": tag.category.created_at,
            "updated_at": tag.category.updated_at,
        }
    return tag_dict


def build_material_response(item, attachments, tags, is_favorite):
    """构建素材响应数据"""
    # 构建分类和平台信息
    category = None
    platform = None

    logger.debug(f"[build_material_response] item id={item.id}, tags count={len(tags) if tags else 0}")

    # 从标签中获取分类和平台信息
    if tags and len(tags) > 0:
        first_tag = tags[0]
        logger.debug(f"[build_material_response] first_tag: id={first_tag.id}, name={first_tag.name}")
        logger.debug(f"[build_material_response] first_tag.category: {first_tag.category}")
        if hasattr(first_tag, 'category') and first_tag.category:
            cat = first_tag.category
            category = {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "platform_id": cat.material_platform_id,
            }
            logger.debug(f"[build_material_response] category built: {category}")
            if hasattr(cat, 'platform') and cat.platform:
                plat = cat.platform
                platform = {
                    "id": plat.id,
                    "name": plat.name,
                    "description": plat.description,
                    "color": plat.color,
                }
                logger.debug(f"[build_material_response] platform built: {platform}")

    # 转换标签为字典格式
    tag_dicts = [build_tag_response(tag) for tag in tags]

    response = {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "topic": item.topic,
        "library_type": item.library_type,
        "text_content": item.text_content,
        "source_url": item.source_url,
        "source_type": item.source_type,
        "content_type": item.content_type,
        "status": item.status,
        "image_count": item.image_count,
        "video_count": item.video_count,
        "created_by": item.created_by,
        "owner_admin_id": item.owner_operator_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "attachments": attachments,
        "tags": tag_dicts,
        "category": category,
        "platform": platform,
        "is_favorite": is_favorite,
    }
    logger.debug(f"[build_material_response] Final response for item {item.id}:")
    logger.debug(f"  - platform: {response.get('platform')}")
    logger.debug(f"  - category: {response.get('category')}")
    logger.debug(f"  - tags count: {len(response.get('tags', []))}")
    return response


@router.get("", response_model=ApiResponse[PaginatedResponse[MaterialResponse]])
async def list_materials(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    library_type: Optional[str] = Query(None, description="素材库类型：creation/benchmark"),
    tag_id: Optional[int] = Query(None, description="标签筛选"),
    no_tag: Optional[bool] = Query(None, description="仅显示无标签的素材"),
    category_id: Optional[int] = Query(None, description="分类筛选"),
    platform_id: Optional[int] = Query(None, description="平台筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_favorite: Optional[bool] = Query(None, description="是否仅收藏"),
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用，传null表示超级管理员自己的素材）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材列表

    - 超级管理员：可查看所有素材，或通过owner_operator_id筛选特定管理员的素材
    - 创作管理员：只能查看自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 权限控制：超级管理员可查看所有或筛选，创作管理员只能查看自己的
    if user_type == "super_admin":
        # 注意：owner_operator_id=None 表示查看超级管理员"自己"的素材（这种情况很少，因为超级管理员不创建素材）
        # owner_operator_id 不传或传某个值表示查看特定创作管理员的素材
        filter_owner_id = owner_operator_id
        # 超级管理员查看收藏时需要指定具体的创作管理员
        if is_favorite is not None and filter_owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="超级管理员查看收藏素材时请指定 owner_operator_id"
            )
    else:
        filter_owner_id = current_user_id

    # 只有当明确要筛选收藏时才设置favorite_user_id
    favorite_user_id = filter_owner_id if is_favorite is not None else None

    items, total = await MaterialService.list_materials(
        db,
        owner_operator_id=filter_owner_id,
        page=page,
        limit=limit,
        status=status,
        content_type=content_type,
        library_type=library_type,
        tag_id=tag_id,
        no_tag=no_tag,
        category_id=category_id,
        platform_id=platform_id,
        keyword=keyword,
        is_favorite=is_favorite,
        favorite_user_id=favorite_user_id,
    )

    # 加载关联数据
    response_items = []
    for item in items:
        # 使用已加载的附件（通过 selectinload）
        attachments = item.attachments or []
        logger.debug(f"[MaterialList] Item id={item.id}: attachments_count={len(attachments)}, "
                    f"image_count={item.image_count}, "
                    f"attachment_urls={[a.file_url for a in attachments[:3]]}")
        # 加载标签
        tags = await MaterialService.get_material_tags(db, item.id, item.owner_operator_id)
        # 检查收藏状态 - 只有当明确筛选收藏时才检查，避免超级管理员查看其他管理员素材时报错
        item_is_favorite = False
        if is_favorite is not None and favorite_user_id:
            favorite = await MaterialService.get_favorite(db, item.id, favorite_user_id)
            item_is_favorite = favorite is not None

        # 构建响应
        response_items.append(build_material_response(item, attachments, tags, item_is_favorite))

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


@router.post("", response_model=ApiResponse[MaterialResponse])
async def create_material(
    request: MaterialCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建素材

    - 创作管理员：可创建素材
    - 超级管理员：不可创建素材
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能上传素材，请由创作管理员操作"
        )
    
    owner_operator_id = current_user_id
    created_by = current_user_id
    user_id = current_user_id

    material = await MaterialService.create_material(
        db,
        title=request.title,
        content=request.content,
        topic=request.topic,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
        text_content=request.text_content,
        source_url=request.source_url,
        source_type=request.source_type,
        content_type=request.content_type,
        tag_ids=request.tag_ids,
    )

    # 加载关联数据并构建响应
    attachments = await MaterialService.list_material_attachments(db, material.id, material.owner_operator_id)
    tags = await MaterialService.get_material_tags(db, material.id, material.owner_operator_id)
    is_favorite = False
    favorite = await MaterialService.get_favorite(db, material.id, user_id)
    is_favorite = favorite is not None

    response_data = build_material_response(material, attachments, tags, is_favorite)

    return success_response(data=response_data, message="创建成功")


@router.post("/upload", response_model=ApiResponse[MaterialResponse])
async def upload_material(
    title: str = Form(..., description="素材标题"),
    content: str = Form(..., description="素材内容"),
    topic: str = Form(..., description="素材话题"),
    text_content: Optional[str] = Form(default=None, description="文本内容"),
    source_url: Optional[str] = Form(default=None, description="来源URL"),
    source_type: str = Form(default="upload", description="来源类型"),
    content_type: str = Form(default="image_text", description="内容类型"),
    tag_ids: Optional[str] = Form(default=None, description="标签ID列表（逗号分隔）"),
    files: Optional[List[UploadFile]] = File(default=None, description="图片文件列表（最多5张）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    上传素材（支持文件上传）

    - 使用 multipart/form-data 格式
    - 支持同时上传多张图片（最多5张）
    - 自动保存原图并生成缩略图
    - 创作管理员：可创建素材
    - 超级管理员：不可创建素材
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))

    logger.info(f"[MaterialUpload] Starting upload: user_type={user_type}, current_user_id={current_user_id}, "
                f"title={title}, files_count={len(files) if files else 0}")

    if user_type == "super_admin":
        logger.warning(f"[MaterialUpload] Super admin attempted upload: user_id={current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能上传素材，请由创作管理员操作"
        )

    owner_operator_id = current_user_id
    created_by = current_user_id

    # 解析标签ID
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()]
            logger.debug(f"[MaterialUpload] Parsed tag_ids: {parsed_tag_ids}")
        except ValueError:
            logger.warning(f"[MaterialUpload] Invalid tag_ids format: {tag_ids}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="标签ID格式不正确"
            )

    # 验证文件数量
    if files and len(files) > 5:
        logger.warning(f"[MaterialUpload] Too many files: {len(files)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多上传5张图片"
        )

    # 验证文件类型和大小
    if files:
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        max_size = 5 * 1024 * 1024  # 5MB
        for idx, file in enumerate(files):
            if file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                logger.debug(f"[MaterialUpload] File {idx}: filename={file.filename}, ext={ext}, "
                            f"content_type={file.content_type}")
                if ext not in allowed_extensions:
                    logger.warning(f"[MaterialUpload] Unsupported file format: {ext}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的文件格式: {ext}，仅支持 jpg/jpeg/png/gif/webp"
                    )

    # 创建素材
    material = await MaterialService.create_material(
        db,
        title=title,
        content=content,
        topic=topic,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
        text_content=text_content,
        source_url=source_url,
        source_type=source_type,
        content_type=content_type,
        tag_ids=parsed_tag_ids,
    )
    logger.info(f"[MaterialUpload] Created material: id={material.id}, owner_operator_id={owner_operator_id}")

    # 处理文件上传
    if files and material.id:
        storage = get_storage_service()

        saved_count = 0
        failed_count = 0

        for idx, file in enumerate(files):
            try:
                file_content = await file.read()

                if not file_content:
                    logger.warning(f"[MaterialUpload] File {idx} is empty, skipping: filename={file.filename}")
                    continue

                logger.info(f"[MaterialUpload] Processing file {idx}: filename={file.filename}, "
                           f"size={len(file_content)} bytes")

                # 获取文件扩展名
                ext = "jpg"
                if file.filename and '.' in file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()

                # 保存原图并生成缩略图
                original_url, thumbnail_url = await storage.save_material_image_with_thumbnail(
                    file_content=file_content,
                    owner_admin_id=owner_operator_id,
                    material_id=material.id,
                    extension=ext,
                )

                logger.info(f"[MaterialUpload] Storage result for file {idx}: "
                           f"original_url={original_url}, thumbnail_url={thumbnail_url}")

                # 保存附件记录
                if original_url:
                    # 获取图片尺寸
                    width, height = None, None
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(file_content))
                        width, height = img.size
                    except Exception:
                        pass

                    attachment = await MaterialService.add_material_attachment(
                        db,
                        material_id=material.id,
                        owner_operator_id=owner_operator_id,
                        file_type="image",
                        file_url=original_url,
                        file_name=file.filename or f"image_{idx + 1}.{ext}",
                        file_size=len(file_content),
                        sort_order=idx,
                        width=width,
                        height=height,
                        thumbnail_url=thumbnail_url,
                    )
                    logger.info(f"[MaterialUpload] Saved attachment: id={attachment.id if attachment else 'None'}, "
                               f"file_url={original_url}, file_size={len(file_content)}, "
                               f"width={width}, height={height}, thumbnail_url={thumbnail_url}")
                    saved_count += 1
                else:
                    logger.error(f"[MaterialUpload] Failed to save file {idx}: "
                               f"storage returned (None, None), filename={file.filename}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"[MaterialUpload] Exception processing file {idx}: {e}", exc_info=True)
                failed_count += 1

        logger.info(f"[MaterialUpload] File processing complete: saved={saved_count}, failed={failed_count}")

        # 更新素材的图片计数
        image_count = saved_count
        if image_count > 0:
            await MaterialService.update_material(
                db, material.id, owner_operator_id, image_count=image_count
            )
            logger.info(f"[MaterialUpload] Updated material image_count={image_count} for material_id={material.id}")

    # 加载关联数据并构建响应
    attachments = await MaterialService.list_material_attachments(db, material.id, material.owner_operator_id)
    tags = await MaterialService.get_material_tags(db, material.id, material.owner_operator_id)
    is_favorite = False
    favorite = await MaterialService.get_favorite(db, material.id, current_user_id)
    is_favorite = favorite is not None

    logger.info(f"[MaterialUpload] Loaded for response: material_id={material.id}, "
                f"attachments_count={len(attachments)}, tags_count={len(tags)}, is_favorite={is_favorite}")

    response_data = build_material_response(material, attachments, tags, is_favorite)

    # 记录响应中的图片信息
    response_attachments = response_data.get("attachments", []) if isinstance(response_data, dict) else getattr(response_data, "attachments", [])
    if response_attachments:
        for idx, att in enumerate(response_attachments):
            att_file_url = att.get("file_url") if isinstance(att, dict) else getattr(att, "file_url", None)
            att_thumb_url = att.get("thumbnail_url") if isinstance(att, dict) else getattr(att, "thumbnail_url", None)
            att_type = att.get("file_type") if isinstance(att, dict) else getattr(att, "file_type", None)
            logger.info(f"[MaterialUpload] Response attachment {idx}: file_url={att_file_url}, "
                       f"thumbnail_url={att_thumb_url}, file_type={att_type}")
    else:
        logger.warning(f"[MaterialUpload] Response has no attachments: material_id={material.id}")

    logger.info(f"[MaterialUpload] Upload completed successfully: material_id={material.id}")

    if failed_count > 0:
        return success_response(data=response_data, message=f"创建成功，但有 {failed_count} 个文件上传失败（可能是文件大小超限）")
    return success_response(data=response_data, message="创建成功")


@router.put("/batch-status")
async def batch_update_material_status(
    request: BatchStatusRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量更新素材状态

    - 超级管理员：可更新任何素材状态
    - 创作管理员：只能更新自己的素材状态
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    success_count = 0
    failed_ids = []

    for material_id in request.material_ids:
        try:
            await MaterialService.update_material(
                db,
                material_id=material_id,
                owner_operator_id=None if is_super_admin else current_user_id,
                status=request.status
            )
            success_count += 1
        except Exception:
            failed_ids.append(material_id)

    if failed_ids:
        return success_response(
            data={"success_count": success_count, "failed_ids": failed_ids},
            message=f"批量状态更新完成，成功 {success_count} 条，失败 {len(failed_ids)} 条"
        )

    return success_response(
        data={"success_count": success_count, "failed_ids": []},
        message=f"成功更新 {success_count} 条素材状态"
    )


@router.delete("/batch")
async def batch_delete_materials(
    request: BatchDeleteRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量删除素材

    - 超级管理员：可删除任何素材
    - 创作管理员：只能删除自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    success_count = 0
    failed_ids = []

    for material_id in request.material_ids:
        try:
            await MaterialService.delete_material(
                db, material_id=material_id,
                owner_operator_id=None if is_super_admin else current_user_id
            )
            success_count += 1
        except Exception:
            failed_ids.append(material_id)

    if failed_ids:
        return success_response(
            data={"success_count": success_count, "failed_ids": failed_ids},
            message=f"批量删除完成，成功 {success_count} 条，失败 {len(failed_ids)} 条"
        )

    return success_response(
        data={"success_count": success_count, "failed_ids": []},
        message=f"成功删除 {success_count} 条素材"
    )


# ============================================
# 素材平台管理（独立平台表）
# ============================================

@router.post("/platforms", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_material_platform(
    data: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建素材平台

    - 仅创作管理员可创建平台
    - 超级管理员不能创建平台
    """
    from app.services.material_platform_service import MaterialPlatformService

    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建平台，请由创作管理员操作"
        )

    current_user_id = int(payload.get("sub"))
    service = MaterialPlatformService(db)
    platform = await service.create_platform(
        name=data.get("name"),
        owner_operator_id=current_user_id,
        created_by=current_user_id,
        description=data.get("description"),
        color=data.get("color"),
        sort_order=data.get("sort_order", 0)
    )

    return success_response(data={
        "id": platform.id,
        "name": platform.name,
        "description": platform.description,
        "color": platform.color,
        "sort_order": platform.sort_order,
        "created_by": platform.created_by,
        "owner_operator_id": platform.owner_operator_id,
        "created_at": platform.created_at,
        "updated_at": platform.updated_at,
        "category_count": 0,
    }, message="创建成功")


@router.get("/platforms", response_model=ApiResponse[list])
async def list_material_platforms(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材平台列表

    - 超级管理员：可查看所有平台
    - 创作管理员：只能查看自己的平台
    """
    from app.services.material_platform_service import MaterialPlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    service = MaterialPlatformService(db)
    platforms = await service.get_platforms(
        owner_operator_id=filter_owner_id,
        keyword=keyword
    )

    result = []
    for p in platforms:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "color": p.color,
            "sort_order": p.sort_order,
            "created_by": p.created_by,
            "owner_operator_id": p.owner_operator_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "category_count": len(p.categories),
        })
    return success_response(data=result, message="获取成功")


@router.get("/platforms/tree", response_model=ApiResponse[dict])
async def get_material_platform_tree(
    owner_operator_id: Optional[int] = Query(None, description="指定创作管理员ID（仅超级管理员可用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材平台分类标签树形结构

    返回完整的平台-分类-标签层级结构，用于左侧导航栏展示。
    """
    from app.services.material_platform_service import MaterialPlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    service = MaterialPlatformService(db)
    tree = await service.get_platform_tree(
        owner_operator_id=filter_owner_id,
    )
    return success_response(data=tree, message="获取成功")


@router.get("/platforms/{platform_id}", response_model=ApiResponse[dict])
async def get_material_platform(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """获取素材平台详情"""
    from app.services.material_platform_service import MaterialPlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = MaterialPlatformService(db)
    platform = await service.get_platform(
        platform_id, None if is_super_admin else current_user_id
    )
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="平台不存在"
        )

    return success_response(data={
        "id": platform.id,
        "name": platform.name,
        "description": platform.description,
        "color": platform.color,
        "sort_order": platform.sort_order,
        "created_by": platform.created_by,
        "owner_operator_id": platform.owner_operator_id,
        "created_at": platform.created_at,
        "updated_at": platform.updated_at,
        "category_count": len(platform.categories),
    }, message="获取成功")


@router.get("/platforms/{platform_id}/stats", response_model=ApiResponse[dict])
async def get_material_platform_stats(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材平台统计信息（素材数量、分类数量、标签数量）
    """
    from app.services.material_platform_service import MaterialPlatformService
    from app.models import MaterialTagRel, MaterialTag, MaterialCategory

    service = MaterialPlatformService(db)
    platform = await service.get_platform(platform_id)
    if not platform:
        raise HTTPException(status=status.HTTP_404_NOT_FOUND, detail="平台不存在")

    # 统计分类数量
    category_count = len(platform.categories)

    # 统计标签数量
    tag_count = sum(len(cat.tags) for cat in platform.categories)

    # 统计素材数量
    if platform.categories:
        category_ids = [cat.id for cat in platform.categories]
        material_count = await db.scalar(
            select(func.count(func.distinct(MaterialTagRel.material_id)))
            .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
            .where(MaterialTag.category_id.in_(category_ids))
        ) or 0
    else:
        material_count = 0

    return success_response(data={
        "platform_id": platform_id,
        "material_count": material_count,
        "category_count": category_count,
        "tag_count": tag_count,
    }, message="获取成功")


@router.put("/platforms/{platform_id}", response_model=ApiResponse[dict])
async def update_material_platform(
    platform_id: int,
    data: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """更新素材平台"""
    from app.services.material_platform_service import MaterialPlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = MaterialPlatformService(db)
    try:
        platform = await service.update_platform(
            platform_id=platform_id,
            owner_operator_id=None if is_super_admin else current_user_id,
            **data
        )
        return success_response(data={
            "id": platform.id,
            "name": platform.name,
            "description": platform.description,
            "color": platform.color,
            "sort_order": platform.sort_order,
            "created_by": platform.created_by,
            "owner_operator_id": platform.owner_operator_id,
            "created_at": platform.created_at,
            "updated_at": platform.updated_at,
            "category_count": len(platform.categories),
        }, message="更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/platforms/{platform_id}")
async def delete_material_platform(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """删除素材平台（级联删除关联的分类和标签）"""
    from app.services.material_platform_service import MaterialPlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = MaterialPlatformService(db)
    try:
        await service.delete_platform(platform_id, None if is_super_admin else current_user_id)
        return success_response(message="删除成功")
    except Exception as e:
        error_msg = str(e)
        if "存在" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )


@router.get("/{id}", response_model=ApiResponse[MaterialResponse])
async def get_material(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材详情

    - 超级管理员：可查看所有素材
    - 创作管理员：只能查看自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    user_id = current_user_id

    material = await MaterialService.get_material(
        db, id, owner_operator_id=None if is_super_admin else current_user_id
    )
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="素材不存在"
        )

    # 加载关联数据
    attachments = await MaterialService.list_material_attachments(db, id, material.owner_operator_id)
    tags = await MaterialService.get_material_tags(db, id, material.owner_operator_id)
    is_favorite = False
    favorite = await MaterialService.get_favorite(db, id, user_id)
    is_favorite = favorite is not None

    # 构建响应
    response_data = build_material_response(material, attachments, tags, is_favorite)

    return success_response(data=response_data, message="获取成功")


@router.put("/{id}", response_model=ApiResponse[MaterialResponse])
async def update_material(
    id: int,
    request: MaterialUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新素材

    - 超级管理员：可更新所有素材
    - 创作管理员：只能更新自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    user_id = current_user_id
    try:
        material = await MaterialService.update_material(
            db,
            material_id=id,
            owner_operator_id=None if is_super_admin else current_user_id,
            **request.model_dump(exclude_unset=True),
        )

        # 加载关联数据并构建响应
        attachments = await MaterialService.list_material_attachments(db, material.id, material.owner_operator_id)
        tags = await MaterialService.get_material_tags(db, material.id, material.owner_operator_id)
        is_favorite = False
        favorite = await MaterialService.get_favorite(db, material.id, user_id)
        is_favorite = favorite is not None

        response_data = build_material_response(material, attachments, tags, is_favorite)

        return success_response(data=response_data, message="更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{id}")
async def delete_material(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除素材

    - 超级管理员：可删除所有素材
    - 创作管理员：只能删除自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    try:
        await MaterialService.delete_material(
            db, material_id=id, owner_operator_id=None if is_super_admin else current_user_id
        )
        return success_response(message="删除成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{id}/copy", response_model=ApiResponse[MaterialResponse])
async def copy_material(
    id: int,
    request: MaterialCopyRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    复制素材

    - 创作管理员：可复制自己的素材，复制到自己名下
    - 超级管理员：可复制任何素材，支持复制给任何管理员
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    is_super_admin = user_type == "super_admin"
    user_id = current_user_id

    try:
        # 确定目标管理员ID
        if is_super_admin and request.target_operator_id:
            # 超级管理员可以复制给其他管理员
            target_operator_id = request.target_operator_id
        else:
            # 创作管理员复制到自己名下
            target_operator_id = current_user_id

        # 超级管理员可以复制任何素材，创作管理员只能复制自己的
        material = await MaterialService.copy_material(
            db,
            material_id=id,
            owner_operator_id=target_operator_id,
            new_title=request.new_title,
            tag_ids=request.tag_ids,
        )

        # 加载关联数据并构建响应
        attachments = await MaterialService.list_material_attachments(db, material.id, material.owner_operator_id)
        tags = await MaterialService.get_material_tags(db, material.id, material.owner_operator_id)
        is_favorite = False
        favorite = await MaterialService.get_favorite(db, material.id, user_id)
        is_favorite = favorite is not None

        response_data = build_material_response(material, attachments, tags, is_favorite)

        return success_response(data=response_data, message="复制成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/batch-copy")
async def batch_copy_materials(
    request: BatchCopyRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    批量复制素材

    - 超级管理员：可复制任何素材，可指定目标管理员
    - 创作管理员：可复制自己的素材
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 目标管理员：超级管理员可指定，创作管理员使用自己
    target_operator_id = request.target_operator_id if is_super_admin else current_user_id

    success_count = 0
    failed_ids = []
    new_materials = []

    for material_id in request.material_ids:
        try:
            # 获取新标题（如果提供）
            new_title = None
            if request.new_titles and str(material_id) in request.new_titles:
                new_title = request.new_titles[str(material_id)]

            material = await MaterialService.copy_material(
                db,
                material_id=material_id,
                owner_operator_id=target_operator_id,
                new_title=new_title,
                tag_ids=request.target_tag_ids
            )
            success_count += 1
            new_materials.append(material.id)
        except Exception:
            failed_ids.append(material_id)

    if failed_ids:
        return success_response(
            data={"success_count": success_count, "failed_ids": failed_ids, "new_material_ids": new_materials},
            message=f"批量复制完成，成功 {success_count} 条，失败 {len(failed_ids)} 条"
        )

    return success_response(
        data={"success_count": success_count, "failed_ids": [], "new_material_ids": new_materials},
        message=f"成功复制 {success_count} 条素材"
    )


# ============================================
# 素材转移 API
# ============================================
@router.post("/{id}/transfer")
async def transfer_material(
    id: int,
    request: TransferRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    转移素材给其他创作管理员

    - 仅超级管理员可转移素材
    """
    user_type = payload.get("user_type")
    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅超级管理员可转移素材"
        )
    
    try:
        material = await MaterialService.update_material(
            db,
            material_id=id,
            owner_operator_id=None,  # 超级管理员可以更新任何素材
            owner_operator_id_new=request.target_operator_id
        )
        
        return success_response(
            data={"material_id": material.id, "new_owner_id": request.target_operator_id},
            message="素材转移成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# 素材附件管理
# ============================================
@router.get("/{id}/attachments", response_model=ApiResponse[list[MaterialAttachmentResponse]])
async def list_material_attachments(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取素材附件列表

    - 超级管理员：可查看所有素材的附件
    - 创作管理员：只能查看自己素材的附件
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 先获取素材确认权限
    material = await MaterialService.get_material(
        db, id, owner_operator_id=None if is_super_admin else current_user_id
    )
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="素材不存在"
        )

    attachments = await MaterialService.list_material_attachments(
        db, id, owner_operator_id=material.owner_operator_id
    )
    return success_response(data=attachments, message="获取成功")


@router.post("/{id}/attachments", response_model=ApiResponse[MaterialAttachmentResponse])
async def add_material_attachment(
    id: int,
    request: MaterialAttachmentCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    添加素材附件

    - 超级管理员：不可添加附件（仅可查看和转移）
    - 创作管理员：只能为自己素材添加附件
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    is_super_admin = user_type == "super_admin"
    
    # 超级管理员不能上传素材附件
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能添加素材附件，请由创作管理员操作"
        )
    
    try:
        # 创作管理员只能为自己的素材添加附件
        owner_operator_id = current_user_id
        
        attachment = await MaterialService.add_material_attachment(
            db,
            material_id=id,
            owner_operator_id=owner_operator_id,
            file_type=request.file_type,
            file_url=request.file_url,
            file_name=request.file_name,
            file_size=request.file_size,
            sort_order=request.sort_order,
            width=request.width,
            height=request.height,
            duration=request.duration,
            thumbnail_url=request.thumbnail_url,
        )
        return success_response(data=attachment, message="添加成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{id}/update-with-attachments", response_model=ApiResponse[MaterialResponse])
async def update_material_with_attachments(
    id: int,
    title: Optional[str] = Form(default=None, description="素材标题"),
    content: Optional[str] = Form(default=None, description="素材内容"),
    topic: Optional[str] = Form(default=None, description="素材话题"),
    content_type: Optional[str] = Form(default=None, description="内容类型"),
    text_content: Optional[str] = Form(default=None, description="文本内容"),
    tag_ids: Optional[str] = Form(default=None, description="标签ID列表（逗号分隔）"),
    platform_id: Optional[int] = Form(default=None, description="所属平台ID"),
    category_id: Optional[int] = Form(default=None, description="所属分类ID"),
    source_url: Optional[str] = Form(default=None, description="来源URL"),
    delete_attachment_ids: Optional[str] = Form(default=None, description="要删除的附件ID列表（逗号分隔）"),
    files: Optional[List[UploadFile]] = File(default=None, description="新文件列表（图片或视频，最多5个）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新素材并管理附件

    - 使用 multipart/form-data 格式
    - 支持删除指定附件
    - 支持添加新附件
    - 支持同时更新素材基本信息
    """
    import io
    from app.services.storage_service import get_storage_service

    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else current_user_id

    logger.info(f"[MaterialUpdateWithAttachments] Starting: material_id={id}, user_type={user_type}, "
                f"delete_attachment_ids={delete_attachment_ids}, files_count={len(files) if files else 0}")

    # 获取素材（验证所有权）
    material = await MaterialService.get_material(db, id, owner_operator_id=owner_operator_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="素材不存在"
        )

    # 解析要删除的附件ID
    parsed_delete_ids = []
    if delete_attachment_ids:
        try:
            parsed_delete_ids = [int(aid.strip()) for aid in delete_attachment_ids.split(",") if aid.strip()]
            logger.debug(f"[MaterialUpdateWithAttachments] Parsed delete_attachment_ids: {parsed_delete_ids}")
        except ValueError:
            logger.warning(f"[MaterialUpdateWithAttachments] Invalid delete_attachment_ids format: {delete_attachment_ids}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="附件ID格式不正确"
            )

    # 解析标签ID
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()]
            logger.debug(f"[MaterialUpdateWithAttachments] Parsed tag_ids: {parsed_tag_ids}")
        except ValueError:
            logger.warning(f"[MaterialUpdateWithAttachments] Invalid tag_ids format: {tag_ids}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="标签ID格式不正确"
            )

    # 构建更新数据
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if content is not None:
        update_data["content"] = content
    if topic is not None:
        update_data["topic"] = topic
    if content_type is not None:
        update_data["content_type"] = content_type
    if text_content is not None:
        update_data["text_content"] = text_content
    if platform_id is not None:
        update_data["platform_id"] = platform_id
    if category_id is not None:
        update_data["category_id"] = category_id
    if source_url is not None:
        update_data["source_url"] = source_url
    if parsed_tag_ids is not None:
        update_data["tag_ids"] = parsed_tag_ids

    # 删除指定附件
    deleted_count = 0
    for aid in parsed_delete_ids:
        try:
            await MaterialService.delete_material_attachment(db, aid, owner_operator_id)
            deleted_count += 1
            logger.info(f"[MaterialUpdateWithAttachments] Deleted attachment: attachment_id={aid}")
        except Exception as e:
            logger.warning(f"[MaterialUpdateWithAttachments] Failed to delete attachment {aid}: {e}")

    # 处理新文件上传
    saved_count = 0
    failed_count = 0
    image_count = 0
    video_count = 0

    if files and len(files) > 0:
        # 验证文件数量（考虑剩余容量）
        current_attachments = await MaterialService.list_material_attachments(db, id, owner_operator_id)
        current_count = len(current_attachments) - deleted_count
        if current_count + len(files) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="素材最多支持5个附件"
            )

        # 验证文件类型和大小
        allowed_image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        allowed_video_extensions = {'mp4', 'webm', 'mov'}
        max_size = 50 * 1024 * 1024  # 50MB
        for idx, file in enumerate(files):
            if file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                logger.debug(f"[MaterialUpdateWithAttachments] File {idx}: filename={file.filename}, ext={ext}")
                if ext not in allowed_image_extensions and ext not in allowed_video_extensions:
                    logger.warning(f"[MaterialUpdateWithAttachments] Unsupported file format: {ext}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的文件格式: {ext}，仅支持 jpg/jpeg/png/gif/webp/mp4/webm/mov"
                    )

        # 保存文件
        storage = get_storage_service()
        for idx, file in enumerate(files):
            try:
                file_content = await file.read()

                if not file_content:
                    logger.warning(f"[MaterialUpdateWithAttachments] File {idx} is empty, skipping: filename={file.filename}")
                    continue

                logger.info(f"[MaterialUpdateWithAttachments] Processing file {idx}: filename={file.filename}, "
                           f"size={len(file_content)} bytes")

                # 获取文件扩展名和类型
                ext = "jpg"
                file_type = "image"
                if file.filename and '.' in file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    if ext in {'mp4', 'webm', 'mov'}:
                        file_type = "video"

                original_url = None
                thumbnail_url = None
                width, height = None, None
                duration = None

                if file_type == "image":
                    # 保存原图并生成缩略图（使用素材库的方法）
                    original_url, thumbnail_url = await storage.save_material_image_with_thumbnail(
                        file_content=file_content,
                        owner_admin_id=material.owner_operator_id,
                        material_id=material.id,
                        extension=ext,
                    )

                    # 获取图片尺寸
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(file_content))
                        width, height = img.size
                    except Exception:
                        pass
                else:
                    # 保存视频（使用素材库的方法）
                    original_url = await storage.save_material_video(
                        file_content=file_content,
                        owner_admin_id=material.owner_operator_id,
                        material_id=material.id,
                        extension=ext,
                    )

                # 保存附件记录
                if original_url:
                    # 获取当前最大 sort_order
                    current_attachments = await MaterialService.list_material_attachments(db, id, owner_operator_id)
                    max_sort = max([a.sort_order for a in current_attachments], default=-1)

                    await MaterialService.add_material_attachment(
                        db,
                        material_id=material.id,
                        owner_operator_id=material.owner_operator_id,
                        file_type=file_type,
                        file_url=original_url,
                        file_name=file.filename or f"{file_type}_{idx + 1}.{ext}",
                        file_size=len(file_content),
                        sort_order=max_sort + 1,
                        width=width,
                        height=height,
                        duration=duration,
                        thumbnail_url=thumbnail_url,
                    )
                    saved_count += 1
                    if file_type == "image":
                        image_count += 1
                    else:
                        video_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"[MaterialUpdateWithAttachments] Exception processing file {idx}: {e}", exc_info=True)
                failed_count += 1

        logger.info(f"[MaterialUpdateWithAttachments] File processing complete: saved={saved_count}, failed={failed_count}")

    # 更新素材基本信息
    if update_data:
        material = await MaterialService.update_material(
            db,
            material_id=id,
            owner_operator_id=owner_operator_id,
            **update_data,
        )
        logger.info(f"[MaterialUpdateWithAttachments] Updated material basic info: material_id={id}")

    # 加载关联数据并构建响应
    await db.refresh(material)
    attachments = await MaterialService.list_material_attachments(db, material.id, material.owner_operator_id)
    tags = await MaterialService.get_material_tags(db, material.id, material.owner_operator_id)
    is_favorite = False
    if not is_super_admin:
        favorite = await MaterialService.get_favorite(db, material.id, current_user_id)
        is_favorite = favorite is not None

    response_data = build_material_response(material, attachments, tags, is_favorite)

    logger.info(f"[MaterialUpdateWithAttachments] Update completed: material_id={id}, deleted={deleted_count}, added={saved_count}")

    if failed_count > 0:
        return success_response(data=response_data, message=f"更新成功，但有 {failed_count} 个文件上传失败（可能是文件大小超限）")
    return success_response(data=response_data, message="更新成功")


# ============================================
# 素材收藏管理
# ============================================
@router.post("/{id}/favorite")
async def favorite_material(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    收藏/取消收藏素材
    返回 is_favorite: True 表示已收藏，False 表示已取消收藏

    - 创作管理员：可收藏素材
    - 超级管理员：也可收藏素材（如需要）
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    user_id = current_user_id

    try:
        is_favorite = await MaterialService.toggle_favorite(
            db,
            material_id=id,
            user_id=user_id,
            owner_operator_id=user_id if user_type == "operator" else None,
        )
        return success_response(
            data={"is_favorite": is_favorite},
            message="已收藏" if is_favorite else "已取消收藏"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

