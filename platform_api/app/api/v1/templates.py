"""
模板管理 API 路由 (templates.py)

Author: Claude Code
Date: 2025
"""

import logging

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas import PaginatedResponse
from app.schemas.templates import (TemplateCopyRequest,
                                   TemplateCreate, TemplateResponse,
                                   TemplateTagCreate, TemplateTagResponse,
                                   TemplateTagUpdate, TemplateUpdate)
from app.services.template_service import TemplateService
from app.utils.deps import get_token_payload_required
from app.utils.response import ApiResponse, success_response

router = APIRouter()


# ============================================
# 模板平台管理（独立平台表）- 放在最前面避免路由冲突
# ============================================


@router.post(
    "/platforms", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED
)
async def create_template_platform(
    data: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建模板平台

    - 仅创作管理员可创建平台
    - 超级管理员不能创建平台
    """
    from app.services.template_platform_service import TemplatePlatformService

    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建平台，请由创作管理员操作",
        )

    current_user_id = int(payload.get("sub"))
    service = TemplatePlatformService(db)
    platform = await service.create_platform(
        name=data.get("name"),
        owner_operator_id=current_user_id,
        created_by=current_user_id,
        description=data.get("description"),
        color=data.get("color"),
        sort_order=data.get("sort_order", 0),
    )

    return success_response(
        data={
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
        },
        message="创建成功",
    )


@router.get("/platforms", response_model=ApiResponse[list])
async def list_template_platforms(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板平台列表

    - 超级管理员：可查看所有平台
    - 创作管理员：只能查看自己的平台
    """
    from app.services.template_platform_service import TemplatePlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    service = TemplatePlatformService(db)
    platforms = await service.get_platforms(
        owner_operator_id=filter_owner_id, keyword=keyword
    )

    result = []
    for p in platforms:
        result.append(
            {
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
            }
        )
    return success_response(data=result, message="获取成功")


@router.get("/platforms/tree", response_model=ApiResponse[dict])
async def get_template_platform_tree(
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板平台分类标签树形结构

    返回完整的平台-分类-标签层级结构，用于左侧导航栏展示。
    """
    from app.services.template_platform_service import TemplatePlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    service = TemplatePlatformService(db)
    tree = await service.get_platform_tree(
        owner_operator_id=filter_owner_id,
    )
    return success_response(data=tree, message="获取成功")


@router.get("/platforms/{platform_id}", response_model=ApiResponse[dict])
async def get_template_platform(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """获取模板平台详情"""
    from app.services.template_platform_service import TemplatePlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = TemplatePlatformService(db)
    platform = await service.get_platform(
        platform_id, None if is_super_admin else current_user_id
    )
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="平台不存在")

    return success_response(
        data={
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
        },
        message="获取成功",
    )


@router.put("/platforms/{platform_id}", response_model=ApiResponse[dict])
async def update_template_platform(
    platform_id: int,
    data: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """更新模板平台"""
    from app.services.template_platform_service import TemplatePlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = TemplatePlatformService(db)
    try:
        platform = await service.update_platform(
            platform_id=platform_id,
            owner_operator_id=None if is_super_admin else current_user_id,
            **data,
        )
        return success_response(
            data={
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
            },
            message="更新成功",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/platforms/{platform_id}")
async def delete_template_platform(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """删除模板平台（级联删除关联的分类和标签）"""
    from app.services.template_platform_service import TemplatePlatformService

    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    service = TemplatePlatformService(db)
    try:
        await service.delete_platform(
            platform_id, None if is_super_admin else current_user_id
        )
        return success_response(message="删除成功")
    except Exception as e:
        error_msg = str(e)
        if "存在" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


@router.get("/platforms/{platform_id}/stats", response_model=ApiResponse[dict])
async def get_template_platform_stats(
    platform_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板平台统计信息（模板数量、分类数量、标签数量）
    """

    from app.models import (TemplateTag,
                            TemplateTagRel)
    from app.services.template_platform_service import TemplatePlatformService

    service = TemplatePlatformService(db)
    platform = await service.get_platform(platform_id)
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="平台不存在")

    # 统计分类数量
    category_count = len(platform.categories)

    # 统计标签数量
    tag_count = sum(len(cat.tags) for cat in platform.categories)

    # 统计模板数量
    if platform.categories:
        category_ids = [cat.id for cat in platform.categories]
        template_count = (
            await db.scalar(
                select(func.count(func.distinct(TemplateTagRel.template_id)))
                .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
                .where(TemplateTag.category_id.in_(category_ids))
            )
            or 0
        )
    else:
        template_count = 0

    return success_response(
        data={
            "platform_id": platform_id,
            "template_count": template_count,
            "category_count": category_count,
            "tag_count": tag_count,
        },
        message="获取成功",
    )


# ============================================
# 批量操作请求模型
# ============================================
class BatchDeleteRequest(BaseModel):
    template_ids: List[int]


class BatchStatusRequest(BaseModel):
    template_ids: List[int]
    status: str  # "enabled" or "disabled"


class BatchCopyRequest(BaseModel):
    template_ids: List[int]
    new_names: Optional[dict] = None  # {"1": "新名称1", "2": "新名称2"}
    target_operator_id: Optional[int] = None  # 超级管理员用：复制到指定管理员名下
    target_platform_id: int  # 目标平台
    target_category_id: int  # 目标分类
    target_tag_ids: List[int]  # 复制后设置的目标标签（必填）


class BatchTransferRequest(BaseModel):
    template_ids: List[int]
    target_operator_id: int
    target_platform_id: int  # 目标平台
    target_category_id: int  # 目标分类
    target_tag_ids: List[int]  # 目标标签（必填）


class MigrateTagRequest(BaseModel):
    target_tag_id: int


class BatchMigrateRequest(BaseModel):
    template_ids: List[int]
    target_tag_id: int
    source_tag_id: Optional[int] = None


# ============================================
# 响应构建辅助函数
# ============================================
def build_template_response(
    item, tags=None, platform=None, include_owner=False, attachments=None
):
    """构建模板响应数据（统一复用）"""
    if tags is None:
        tags = []
    if attachments is None:
        attachments = []
    category = None
    if tags:
        first_tag = tags[0]
        if isinstance(first_tag, dict) and "category" in first_tag:
            category = first_tag["category"]
        elif hasattr(first_tag, "category") and first_tag.category:
            category = first_tag.category

    # 转换附件数据
    serialized_attachments = []
    for att in attachments:
        if hasattr(att, "id"):
            # 模型对象，需要序列化
            serialized_attachments.append(
                {
                    "id": att.id,
                    "template_id": att.template_id,
                    "file_type": att.file_type,
                    "file_url": att.file_url,
                    "file_name": att.file_name,
                    "file_size": att.file_size,
                    "sort_order": att.sort_order,
                    "width": att.width,
                    "height": att.height,
                    "duration": att.duration,
                    "thumbnail_url": att.thumbnail_url,
                    "created_at": att.created_at,
                    "updated_at": att.updated_at,
                }
            )
        else:
            # 已经是字典格式
            serialized_attachments.append(att)

    # 转换 platform 对象为字典（如果需要）
    serialized_platform = None
    if platform:
        if isinstance(platform, dict):
            serialized_platform = platform
        else:
            serialized_platform = {
                "id": platform.id,
                "name": platform.name,
                "description": platform.description,
                "color": platform.color,
                "sort_order": platform.sort_order,
                "created_by": platform.created_by,
                "owner_operator_id": platform.owner_operator_id,
                "created_at": platform.created_at,
                "updated_at": platform.updated_at,
            }

    # 转换 category 对象为字典（如果需要）
    serialized_category = None
    if category:
        if isinstance(category, dict):
            serialized_category = category
        else:
            serialized_category = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "template_platform_id": category.template_platform_id,
                "sort_order": category.sort_order,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            }

    data = {
        "id": item.id,
        "name": item.name,
        "product_name": (getattr(item, "product_name", None) or "").strip() or "产品",
        "description": item.description if item.description is not None else "",
        "content_type": item.content_type,
        "prompt_template": item.prompt_template,
        "variables_json": item.variables_json,
        "style_reference": item.style_reference,
        "platform_rules_json": item.platform_rules_json,
        "status": item.status,
        "platform_id": item.platform_id,
        "original_template_id": item.original_template_id,
        "created_by": item.created_by,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "platform": serialized_platform,
        "category": serialized_category,
        "tags": tags,
        "image_count": item.image_count,
        "video_count": item.video_count,
        "attachments": serialized_attachments,
        "image_size_ratio": item.image_size_ratio,
        "add_watermark": item.add_watermark,
        # ===== 爆款模板字段 =====
        "viral_type": item.viral_type,
        "product_selling_points": item.product_selling_points,
        "opening_seed_id": item.opening_seed_id,
        "emotion_seed_id": item.emotion_seed_id,
        "ending_seed_id": item.ending_seed_id,
        "viral_score": item.viral_score,
        "viral_tags": item.viral_tags,
        "use_count": item.use_count,
        "success_count": item.success_count,
    }
    if include_owner:
        data["owner_admin_id"] = item.owner_operator_id
    return data


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
            "template_platform_id": tag.category.template_platform_id,
            "sort_order": tag.category.sort_order,
            "created_at": tag.category.created_at,
            "updated_at": tag.category.updated_at,
        }
        if tag.category.platform:
            tag_dict["category"]["platform"] = {
                "id": tag.category.platform.id,
                "name": tag.category.platform.name,
                "description": tag.category.platform.description,
                "color": tag.category.platform.color,
                "sort_order": tag.category.platform.sort_order,
                "created_at": tag.category.platform.created_at,
                "updated_at": tag.category.platform.updated_at,
            }
    return tag_dict


async def load_template_tags(db, template_id):
    """加载模板的标签列表并构建响应"""
    tags_data = await TemplateService.get_template_tags_by_template_id(db, template_id)
    return [build_tag_response(tag) for tag in tags_data]


# ============================================
# 模板分类管理（3级结构：平台 -> 分类 -> 标签）
# ============================================
@router.get("/categories", response_model=ApiResponse[list])
async def list_template_categories(
    platform_id: Optional[int] = Query(None, description="平台ID筛选"),
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板分类列表

    - 超级管理员：可查看所有分类
    - 创作管理员：只能查看自己的分类
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    categories = await TemplateService.list_template_categories(
        db, owner_operator_id=filter_owner_id, platform_id=platform_id
    )

    # 加载统计信息
    result = []
    for cat in categories:
        tag_count = await TemplateService.count_tags_by_category(db, cat.id)
        result.append(
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "platform_id": cat.template_platform_id,
                "sort_order": cat.sort_order,
                "tag_count": tag_count,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
            }
        )

    return success_response(data=result, message="获取成功")


@router.post("/categories", response_model=ApiResponse[dict])
async def create_template_category(
    request: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建模板分类
    """
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建分类，请由创作管理员操作",
        )

    current_user_id = int(payload.get("sub"))

    category = await TemplateService.create_template_category(
        db,
        name=request["name"],
        template_platform_id=request["platform_id"],
        owner_operator_id=current_user_id,
        created_by=current_user_id,
        description=request.get("description"),
        color=request.get("color"),
        sort_order=request.get("sort_order", 0),
    )

    return success_response(
        data={
            "id": category.id,
            "name": category.name,
            "platform_id": category.template_platform_id,
        },
        message="创建成功",
    )


@router.put("/categories/{id}", response_model=ApiResponse[dict])
async def update_template_category(
    id: int,
    request: dict,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新模板分类
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    category = await TemplateService.update_template_category(
        db,
        category_id=id,
        owner_operator_id=None if is_super_admin else current_user_id,
        **{k: v for k, v in request.items() if v is not None},
    )

    return success_response(
        data={
            "id": category.id,
            "name": category.name,
        },
        message="更新成功",
    )


@router.delete("/categories/{id}")
async def delete_template_category(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除模板分类（同时删除分类下的所有标签）
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    await TemplateService.delete_template_category(
        db, id, None if is_super_admin else current_user_id
    )
    return success_response(message="删除成功")


# ============================================
# 模板标签管理
# ============================================
@router.get("/tags", response_model=ApiResponse[list[TemplateTagResponse]])
async def list_template_tags(
    category_id: Optional[int] = Query(None, description="分类ID，筛选特定分类的标签"),
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板标签列表

    - category_id: 可选，筛选特定分类的标签
    - 超级管理员：可查看所有标签，或通过owner_operator_id筛选特定管理员的标签
    - 创作管理员：只能查看自己的标签
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 权限控制：超级管理员可查看所有或筛选，创作管理员只能查看自己的
    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    tags = await TemplateService.list_template_tags(
        db, owner_operator_id=filter_owner_id, category_id=category_id
    )

    response_tags = []
    for tag in tags:
        response_tags.append(
            {
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
        )

    return success_response(data=response_tags, message="获取成功")


@router.post("/tags", response_model=ApiResponse[TemplateTagResponse])
async def create_template_tag(
    request: TemplateTagCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建模板标签

    - 创作管理员为自己创建标签
    - 标签必须属于某个分类（category_id）
    """
    created_by = int(payload.get("sub"))
    tag = await TemplateService.create_template_tag(
        db,
        name=request.name,
        category_id=request.category_id,
        created_by=created_by,
        description=request.description,
        color=request.color,
    )
    return success_response(data=tag, message="创建成功")


@router.put("/tags/{id}", response_model=ApiResponse[TemplateTagResponse])
async def update_template_tag(
    id: int,
    request: TemplateTagUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新模板标签

    - 超级管理员：可更新所有标签
    - 创作管理员：只能更新自己的标签
    """
    created_by = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    try:
        tag = await TemplateService.update_template_tag(
            db,
            tag_id=id,
            created_by=created_by,
            is_super_admin=is_super_admin,
            **request.model_dump(exclude_unset=True),
        )

        response_data = {
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

        return success_response(data=response_data, message="更新成功")
    except Exception as e:
        error_msg = str(e)
        if "系统默认标签" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


@router.delete("/tags/{id}")
async def delete_template_tag(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除模板标签（系统默认标签不可删除）

    - 超级管理员：可删除所有标签
    - 创作管理员：只能删除自己的标签
    """
    created_by = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    try:
        await TemplateService.delete_template_tag(
            db, id, created_by, is_super_admin=is_super_admin
        )
        return success_response(data=None, message="删除成功")
    except Exception as e:
        error_msg = str(e)
        if "系统默认标签" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)


# ============================================
# 模板管理
# ============================================
@router.get("", response_model=ApiResponse[PaginatedResponse[TemplateResponse]])
async def list_templates(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    platform_id: Optional[int] = Query(None, description="平台筛选"),
    category_id: Optional[int] = Query(None, description="分类筛选"),
    tag_id: Optional[int] = Query(None, description="标签筛选"),
    no_tag: bool = Query(False, description="仅显示无标签模板"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板列表

    - 超级管理员：可查看所有模板，或通过owner_operator_id筛选特定管理员的模板
    - 创作管理员：只能查看自己的模板
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    items, total = await TemplateService.list_templates(
        db,
        owner_operator_id=filter_owner_id,
        page=page,
        limit=limit,
        status=status,
        content_type=content_type,
        platform_id=platform_id,
        category_id=category_id,
        tag_id=tag_id,
        no_tag=no_tag,
        keyword=keyword,
    )

    response_items = []
    for item in items:
        tags = await load_template_tags(db, item.id)
        platform = None
        if item.platform_id:
            platform = await TemplateService.get_template_platform(
                db, item.platform_id, filter_owner_id
            )
        attachments = await TemplateService.list_template_attachments(
            db, item.id, filter_owner_id
        )
        response_items.append(
            build_template_response(
                item,
                tags,
                platform,
                include_owner=(user_type == "super_admin"),
                attachments=attachments,
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
        message="获取成功",
    )


@router.post("", response_model=ApiResponse[TemplateResponse])
async def create_template(
    request: TemplateCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建模板

    - 仅创作管理员可创建模板
    - 超级管理员不能创建模板（需要通过特定创作管理员创建）
    """
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        # 超级管理员可以通过 owner_operator_id 指定创作管理员
        owner_operator_id = request.owner_operator_id or int(payload.get("sub"))
    else:
        owner_operator_id = int(payload.get("sub"))

    created_by = owner_operator_id

    # DEBUG: 打印创建模板的请求参数
    logger.debug(
        f"[Template Create] request: name={request.name}, content_type={request.content_type}, "
        f"platform_id={request.platform_id}, tag_ids={request.tag_ids}, "
        f"owner_operator_id={owner_operator_id}"
    )

    template = await TemplateService.create_template(
        db,
        name=request.name,
        content_type=request.content_type,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
        product_name=request.product_name,
        description=request.description,
        prompt_template=request.prompt_template,
        variables_json=request.variables_json,
        style_reference=request.style_reference,
        platform_rules_json=request.platform_rules_json,
        platform_id=request.platform_id,
        tag_ids=request.tag_ids,
        image_size_ratio=request.image_size_ratio,
        add_watermark=request.add_watermark,
        viral_type=request.viral_type,
        product_selling_points=request.product_selling_points,
        opening_seed_id=request.opening_seed_id,
        emotion_seed_id=request.emotion_seed_id,
        ending_seed_id=request.ending_seed_id,
    )

    # DEBUG: 打印创建后的模板信息
    logger.debug(
        f"[Template Create] template created: id={template.id}, platform_id={template.platform_id}"
    )

    # 加载关联数据并构建响应
    tags = await load_template_tags(db, template.id)
    platform = None
    if template.platform_id:
        platform = await TemplateService.get_template_platform(
            db, template.platform_id, owner_operator_id
        )
    attachments = await TemplateService.list_template_attachments(
        db, template.id, owner_operator_id
    )

    response_data = build_template_response(
        template, tags, platform, include_owner=True, attachments=attachments
    )
    return success_response(data=response_data, message="创建成功")


@router.get("/{id}", response_model=ApiResponse[TemplateResponse])
async def get_template(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板详情

    - 超级管理员：可查看所有模板
    - 创作管理员：只能查看自己的模板
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    template = await TemplateService.get_template(
        db, id, owner_operator_id=None if is_super_admin else current_user_id
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    tags = await load_template_tags(db, template.id)
    platform = None
    if template.platform_id:
        platform = await TemplateService.get_template_platform(
            db, template.platform_id, template.owner_operator_id
        )
    attachments = await TemplateService.list_template_attachments(
        db, template.id, template.owner_operator_id
    )

    response_data = build_template_response(
        template, tags, platform, include_owner=is_super_admin, attachments=attachments
    )
    return success_response(data=response_data, message="获取成功")


@router.put("/{id}", response_model=ApiResponse[TemplateResponse])
async def update_template(
    id: int,
    request: TemplateUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新模板

    - 超级管理员：可更新所有模板
    - 创作管理员：只能更新自己的模板
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    try:
        template = await TemplateService.update_template(
            db,
            template_id=id,
            owner_operator_id=None if is_super_admin else current_user_id,
            **request.model_dump(exclude_unset=True),
        )

        tags = await load_template_tags(db, template.id)
        platform = None
        if template.platform_id:
            platform = await TemplateService.get_template_platform(
                db, template.platform_id, template.owner_operator_id
            )
        attachments = await TemplateService.list_template_attachments(
            db, template.id, template.owner_operator_id
        )

        response_data = build_template_response(
            template,
            tags,
            platform,
            include_owner=is_super_admin,
            attachments=attachments,
        )
        return success_response(data=response_data, message="更新成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{id}/update-with-attachments", response_model=ApiResponse[TemplateResponse]
)
async def update_template_with_attachments(
    id: int,
    name: Optional[str] = Form(default=None, description="模板名称"),
    product_name: Optional[str] = Form(default=None, description="产品名称（必填）"),
    description: Optional[str] = Form(default=None, description="模板内容"),
    prompt_template: Optional[str] = Form(default=None, description="提示词模板"),
    content_type: Optional[str] = Form(default=None, description="内容类型"),
    tag_ids: Optional[str] = Form(default=None, description="标签ID列表（逗号分隔）"),
    platform_id: Optional[int] = Form(default=None, description="所属平台ID"),
    style_reference: Optional[str] = Form(default=None, description="风格参考"),
    platform_rules_json: Optional[str] = Form(default=None, description="平台规则JSON"),
    status: Optional[str] = Form(default=None, description="状态"),
    image_size_ratio: Optional[str] = Form(
        default=None, description="图片尺寸比例：1:1/4:3/16:9/3:4/9:16"
    ),
    add_watermark: Optional[bool] = Form(default=None, description="是否添加水印"),
    viral_type: Optional[str] = Form(default=None, description="爆款类型"),
    product_selling_points: Optional[str] = Form(
        default=None, description="产品卖点描述"
    ),
    opening_seed_id: Optional[str] = Form(default=None, description="开头模式种子ID"),
    emotion_seed_id: Optional[str] = Form(default=None, description="情感基调种子ID"),
    ending_seed_id: Optional[str] = Form(default=None, description="结尾模式种子ID"),
    delete_attachment_ids: Optional[str] = Form(
        default=None, description="要删除的附件ID列表（逗号分隔）"
    ),
    files: Optional[List[UploadFile]] = File(
        default=None, description="新文件列表（图片或视频，最多5个）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新模板并管理附件

    - 使用 multipart/form-data 格式
    - 支持删除指定附件
    - 支持添加新附件
    - 支持同时更新模板基本信息
    """
    import io

    from app.services.storage_service import get_storage_service

    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))
    is_super_admin = user_type == "super_admin"
    owner_operator_id = None if is_super_admin else current_user_id

    logger.info(
        f"[TemplateUpdateWithAttachments] Starting: template_id={id}, user_type={user_type}, "
        f"delete_attachment_ids={delete_attachment_ids}, files_count={len(files) if files else 0}"
    )

    # 获取模板（验证所有权）
    template = await TemplateService.get_template(db, id, owner_operator_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    # 解析要删除的附件ID
    parsed_delete_ids = []
    if delete_attachment_ids:
        try:
            parsed_delete_ids = [
                int(aid.strip())
                for aid in delete_attachment_ids.split(",")
                if aid.strip()
            ]
            logger.debug(
                f"[TemplateUpdateWithAttachments] Parsed delete_attachment_ids: {parsed_delete_ids}"
            )
        except ValueError:
            logger.warning(
                f"[TemplateUpdateWithAttachments] Invalid delete_attachment_ids format: {delete_attachment_ids}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="附件ID格式不正确"
            )

    # 解析标签ID
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [
                int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()
            ]
            logger.debug(
                f"[TemplateUpdateWithAttachments] Parsed tag_ids: {parsed_tag_ids}"
            )
        except ValueError:
            logger.warning(
                f"[TemplateUpdateWithAttachments] Invalid tag_ids format: {tag_ids}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="标签ID格式不正确"
            )

    # 解析 platform_rules_json
    import json

    parsed_platform_rules = None
    if platform_rules_json:
        try:
            parsed_platform_rules = json.loads(platform_rules_json)
        except Exception:
            logger.warning(
                f"[TemplateUpdateWithAttachments] Invalid platform_rules_json format: {platform_rules_json}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="平台规则JSON格式不正确"
            )

    # 构建更新数据
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if product_name is not None:
        update_data["product_name"] = product_name
    if description is not None:
        update_data["description"] = description
    if prompt_template is not None:
        update_data["prompt_template"] = prompt_template
    if content_type is not None:
        update_data["content_type"] = content_type
    if platform_id is not None:
        update_data["platform_id"] = platform_id
    if style_reference is not None:
        update_data["style_reference"] = style_reference
    if parsed_platform_rules is not None:
        update_data["platform_rules_json"] = parsed_platform_rules
    if status is not None:
        update_data["status"] = status
    if parsed_tag_ids is not None:
        update_data["tag_ids"] = parsed_tag_ids
    if image_size_ratio is not None:
        update_data["image_size_ratio"] = image_size_ratio
    if add_watermark is not None:
        update_data["add_watermark"] = add_watermark
    # 爆款类型：空字符串转为 "auto" 表示随机选择
    if viral_type is not None:
        update_data["viral_type"] = viral_type if viral_type else "auto"
    if product_selling_points is not None:
        update_data["product_selling_points"] = product_selling_points
    # 转换种子 ID："auto" 或空表示随机选择，否则保持原值（字符串）
    if opening_seed_id is not None:
        update_data["opening_seed_id"] = (
            "auto"
            if (opening_seed_id == "auto" or not opening_seed_id)
            else opening_seed_id
        )
    if emotion_seed_id is not None:
        update_data["emotion_seed_id"] = (
            "auto"
            if (emotion_seed_id == "auto" or not emotion_seed_id)
            else emotion_seed_id
        )
    if ending_seed_id is not None:
        update_data["ending_seed_id"] = (
            "auto"
            if (ending_seed_id == "auto" or not ending_seed_id)
            else ending_seed_id
        )

    logger.info(
        f"[TemplateUpdateWithAttachments] image_size_ratio received: '{image_size_ratio}', type: {type(image_size_ratio)}"
    )
    logger.info(f"[TemplateUpdateWithAttachments] update_data: {update_data}")

    # 删除指定附件
    deleted_count = 0
    for aid in parsed_delete_ids:
        try:
            await TemplateService.delete_template_attachment(db, aid, owner_operator_id)
            deleted_count += 1
            logger.info(
                f"[TemplateUpdateWithAttachments] Deleted attachment: attachment_id={aid}"
            )
        except Exception as e:
            logger.warning(
                f"[TemplateUpdateWithAttachments] Failed to delete attachment {aid}: {e}"
            )

    # 处理新文件上传
    saved_count = 0
    failed_count = 0
    image_count = 0
    video_count = 0

    if files and len(files) > 0:
        # 验证文件数量（考虑剩余容量）
        current_attachments = await TemplateService.list_template_attachments(
            db, id, owner_operator_id
        )
        current_count = len(current_attachments) - deleted_count
        if current_count + len(files) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="模板最多支持5个附件"
            )

        # 验证文件类型和大小
        allowed_image_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
        allowed_video_extensions = {"mp4", "webm", "mov"}
        max_size = 50 * 1024 * 1024  # 50MB
        for idx, file in enumerate(files):
            if file.filename:
                ext = (
                    file.filename.rsplit(".", 1)[-1].lower()
                    if "." in file.filename
                    else ""
                )
                logger.debug(
                    f"[TemplateUpdateWithAttachments] File {idx}: filename={file.filename}, ext={ext}"
                )
                if (
                    ext not in allowed_image_extensions
                    and ext not in allowed_video_extensions
                ):
                    logger.warning(
                        f"[TemplateUpdateWithAttachments] Unsupported file format: {ext}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的文件格式: {ext}，仅支持 jpg/jpeg/png/gif/webp/mp4/webm/mov",
                    )

        # 保存文件
        storage = get_storage_service()
        for idx, file in enumerate(files):
            try:
                file_content = await file.read()

                if not file_content:
                    logger.warning(
                        f"[TemplateUpdateWithAttachments] File {idx} is empty, skipping: filename={file.filename}"
                    )
                    continue

                logger.info(
                    f"[TemplateUpdateWithAttachments] Processing file {idx}: filename={file.filename}, "
                    f"size={len(file_content)} bytes"
                )

                # 获取文件扩展名和类型
                ext = "jpg"
                file_type = "image"
                if file.filename and "." in file.filename:
                    ext = file.filename.rsplit(".", 1)[-1].lower()
                    if ext in {"mp4", "webm", "mov"}:
                        file_type = "video"

                original_url = None
                thumbnail_url = None
                width, height = None, None
                duration = None

                if file_type == "image":
                    # 保存原图并生成缩略图
                    original_url, thumbnail_url = (
                        await storage.save_template_image_with_thumbnail(
                            file_content=file_content,
                            owner_admin_id=template.owner_operator_id,
                            template_id=template.id,
                            extension=ext,
                        )
                    )

                    # 获取图片尺寸
                    try:
                        from PIL import Image

                        img = Image.open(io.BytesIO(file_content))
                        width, height = img.size
                    except Exception:
                        pass
                else:
                    # 保存视频
                    original_url, thumbnail_url, duration = (
                        await storage.save_template_video(
                            file_content=file_content,
                            owner_admin_id=template.owner_operator_id,
                            template_id=template.id,
                            extension=ext,
                        )
                    )

                # 保存附件记录
                if original_url:
                    # 获取当前最大 sort_order
                    current_attachments = (
                        await TemplateService.list_template_attachments(
                            db, id, owner_operator_id
                        )
                    )
                    max_sort = max(
                        [a.sort_order for a in current_attachments], default=-1
                    )

                    await TemplateService.add_template_attachment(
                        db,
                        template_id=template.id,
                        owner_operator_id=template.owner_operator_id,
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
                logger.error(
                    f"[TemplateUpdateWithAttachments] Exception processing file {idx}: {e}",
                    exc_info=True,
                )
                failed_count += 1

        logger.info(
            f"[TemplateUpdateWithAttachments] File processing complete: saved={saved_count}, failed={failed_count}"
        )

    # 更新模板基本信息
    if update_data:
        template = await TemplateService.update_template(
            db,
            template_id=id,
            owner_operator_id=owner_operator_id,
            **update_data,
        )
        logger.info(
            f"[TemplateUpdateWithAttachments] Updated template basic info: template_id={id}"
        )

    # 加载关联数据并构建响应
    await db.refresh(template)
    tags = await load_template_tags(db, template.id)
    platform = None
    if template.platform_id:
        platform = await TemplateService.get_template_platform(
            db, template.platform_id, template.owner_operator_id
        )
    attachments = await TemplateService.list_template_attachments(
        db, template.id, template.owner_operator_id
    )

    response_data = build_template_response(
        template, tags, platform, include_owner=is_super_admin, attachments=attachments
    )

    logger.info(
        f"[TemplateUpdateWithAttachments] Update completed: template_id={id}, deleted={deleted_count}, added={saved_count}"
    )

    if failed_count > 0:
        return success_response(
            data=response_data,
            message=f"更新成功，但有 {failed_count} 个文件上传失败（可能是文件大小超限）",
        )
    return success_response(data=response_data, message="更新成功")


@router.delete("/{id}")
async def delete_template(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除模板

    - 超级管理员：可删除所有模板
    - 创作管理员：只能删除自己的模板
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    try:
        await TemplateService.delete_template(
            db,
            template_id=id,
            owner_operator_id=None if is_super_admin else current_user_id,
        )
        return success_response(message="删除成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================
# 批量操作
# ============================================
@router.post("/batch-delete")
async def batch_delete_templates(
    request: BatchDeleteRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """批量删除模板"""
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_id = None if is_super_admin else current_user_id

    success_count = 0
    failed_ids = []
    for tid in request.template_ids:
        try:
            await TemplateService.delete_template(db, tid, owner_id)
            success_count += 1
        except Exception:
            failed_ids.append(tid)

    msg = f"成功删除 {success_count} 个模板"
    if failed_ids:
        msg += f"，{len(failed_ids)} 个失败: {failed_ids}"
    return success_response(
        data={"success_count": success_count, "failed_ids": failed_ids}, message=msg
    )


@router.post("/batch-status")
async def batch_update_template_status(
    request: BatchStatusRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """批量更新模板状态"""
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"
    owner_id = None if is_super_admin else current_user_id

    if request.status not in ("enabled", "disabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status 必须为 enabled 或 disabled",
        )

    success_count = 0
    for tid in request.template_ids:
        try:
            await TemplateService.update_template(
                db, tid, owner_id, status=request.status
            )
            success_count += 1
        except Exception:
            pass

    return success_response(
        data={"success_count": success_count},
        message=f"成功更新 {success_count} 个模板状态",
    )


@router.post("/batch-copy")
async def batch_copy_templates(
    request: BatchCopyRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """批量复制模板

    - 创作管理员：复制到自己的名下
    - 超级管理员：可通过 target_operator_id 复制到指定创作管理员名下
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 超级管理员可指定目标创作管理员，否则复制到当前用户
    if user_type == "super_admin" and request.target_operator_id:
        target_operator_id = request.target_operator_id
    else:
        target_operator_id = current_user_id

    success_count = 0
    failed_ids = []
    for tid in request.template_ids:
        new_name = None
        if request.new_names and str(tid) in request.new_names:
            new_name = request.new_names[str(tid)]
        try:
            await TemplateService.copy_template(
                db,
                tid,
                target_operator_id,
                new_name=new_name,
                tag_ids=request.target_tag_ids,
            )
            success_count += 1
        except Exception:
            failed_ids.append(tid)

    msg = f"成功复制 {success_count} 个模板"
    if failed_ids:
        msg += f"，{len(failed_ids)} 个失败: {failed_ids}"
    return success_response(
        data={"success_count": success_count, "failed_ids": failed_ids}, message=msg
    )


@router.post("/batch-transfer")
async def batch_transfer_templates(
    request: BatchTransferRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """批量转移模板所有权（超级管理员专用）"""
    user_type = payload.get("user_type")
    if user_type != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可执行批量转移"
        )

    if len(request.template_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="单次最多转移 100 个模板"
        )

    result = await TemplateService.batch_transfer_templates(
        db,
        template_ids=request.template_ids,
        target_operator_id=request.target_operator_id,
        target_platform_id=request.target_platform_id,
        target_category_id=request.target_category_id,
        target_tag_ids=request.target_tag_ids,
    )
    return success_response(data=result, message="批量转移完成")


# ============================================
# 标签迁移
# ============================================
@router.post("/tags/{id}/migrate")
async def migrate_tag_templates(
    id: int,
    request: MigrateTagRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """将指定标签下的所有模板迁移到目标标签"""
    result = await TemplateService.migrate_tag_templates(
        db,
        source_tag_id=id,
        target_tag_id=request.target_tag_id,
    )
    return success_response(data=result, message="标签迁移完成")


@router.post("/batch-migrate-tags")
async def batch_migrate_templates(
    request: BatchMigrateRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """批量将模板从源标签迁移到目标标签"""
    result = await TemplateService.batch_migrate_templates(
        db,
        template_ids=request.template_ids,
        target_tag_id=request.target_tag_id,
        source_tag_id=request.source_tag_id,
    )
    return success_response(data=result, message="批量标签迁移完成")


# ============================================
# 标签统计
# ============================================
@router.get("/tag-summary")
async def get_template_tag_summary(
    owner_operator_id: Optional[int] = Query(
        None, description="指定创作管理员ID（仅超级管理员可用）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """获取标签统计汇总（各标签模板数量、无标签模板数）"""
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    if user_type == "super_admin":
        filter_owner_id = owner_operator_id
    else:
        filter_owner_id = current_user_id

    result = await TemplateService.get_tag_summary(db, filter_owner_id)
    return success_response(data=result, message="获取成功")


@router.post("/{id}/copy", response_model=ApiResponse[TemplateResponse])
async def copy_template(
    id: int,
    request: TemplateCopyRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    复制模板

    - 创作管理员：复制到自己的名下
    - 超级管理员：可通过 target_operator_id 复制到指定创作管理员名下
    """
    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))

    # 超级管理员可指定目标创作管理员
    if (
        user_type == "super_admin"
        and hasattr(request, "target_operator_id")
        and request.target_operator_id
    ):
        owner_operator_id = request.target_operator_id
    else:
        owner_operator_id = current_user_id

    try:
        tag_ids = getattr(request, "target_tag_ids", None)
        target_platform_id = getattr(request, "target_platform_id", None)
        target_category_id = getattr(request, "target_category_id", None)
        template = await TemplateService.copy_template(
            db,
            template_id=id,
            owner_operator_id=owner_operator_id,
            new_name=request.new_name,
            tag_ids=tag_ids,
            target_platform_id=target_platform_id,
            target_category_id=target_category_id,
        )

        tags = await load_template_tags(db, template.id)
        platform = None
        if template.platform_id:
            platform = await TemplateService.get_template_platform(
                db, template.platform_id, template.owner_operator_id
            )

        # 加载附件
        attachments = await TemplateService.list_template_attachments(
            db, template.id, template.owner_operator_id
        )

        response_data = build_template_response(
            template, tags, platform, include_owner=True, attachments=attachments
        )
        return success_response(data=response_data, message="复制成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/upload-image", response_model=ApiResponse[dict])
async def upload_template_image(
    file: UploadFile = File(..., description="图片文件"),
    payload: dict = Depends(get_token_payload_required),
):
    """
    上传模板图片（兼容旧接口）

    - 仅用于上传单张图片，返回图片URL
    - 创作管理员：可上传图片
    - 超级管理员：不可上传图片
    """
    import hashlib
    import os
    from datetime import datetime, timezone

    from app.services.storage_service import get_storage_service

    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))

    logger.info(
        f"[TemplateUploadImage] Starting upload: user_type={user_type}, current_user_id={current_user_id}, "
        f"filename={file.filename}"
    )

    if user_type == "super_admin":
        logger.warning(
            f"[TemplateUploadImage] Super admin attempted upload: user_id={current_user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能上传图片，请由创作管理员操作",
        )

    owner_operator_id = current_user_id

    # 读取文件内容
    file_content = await file.read()
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容为空"
        )

    # 验证文件类型
    allowed_image_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in allowed_image_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式: {ext}，仅支持 jpg/jpeg/png/gif/webp",
            )

    # 获取存储服务
    storage = get_storage_service()

    # 生成唯一文件名
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    random_suffix = hashlib.md5(f"{timestamp}_{os.urandom(8)}".encode()).hexdigest()[:8]
    filename = f"temp_{timestamp}_{random_suffix}.{ext}"

    # 保存到临时目录：Templates/{owner_admin_id}/temp/
    storage_path = (
        storage.cos_mount_path / storage.TEMPLATES_DIR / str(owner_operator_id) / "temp"
    )
    storage_path.mkdir(parents=True, exist_ok=True)

    file_path = storage_path / filename
    file_path.write_bytes(file_content)

    # 生成 URL
    original_url = storage._path_to_url(file_path)

    logger.info(f"[TemplateUploadImage] Image saved: original_url={original_url}")

    return success_response(data={"url": original_url}, message="上传成功")


@router.post("/upload", response_model=ApiResponse[TemplateResponse])
async def upload_template(
    name: str = Form(..., description="模板名称"),
    product_name: str = Form(..., description="产品名称（必填）"),
    description: Optional[str] = Form(default=None, description="模板内容"),
    prompt_template: Optional[str] = Form(default=None, description="提示词模板"),
    text_content: Optional[str] = Form(default=None, description="文本内容"),
    content_type: str = Form(default="image_text", description="内容类型"),
    tag_ids: Optional[str] = Form(default=None, description="标签ID列表（逗号分隔）"),
    platform_id: Optional[int] = Form(default=None, description="所属平台ID"),
    style_reference: Optional[str] = Form(default=None, description="风格参考"),
    platform_rules_json: Optional[str] = Form(default=None, description="平台规则JSON"),
    image_size_ratio: Optional[str] = Form(
        default=None, description="图片尺寸比例：1:1/4:3/16:9/3:4/9:16"
    ),
    add_watermark: Optional[bool] = Form(default=None, description="是否添加水印"),
    viral_type: Optional[str] = Form(default=None, description="爆款类型"),
    product_selling_points: Optional[str] = Form(
        default=None, description="产品卖点描述"
    ),
    opening_seed_id: Optional[str] = Form(default=None, description="开头模式种子ID"),
    emotion_seed_id: Optional[str] = Form(default=None, description="情感基调种子ID"),
    ending_seed_id: Optional[str] = Form(default=None, description="结尾模式种子ID"),
    files: Optional[List[UploadFile]] = File(
        default=None, description="文件列表（图片或视频，最多5个）"
    ),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    上传模板（支持文件上传）

    - 使用 multipart/form-data 格式
    - 支持同时上传多张图片和视频（最多5个）
    - 自动保存原图并生成缩略图
    - 创作管理员：可创建模板
    - 超级管理员：不可创建模板
    """
    import io

    from app.services.storage_service import get_storage_service

    user_type = payload.get("user_type")
    current_user_id = int(payload.get("sub"))

    logger.info(
        f"[TemplateUpload] Starting upload: user_type={user_type}, current_user_id={current_user_id}, "
        f"name={name}, files_count={len(files) if files else 0}"
    )

    if user_type == "super_admin":
        logger.warning(
            f"[TemplateUpload] Super admin attempted upload: user_id={current_user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能上传模板，请由创作管理员操作",
        )

    owner_operator_id = current_user_id
    created_by = current_user_id

    # 解析标签ID
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [
                int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()
            ]
            logger.debug(f"[TemplateUpload] Parsed tag_ids: {parsed_tag_ids}")
        except ValueError:
            logger.warning(f"[TemplateUpload] Invalid tag_ids format: {tag_ids}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="标签ID格式不正确"
            )

    # 验证文件数量
    if files and len(files) > 5:
        logger.warning(f"[TemplateUpload] Too many files: {len(files)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="最多上传5个文件"
        )

    # 验证文件类型和大小
    if files:
        allowed_image_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
        allowed_video_extensions = {"mp4", "webm", "mov"}
        max_size = 50 * 1024 * 1024  # 50MB
        for idx, file in enumerate(files):
            if file.filename:
                ext = (
                    file.filename.rsplit(".", 1)[-1].lower()
                    if "." in file.filename
                    else ""
                )
                logger.debug(
                    f"[TemplateUpload] File {idx}: filename={file.filename}, ext={ext}, "
                    f"content_type={file.content_type}"
                )
                if (
                    ext not in allowed_image_extensions
                    and ext not in allowed_video_extensions
                ):
                    logger.warning(f"[TemplateUpload] Unsupported file format: {ext}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的文件格式: {ext}，仅支持 jpg/jpeg/png/gif/webp/mp4/webm/mov",
                    )

    # 解析 platform_rules_json
    import json

    parsed_platform_rules = None
    if platform_rules_json:
        try:
            parsed_platform_rules = json.loads(platform_rules_json)
        except Exception:
            logger.warning(
                f"[TemplateUpload] Invalid platform_rules_json format: {platform_rules_json}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="平台规则JSON格式不正确"
            )

    # 爆款类型：空字符串转为 "auto" 表示随机选择
    _viral_type = viral_type if viral_type else "auto"
    # 转换种子 ID："auto" 或空表示随机选择，否则保持原值（字符串）
    _opening_seed_id = (
        "auto"
        if (opening_seed_id == "auto" or not opening_seed_id)
        else opening_seed_id
    )
    _emotion_seed_id = (
        "auto"
        if (emotion_seed_id == "auto" or not emotion_seed_id)
        else emotion_seed_id
    )
    _ending_seed_id = (
        "auto" if (ending_seed_id == "auto" or not ending_seed_id) else ending_seed_id
    )

    # 创建模板
    template = await TemplateService.create_template(
        db,
        name=name,
        content_type=content_type,
        owner_operator_id=owner_operator_id,
        created_by=created_by,
        product_name=product_name,
        description=description,
        prompt_template=prompt_template,
        variables_json=None,
        style_reference=style_reference,
        platform_rules_json=parsed_platform_rules,
        platform_id=platform_id,
        tag_ids=parsed_tag_ids,
        image_size_ratio=image_size_ratio,
        add_watermark=add_watermark,
        viral_type=_viral_type,
        product_selling_points=product_selling_points,
        opening_seed_id=_opening_seed_id,
        emotion_seed_id=_emotion_seed_id,
        ending_seed_id=_ending_seed_id,
    )
    logger.info(
        f"[TemplateUpload] Created template: id={template.id}, owner_operator_id={owner_operator_id}"
    )

    # 处理文件上传
    if files and template.id:
        storage = get_storage_service()

        saved_count = 0
        failed_count = 0
        image_count = 0
        video_count = 0

        for idx, file in enumerate(files):
            try:
                file_content = await file.read()

                if not file_content:
                    logger.warning(
                        f"[TemplateUpload] File {idx} is empty, skipping: filename={file.filename}"
                    )
                    continue

                logger.info(
                    f"[TemplateUpload] Processing file {idx}: filename={file.filename}, "
                    f"size={len(file_content)} bytes"
                )

                # 获取文件扩展名和类型
                ext = "jpg"
                file_type = "image"
                if file.filename and "." in file.filename:
                    ext = file.filename.rsplit(".", 1)[-1].lower()
                    if ext in {"mp4", "webm", "mov"}:
                        file_type = "video"

                original_url = None
                thumbnail_url = None
                width, height = None, None
                duration = None

                if file_type == "image":
                    # 保存原图并生成缩略图
                    original_url, thumbnail_url = (
                        await storage.save_template_image_with_thumbnail(
                            file_content=file_content,
                            owner_admin_id=owner_operator_id,
                            template_id=template.id,
                            extension=ext,
                        )
                    )

                    # 获取图片尺寸
                    try:
                        from PIL import Image

                        img = Image.open(io.BytesIO(file_content))
                        width, height = img.size
                    except Exception:
                        pass
                else:
                    # 保存视频
                    original_url, thumbnail_url, duration = (
                        await storage.save_template_video(
                            file_content=file_content,
                            owner_admin_id=owner_operator_id,
                            template_id=template.id,
                            extension=ext,
                        )
                    )

                logger.info(
                    f"[TemplateUpload] Storage result for file {idx}: "
                    f"original_url={original_url}, thumbnail_url={thumbnail_url}, file_type={file_type}"
                )

                # 保存附件记录
                if original_url:
                    attachment = await TemplateService.add_template_attachment(
                        db,
                        template_id=template.id,
                        owner_operator_id=owner_operator_id,
                        file_type=file_type,
                        file_url=original_url,
                        file_name=file.filename or f"{file_type}_{idx + 1}.{ext}",
                        file_size=len(file_content),
                        sort_order=idx,
                        width=width,
                        height=height,
                        duration=duration,
                        thumbnail_url=thumbnail_url,
                    )
                    logger.info(
                        f"[TemplateUpload] Saved attachment: id={attachment.id if attachment else 'None'}, "
                        f"file_url={original_url}, file_size={len(file_content)}, "
                        f"width={width}, height={height}, thumbnail_url={thumbnail_url}"
                    )
                    saved_count += 1
                    if file_type == "image":
                        image_count += 1
                    else:
                        video_count += 1
                else:
                    logger.error(
                        f"[TemplateUpload] Failed to save file {idx}: "
                        f"storage returned (None, None), filename={file.filename}"
                    )
                    failed_count += 1
            except Exception as e:
                logger.error(
                    f"[TemplateUpload] Exception processing file {idx}: {e}",
                    exc_info=True,
                )
                failed_count += 1

        logger.info(
            f"[TemplateUpload] File processing complete: saved={saved_count}, failed={failed_count}"
        )

        # 更新模板的图片/视频计数
        if image_count > 0 or video_count > 0:
            await TemplateService.update_template(
                db,
                template.id,
                owner_operator_id,
                image_count=image_count,
                video_count=video_count,
            )
            logger.info(
                f"[TemplateUpload] Updated template image_count={image_count}, video_count={video_count} for template_id={template.id}"
            )

    # 加载关联数据并构建响应
    tags = await load_template_tags(db, template.id)
    platform = None
    if template.platform_id:
        platform = await TemplateService.get_template_platform(
            db, template.platform_id, owner_operator_id
        )
    attachments = await TemplateService.list_template_attachments(
        db, template.id, owner_operator_id
    )

    logger.info(
        f"[TemplateUpload] Loaded for response: template_id={template.id}, "
        f"attachments_count={len(attachments)}, tags_count={len(tags)}"
    )

    response_data = build_template_response(
        template, tags, platform, include_owner=True, attachments=attachments
    )

    # 记录响应中的文件信息
    response_attachments = (
        response_data.get("attachments", [])
        if isinstance(response_data, dict)
        else getattr(response_data, "attachments", [])
    )
    if response_attachments:
        for idx, att in enumerate(response_attachments):
            att_file_url = (
                att.get("file_url")
                if isinstance(att, dict)
                else getattr(att, "file_url", None)
            )
            att_thumb_url = (
                att.get("thumbnail_url")
                if isinstance(att, dict)
                else getattr(att, "thumbnail_url", None)
            )
            att_type = (
                att.get("file_type")
                if isinstance(att, dict)
                else getattr(att, "file_type", None)
            )
            logger.info(
                f"[TemplateUpload] Response attachment {idx}: file_url={att_file_url}, "
                f"thumbnail_url={att_thumb_url}, file_type={att_type}"
            )
    else:
        logger.warning(
            f"[TemplateUpload] Response has no attachments: template_id={template.id}"
        )

    logger.info(
        f"[TemplateUpload] Upload completed successfully: template_id={template.id}"
    )
    return success_response(data=response_data, message="创建成功")


@router.get("/categories/{category_id}/stats", response_model=ApiResponse[dict])
async def get_template_category_stats(
    category_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板分类统计信息（模板数量、标签数量）
    """

    from app.models import TemplateTag, TemplateTagRel

    # 统计分类下的标签数量
    tag_count_result = await db.execute(
        select(func.count())
        .select_from(TemplateTag)
        .where(TemplateTag.category_id == category_id)
    )
    tag_count = tag_count_result.scalar() or 0

    # 统计分类下的模板数量（通过标签关联）
    template_count_result = await db.execute(
        select(func.count(func.distinct(TemplateTagRel.template_id)))
        .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
        .where(TemplateTag.category_id == category_id)
    )
    template_count = template_count_result.scalar() or 0

    return success_response(
        data={
            "category_id": category_id,
            "template_count": template_count,
            "tag_count": tag_count,
        },
        message="获取成功",
    )


@router.get("/tags/{tag_id}/stats", response_model=ApiResponse[dict])
async def get_template_tag_stats(
    tag_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取模板标签统计信息（模板数量）
    """

    from app.models import TemplateTagRel

    template_count_result = await db.execute(
        select(func.count())
        .select_from(TemplateTagRel)
        .where(TemplateTagRel.tag_id == tag_id)
    )
    template_count = template_count_result.scalar() or 0

    return success_response(
        data={
            "tag_id": tag_id,
            "template_count": template_count,
        },
        message="获取成功",
    )
