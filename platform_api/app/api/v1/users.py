"""
用户管理 API 路由 (users.py)

Author: Claude Code
Date: 2025
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_async_db
from app.utils.response import success_response, ApiResponse
from app.schemas import PaginatedResponse
from app.utils.deps import get_token_payload_required, get_current_super_admin
from app.services.user_service import UserService
from app.schemas.users import (
    SuperAdminCreate,
    SuperAdminUpdate,
    SuperAdminResponse,
    OperatorCreate,
    OperatorUpdate,
    OperatorResponse,
    SubUserCreate,
    SubUserUpdate,
    SubUserResponse,
    UserTagCreate,
    UserTagUpdate,
    UserTagResponse,
    UserTransferRequest,
    ResetPasswordRequest,
)
from app.core.exceptions import UserNotFoundError

router = APIRouter()


# ============================================
# 超级创作管理员（仅超级管理员可访问）
# ============================================
@router.get("/super-admins", response_model=ApiResponse[PaginatedResponse[SuperAdminResponse]])
async def list_super_admins(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取超级管理员列表
    """
    items, total = await UserService.list_super_admins(
        db, page=page, limit=limit, status=status
    )
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


@router.post("/super-admins", response_model=ApiResponse[SuperAdminResponse])
async def create_super_admin(
    request: SuperAdminCreate,
    current_admin: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建超级管理员
    """
    created_by = current_admin.id
    super_admin = await UserService.create_super_admin(
        db,
        userid=request.userid,
        nickname=request.nickname,
        password=request.password,
        created_by=created_by,
    )
    return success_response(data=super_admin, message="创建成功")


@router.get("/super-admins/{id}", response_model=ApiResponse[SuperAdminResponse])
async def get_super_admin(
    id: int,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取超级管理员详情
    """
    super_admin = await UserService.get_super_admin(db, id)
    if not super_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="超级管理员不存在"
        )
    return success_response(data=super_admin, message="获取成功")


@router.put("/super-admins/{id}", response_model=ApiResponse[SuperAdminResponse])
async def update_super_admin(
    id: int,
    request: SuperAdminUpdate,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新超级管理员
    """
    try:
        super_admin = await UserService.update_super_admin(
            db,
            super_admin_id=id,
            **request.model_dump(exclude_unset=True),
        )
        return success_response(data=super_admin, message="更新成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/super-admins/{id}")
async def delete_super_admin(
    id: int,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除超级管理员
    """
    try:
        await UserService.delete_super_admin(db, id)
        return success_response(data=None, message="删除成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# 创作创作管理员（超级管理员和创作管理员可访问）
# ============================================
@router.get("/operators", response_model=ApiResponse[PaginatedResponse[OperatorResponse]])
async def list_operators(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创作管理员列表

    - 超级管理员：可查看所有创作管理员
    - 创作管理员：只能看到自己（不适用于此场景，返回空或仅自己）
    """
    user_type = payload.get("user_type")

    # 超级管理员查看所有创作管理员，创作管理员只能看到自己
    if user_type == "operator":
        current_user_id = int(payload.get("sub"))
        created_by = current_user_id  # 创作管理员只看自己
    else:
        created_by = None  # 超级管理员查看所有

    items, total = await UserService.list_operators(
        db, page=page, limit=limit, created_by=created_by, status=status, keyword=keyword
    )
    # 手动将 Operator 模型转换为 OperatorResponse Pydantic 模型
    response_items = [OperatorResponse.model_validate(item) for item in items]
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


@router.post("/operators", response_model=ApiResponse[OperatorResponse])
async def create_operator(
    request: OperatorCreate,
    current_admin: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建创作管理员
    """
    created_by = current_admin.id
    operator = await UserService.create_operator(
        db,
        nickname=request.nickname,
        password=request.password,
        created_by=created_by,
        display_name=request.display_name,
        user_positioning=request.user_positioning,
        user_category=request.user_category,
    )
    return success_response(data=operator, message="创建成功")


@router.get("/operators/{id}", response_model=ApiResponse[OperatorResponse])
async def get_operator(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创作管理员详情
    """
    operator = await UserService.get_operator(db, id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="创作管理员不存在"
        )
    return success_response(data=operator, message="获取成功")


@router.put("/operators/{id}", response_model=ApiResponse[OperatorResponse])
async def update_operator(
    id: int,
    request: OperatorUpdate,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新创作管理员
    """
    try:
        operator = await UserService.update_operator(
            db,
            operator_id=id,
            **request.model_dump(exclude_unset=True),
        )
        return success_response(data=operator, message="更新成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/operators/{id}")
async def delete_operator(
    id: int,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除创作管理员
    """
    try:
        await UserService.delete_operator(db, id)
        return success_response(data=None, message="删除成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/operators/{id}/reset-password")
async def reset_operator_password(
    id: int,
    request: ResetPasswordRequest,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重置创作管理员密码（超级管理员）
    """
    try:
        await UserService.reset_operator_password(
            db,
            operator_id=id,
            new_password=request.new_password,
        )
        return success_response(data=None, message="密码重置成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/super-admins/{id}/reset-password")
async def reset_super_admin_password(
    id: int,
    request: ResetPasswordRequest,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重置超级管理员密码
    """
    try:
        await UserService.reset_super_admin_password(
            db,
            super_admin_id=id,
            new_password=request.new_password,
        )
        return success_response(data=None, message="密码重置成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/operators/transfer")
async def transfer_operators(
    request: UserTransferRequest,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    转移创作管理员的创作者（超级管理员）
    """
    count = await UserService.transfer_sub_users(
        db,
        sub_user_ids=request.user_ids,
        from_operator_id=request.from_operator_id,
        to_operator_id=request.to_operator_id,
    )
    return success_response(data={"transferred_count": count}, message=f"成功转移 {count} 个创作者")


# ============================================
# 创作员管理（创作管理员可访问）
# ============================================
@router.get("/sub-users", response_model=ApiResponse[PaginatedResponse[SubUserResponse]])
async def list_sub_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    tag_id: Optional[int] = Query(None, description="标签筛选"),
    operator_id: Optional[int] = Query(None, description="创作管理员筛选（超级管理员专用）"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创作者列表

    超级管理员可以查看所有创作者，并通过 operator_id 筛选特定创作管理员的创作者。
    创作管理员只能查看自己的创作者。
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if is_super_admin:
        # 超级管理员：可以查看所有创作者，或通过 operator_id 筛选
        owner_operator_id = operator_id  # 可选，None 表示全部
    else:
        # 创作管理员：只能查看自己的创作者
        owner_operator_id = int(payload.get("sub"))

    items, total = await UserService.list_sub_users(
        db,
        owner_operator_id=owner_operator_id,
        page=page,
        limit=limit,
        status=status,
        tag_id=tag_id,
        keyword=keyword,
    )
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


@router.post("/sub-users", response_model=ApiResponse[SubUserResponse])
async def create_sub_user(
    request: SubUserCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建创作者
    """
    owner_operator_id = int(payload.get("sub"))
    created_by = owner_operator_id

    sub_user = await UserService.create_sub_user(
        db,
        owner_operator_id=owner_operator_id,
        nickname=request.nickname,
        password=request.password,
        created_by=created_by,
        display_name=request.display_name,
        fan_profile=request.fan_profile,
        user_positioning=request.user_positioning,
        user_category=request.user_category,
        content_style=request.content_style,
        account_type=request.account_type,
        tag_ids=request.tag_ids,
    )
    return success_response(data=sub_user, message="创建成功")


@router.get("/sub-users/{id}", response_model=ApiResponse[SubUserResponse])
async def get_sub_user(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取创作者详情
    """
    owner_operator_id = int(payload.get("sub"))
    sub_user = await UserService.get_sub_user(
        db, id, owner_operator_id=owner_operator_id
    )
    if not sub_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="创作者不存在"
        )
    return success_response(data=sub_user, message="获取成功")


@router.put("/sub-users/{id}", response_model=ApiResponse[SubUserResponse])
async def update_sub_user(
    id: int,
    request: SubUserUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新创作者
    超级管理员可以更新任何创作者，创作管理员只能更新自己的创作者
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if is_super_admin:
        # 超级管理员：不限制 owner_operator_id
        owner_operator_id = None
    else:
        # 创作管理员：只能更新自己的创作者
        owner_operator_id = int(payload.get("sub"))

    try:
        sub_user = await UserService.update_sub_user(
            db,
            sub_user_id=id,
            owner_operator_id=owner_operator_id,
            **request.model_dump(exclude_unset=True),
        )
        return success_response(data=sub_user, message="更新成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/sub-users/{id}")
async def delete_sub_user(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除创作者
    """
    owner_operator_id = int(payload.get("sub"))
    try:
        await UserService.delete_sub_user(db, id, owner_operator_id)
        return success_response(data=None, message="删除成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/sub-users/{id}/reset-password")
async def reset_sub_user_password(
    id: int,
    request: ResetPasswordRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    重置创作者密码（创作管理员）
    """
    owner_operator_id = int(payload.get("sub"))
    try:
        sub_user = await UserService.reset_sub_user_password(
            db,
            sub_user_id=id,
            new_password=request.new_password,
            owner_operator_id=owner_operator_id,
        )
        return success_response(data=None, message="密码重置成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/sub-users/transfer")
async def transfer_sub_users(
    request: UserTransferRequest,
    _: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    转移创作者到其他创作管理员（超级管理员）
    """
    try:
        count = await UserService.transfer_sub_users(
            db,
            sub_user_ids=request.user_ids,
            from_operator_id=request.from_operator_id,
            to_operator_id=request.to_operator_id,
        )
        return success_response(data={"transferred_count": count}, message=f"成功转移 {count} 个创作者")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================
# 用户标签管理
# ============================================
@router.get("/tags", response_model=ApiResponse[list[UserTagResponse]])
async def list_user_tags(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    operator_id: Optional[int] = Query(None, description="创作管理员ID（超级管理员专用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取用户标签列表

    超级管理员可以通过 operator_id 参数查看特定创作管理员的标签。
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if is_super_admin and operator_id:
        # 超级管理员查看指定创作管理员的标签
        created_by = operator_id
    else:
        # 普通用户查看自己的标签
        created_by = int(payload.get("sub"))

    tags = await UserService.list_user_tags(
        db, tag_type=tag_type, created_by=created_by
    )
    return success_response(data=tags, message="获取成功")


@router.post("/tags", response_model=ApiResponse[UserTagResponse])
async def create_user_tag(
    request: UserTagCreate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    创建用户标签
    """
    created_by = int(payload.get("sub"))
    tag = await UserService.create_user_tag(
        db,
        name=request.name,
        tag_type=request.tag_type,
        created_by=created_by,
        description=request.description,
        color=request.color,
    )
    return success_response(data=tag, message="创建成功")


@router.put("/tags/{id}", response_model=ApiResponse[UserTagResponse])
async def update_user_tag(
    id: int,
    request: UserTagUpdate,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新用户标签
    """
    created_by = int(payload.get("sub"))
    try:
        tag = await UserService.update_user_tag(
            db,
            tag_id=id,
            created_by=created_by,
            **request.model_dump(exclude_unset=True),
        )
        return success_response(data=tag, message="更新成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/tags/{id}")
async def delete_user_tag(
    id: int,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    删除用户标签
    """
    created_by = int(payload.get("sub"))
    try:
        await UserService.delete_user_tag(db, id, created_by)
        return success_response(data=None, message="删除成功")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/tags/counts", response_model=ApiResponse[dict])
async def get_tag_counts(
    operator_id: Optional[int] = Query(None, description="创作管理员ID（超级管理员专用）"),
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取每个标签下的创作者数量统计

    超级管理员可以通过 operator_id 参数查看特定创作管理员的标签统计。
    """
    user_type = payload.get("user_type")
    is_super_admin = user_type == "super_admin"

    if is_super_admin and operator_id:
        # 超级管理员查看指定创作管理员的标签统计
        owner_operator_id = operator_id
    else:
        # 普通用户查看自己的标签统计
        owner_operator_id = int(payload.get("sub"))

    counts = await UserService.count_sub_users_by_tag(
        db, owner_operator_id=owner_operator_id
    )
    return success_response(data=counts, message="获取成功")
