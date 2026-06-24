"""
认证 API 路由 (auth.py)

Author: Claude Code
Date: 2025
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.token_service import TokenService
from app.core.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    OldPasswordError,
    PasswordSameError,
    UseridNotFoundError,
    PasswordIncorrectError,
    AccountLockedError,
)
from app.utils.response import success_response, ApiResponse
from app.utils.deps import get_token_payload_required
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserInfo,
    ChangePasswordRequest,
    UpdateDisplayNameRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
)

router = APIRouter()


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    账号密码登录

    支持超级管理员、创作管理员、创作者三种角色登录。
    """
    try:
        # 认证用户（内部已更新登录状态和最后登录时间）
        user, user_type, _ = await AuthService.authenticate_user(
            db, request.userid, request.password
        )

        # 生成令牌并创建登录响应
        login_response = await TokenService.create_login_response(
            db=db,
            user=user,
            user_type=user_type
        )

        return success_response(data=login_response, message="登录成功")

    except (UseridNotFoundError, PasswordIncorrectError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )


@router.post("/refresh", response_model=ApiResponse[RefreshTokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    使用 refresh token 刷新 access token

    当 access token 过期时，可以使用 refresh token 获取新的 access token，
    而无需用户重新登录。
    """
    try:
        refresh_response, error = await TokenService.refresh_access_token(
            db=db,
            refresh_token_str=request.refresh_token
        )

        if error or not refresh_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error or "无效的 refresh token"
            )

        return success_response(data=refresh_response, message="刷新成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/change-password", response_model=ApiResponse[dict])
async def change_password(
    request: ChangePasswordRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    修改密码（已登录）
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    try:
        if request.old_password == request.new_password:
            raise PasswordSameError()

        await AuthService.change_password(
            db,
            user_id=user_id,
            user_type=user_type,
            old_password=request.old_password,
            new_password=request.new_password,
        )

        return success_response(message="密码修改成功，请重新登录")

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    except OldPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    except PasswordSameError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与原密码相同"
        )


@router.post("/update-display-name", response_model=ApiResponse[dict])
async def update_display_name(
    request: UpdateDisplayNameRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    更新自定义昵称（已登录）
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    try:
        await AuthService.update_display_name(
            db,
            user_id=user_id,
            user_type=user_type,
            display_name=request.display_name,
        )

        return success_response(message="昵称更新成功")

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.get("/me", response_model=ApiResponse[UserInfo])
async def get_current_user(
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取当前登录用户信息
    """
    from app.services.auth_service import AuthService

    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    user = await AuthService.get_user_by_id(db, user_id, user_type)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user_info = UserInfo(
        id=user.id,
        userid=user.userid,
        nickname=getattr(user, "nickname", None),
        display_name=getattr(user, "display_name", None),
        role=user_type,
    )

    return success_response(data=user_info, message="获取成功")


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    payload: dict = Depends(get_token_payload_required),
    db: AsyncSession = Depends(get_async_db),
):
    """
    退出登录

    会将用户状态标记为离线，并撤销对应的 refresh token。
    """
    user_id = int(payload.get("sub"))
    user_type = payload.get("user_type")

    # 调用 TokenService 处理登出逻辑
    await TokenService.logout(
        db=db,
        user_id=user_id,
        user_type=user_type,
        refresh_token_str=request.refresh_token
    )

    return success_response(message="退出成功")
