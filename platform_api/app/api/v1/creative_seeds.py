"""
创意种子库管理 API 路由 (creative_seeds.py)

提供创意种子的增删改查接口，支持创作管理员自定义管理开头模式、情感基调、结尾模式等创意种子。

Author: Claude Code
Date: 2026
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models import CreativeSeed, Operator
from app.schemas import PaginatedResponse
from app.schemas.creative_seed import (CreativeSeedCreate,
                                       CreativeSeedGroupResponse,
                                       CreativeSeedResponse,
                                       CreativeSeedSelectResponse,
                                       CreativeSeedUpdate)
from app.utils.deps import get_token_payload_required
from app.utils.response import ApiResponse, success_response

router = APIRouter()
logger = logging.getLogger(__name__)


# 种子类型说明
SEED_TYPE_INFO = {
    "opening": {
        "label": "开头模式",
        "description": "控制文案开头的风格，如反常识、自嘲、悬念等",
    },
    "emotion": {
        "label": "情感基调",
        "description": "控制文案的情感表达，如轻松吐槽、真诚分享等",
    },
    "ending": {
        "label": "结尾模式",
        "description": "控制文案的收尾方式，如求建议、留悬念、共鸣式等",
    },
}

# 品类选项（20个品类）
CATEGORY_OPTIONS = [
    "通用",
    "美妆护肤",
    "服饰穿搭",
    "美食探店",
    "家居生活",
    "母婴育儿",
    "数码3C",
    "旅行风景",
    "运动健身",
    "宠物萌宠",
    "教育学习",
    "职场成长",
    "情感心理",
    "娱乐追剧",
    "游戏二次元",
    "汽车出行",
    "珠宝首饰",
    "图书文具",
    "大健康养生",
    "本地生活",
]


def _build_seed_response(seed: CreativeSeed, owner_name: Optional[str] = None) -> dict:
    """构建创意种子响应数据"""
    import json

    return {
        "id": seed.id,
        "name": seed.name,
        "seed_type": seed.seed_type,
        "template": seed.template,
        "description": seed.description,
        "forbidden_patterns": (
            json.loads(seed.forbidden_patterns) if seed.forbidden_patterns else []
        ),
        "example_phrases": (
            json.loads(seed.example_phrases) if seed.example_phrases else []
        ),
        "avoid_phrases": json.loads(seed.avoid_phrases) if seed.avoid_phrases else [],
        "category": seed.category,
        "status": seed.status,
        "is_system": seed.is_system,
        "owner_operator_id": seed.owner_operator_id,
        "owner_operator_name": owner_name,
        "use_count": seed.use_count,
        "success_rate": seed.success_rate,
        "created_at": seed.created_at,
        "updated_at": seed.updated_at,
    }


async def _get_operator_name(db: AsyncSession, operator_id: int) -> Optional[str]:
    """获取创作管理员名称"""
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()
    if operator:
        return getattr(operator, "nickname", None) or getattr(
            operator, "display_name", None
        )
    return None


# ============================================
# 类型枚举
# ============================================
@router.get("/types", response_model=ApiResponse[dict])
async def get_seed_types(
    payload: dict = Depends(get_token_payload_required),
):
    """返回种子类型枚举和品类选项"""
    return success_response(
        data={
            "seed_types": SEED_TYPE_INFO,
            "categories": CATEGORY_OPTIONS,
        },
        message="获取成功",
    )


# ============================================
# 分组查询（用于下拉选择）
# ============================================
@router.get("/grouped", response_model=ApiResponse[CreativeSeedGroupResponse])
async def get_seeds_grouped(
    category: Optional[str] = Query(None, description="品类筛选"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取按类型分组的种子列表（用于下拉选择）

    返回所有启用的种子，按类型分组
    """
    current_user_id = int(payload.get("sub"))

    conditions = [
        CreativeSeed.status == "enabled",
        or_(
            CreativeSeed.owner_operator_id == current_user_id,
            CreativeSeed.is_system == True,
        ),
    ]

    if category and category != "通用":
        conditions.append(
            or_(
                CreativeSeed.category == category,
                CreativeSeed.category == "通用",
            )
        )

    query = (
        select(CreativeSeed)
        .where(and_(*conditions))
        .order_by(CreativeSeed.is_system.desc(), CreativeSeed.use_count.desc())
    )
    result = await db.execute(query)
    seeds = list(result.scalars().all())

    opening = [
        CreativeSeedSelectResponse(
            id=s.id,
            name=s.name,
            seed_type=s.seed_type,
            template=s.template,
            category=s.category,
        )
        for s in seeds
        if s.seed_type == "opening"
    ]
    emotion = [
        CreativeSeedSelectResponse(
            id=s.id,
            name=s.name,
            seed_type=s.seed_type,
            template=s.template,
            category=s.category,
        )
        for s in seeds
        if s.seed_type == "emotion"
    ]
    ending = [
        CreativeSeedSelectResponse(
            id=s.id,
            name=s.name,
            seed_type=s.seed_type,
            template=s.template,
            category=s.category,
        )
        for s in seeds
        if s.seed_type == "ending"
    ]

    return success_response(
        data=CreativeSeedGroupResponse(
            opening=opening,
            emotion=emotion,
            ending=ending,
        ),
        message="获取成功",
    )


# ============================================
# CRUD 操作
# ============================================
@router.get("", response_model=ApiResponse[PaginatedResponse[CreativeSeedResponse]])
async def list_creative_seeds(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    seed_type: Optional[str] = Query(None, description="种子类型筛选"),
    category: Optional[str] = Query(None, description="品类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创意种子列表

    - 超级管理员：可查看所有种子
    - 创作管理员：可查看自己的种子和系统种子
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    # 构建查询条件
    conditions = [
        or_(
            CreativeSeed.owner_operator_id == current_user_id,
            CreativeSeed.is_system == True,
        )
    ]

    if seed_type:
        conditions.append(CreativeSeed.seed_type == seed_type)
    if category:
        conditions.append(CreativeSeed.category == category)
    if status:
        conditions.append(CreativeSeed.status == status)
    if keyword:
        conditions.append(
            or_(
                CreativeSeed.name.ilike(f"%{keyword}%"),
                CreativeSeed.template.ilike(f"%{keyword}%"),
                CreativeSeed.description.ilike(f"%{keyword}%"),
            )
        )

    # 查询总数
    count_query = (
        select(func.count()).select_from(CreativeSeed).where(and_(*conditions))
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 查询数据
    query = (
        select(CreativeSeed)
        .where(and_(*conditions))
        .order_by(CreativeSeed.is_system.desc(), CreativeSeed.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    seeds = list(result.scalars().all())

    response_items = []
    for seed in seeds:
        owner_name = None
        if seed.owner_operator_id:
            owner_name = await _get_operator_name(db, seed.owner_operator_id)
        response_items.append(_build_seed_response(seed, owner_name))

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


@router.get("/{seed_id}", response_model=ApiResponse[dict])
async def get_creative_seed(
    seed_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创意种子详情

    - 超级管理员：可查看所有种子
    - 创作管理员：可查看自己的种子和系统种子
    """
    current_user_id = int(payload.get("sub"))

    query = select(CreativeSeed).where(
        and_(
            CreativeSeed.id == seed_id,
            or_(
                CreativeSeed.owner_operator_id == current_user_id,
                CreativeSeed.is_system == True,
            ),
        )
    )
    result = await db.execute(query)
    seed = result.scalar_one_or_none()

    if not seed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="种子不存在")

    owner_name = None
    if seed.owner_operator_id:
        owner_name = await _get_operator_name(db, seed.owner_operator_id)
    return success_response(
        data=_build_seed_response(seed, owner_name), message="获取成功"
    )


@router.post("", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_creative_seed(
    request: CreativeSeedCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建创意种子

    - 仅创作管理员可创建种子
    - 创建的种子默认 is_system=False
    """
    user_type = payload.get("user_type")
    if user_type == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员不能创建创意种子，请由创作管理员操作",
        )

    current_user_id = int(payload.get("sub"))

    # 检查同名种子是否存在
    existing = await db.execute(
        select(CreativeSeed).where(
            CreativeSeed.owner_operator_id == current_user_id,
            CreativeSeed.name == request.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在同名种子",
        )

    import json

    seed = CreativeSeed(
        name=request.name,
        seed_type=request.seed_type.value,
        template=request.template,
        description=request.description,
        forbidden_patterns=(
            json.dumps(request.forbidden_patterns)
            if request.forbidden_patterns
            else None
        ),
        example_phrases=(
            json.dumps(request.example_phrases) if request.example_phrases else None
        ),
        avoid_phrases=(
            json.dumps(request.avoid_phrases) if request.avoid_phrases else None
        ),
        category=request.category,
        status=request.status.value,
        is_system=False,
        owner_operator_id=current_user_id,
    )
    db.add(seed)
    await db.commit()
    await db.refresh(seed)

    logger.info(
        "[CreativeSeed] 创建种子成功 | id=%s | name=%s | type=%s | owner=%s",
        seed.id,
        seed.name,
        seed.seed_type,
        current_user_id,
    )

    return success_response(data=_build_seed_response(seed), message="创建成功")


@router.put("/{seed_id}", response_model=ApiResponse[dict])
async def update_creative_seed(
    seed_id: int,
    request: CreativeSeedUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新创意种子

    - 超级管理员：可更新所有种子
    - 创作管理员：只能更新自己的种子（系统种子仅可修改状态）
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    query = select(CreativeSeed).where(CreativeSeed.id == seed_id)
    if not is_super_admin:
        query = query.where(CreativeSeed.owner_operator_id == current_user_id)

    result = await db.execute(query)
    seed = result.scalar_one_or_none()

    if not seed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="种子不存在")

    import json
    from datetime import datetime

    # 系统种子：创作管理员只能修改状态，超级管理员可修改所有字段
    if seed.is_system and not is_super_admin:
        if request.status:
            seed.status = request.status.value
    else:
        # 非系统种子或超级管理员可以修改所有属性
        if request.name is not None:
            # 检查同名
            existing = await db.execute(
                select(CreativeSeed).where(
                    CreativeSeed.owner_operator_id == seed.owner_operator_id,
                    CreativeSeed.name == request.name,
                    CreativeSeed.id != seed_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="已存在同名种子",
                )
            seed.name = request.name
        if request.seed_type is not None:
            seed.seed_type = request.seed_type.value
        if request.template is not None:
            seed.template = request.template
        if request.description is not None:
            seed.description = request.description
        if request.forbidden_patterns is not None:
            seed.forbidden_patterns = json.dumps(request.forbidden_patterns)
        if request.example_phrases is not None:
            seed.example_phrases = json.dumps(request.example_phrases)
        if request.avoid_phrases is not None:
            seed.avoid_phrases = json.dumps(request.avoid_phrases)
        if request.category is not None:
            seed.category = request.category
        if request.status is not None:
            seed.status = request.status.value

    seed.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(seed)

    logger.info("[CreativeSeed] 更新种子成功 | id=%s | name=%s", seed.id, seed.name)

    owner_name = None
    if seed.owner_operator_id:
        owner_name = await _get_operator_name(db, seed.owner_operator_id)
    return success_response(
        data=_build_seed_response(seed, owner_name), message="更新成功"
    )


@router.delete("/{seed_id}")
async def delete_creative_seed(
    seed_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除创意种子

    - 超级管理员：可删除所有种子（包括系统种子）
    - 创作管理员：只能删除自己的种子（系统种子不可删除）
    """
    current_user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    query = select(CreativeSeed).where(CreativeSeed.id == seed_id)
    if not is_super_admin:
        query = query.where(CreativeSeed.owner_operator_id == current_user_id)

    result = await db.execute(query)
    seed = result.scalar_one_or_none()

    if not seed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="种子不存在")

    # 非超级管理员不能删除系统种子
    if seed.is_system and not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统种子不可删除",
        )

    await db.delete(seed)
    await db.commit()

    logger.info("[CreativeSeed] 删除种子成功 | id=%s | name=%s", seed.id, seed.name)

    return success_response(message="删除成功")


@router.post("/{seed_id}/increment-use")
async def increment_seed_use_count(
    seed_id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    增加种子使用次数

    在文案生成成功后调用，记录使用次数
    """
    seed = await db.get(CreativeSeed, seed_id)
    if not seed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="种子不存在")

    seed.use_count += 1
    await db.commit()

    return success_response(message="记录成功")
