"""
API v1 依赖模块

包含路由依赖函数，如权限检查等。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import decode_access_token
from app.models.all_user import AllUser
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> AllUser:
    """
    获取当前登录用户

    验证 JWT 令牌并返回对应用户。
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_ERROR", "message": "未提供认证令牌"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "无效的令牌"},
        )

    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "令牌中缺少用户信息"},
        )

    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "用户不存在"},
        )

    return user


async def require_super_admin(
    current_user: AllUser = Depends(get_current_user),
) -> AllUser:
    """
    需要超级管理员权限
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SUPER_ADMIN_REQUIRED", "message": "需要超级管理员权限"},
        )
    return current_user


async def require_operator(
    current_user: AllUser = Depends(get_current_user),
) -> AllUser:
    """
    需要创作管理员权限（超级管理员也允许）

    用于素材库、模板库等平台级管理功能。
    """
    if current_user.role not in ["super_admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "OPERATOR_REQUIRED", "message": "需要创作管理员权限"},
        )
    return current_user


async def require_sub_user(
    current_user: AllUser = Depends(get_current_user),
) -> AllUser:
    """
    需要创作者权限

    注意：创作者功能通常由其所属的管理员代理操作。
    """
    if current_user.role != "sub_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "权限不足"},
        )
    return current_user


async def require_admin_or_owner(
    current_user: AllUser = Depends(get_current_user),
) -> AllUser:
    """
    需要管理员权限（超级管理员或创作管理员）

    与 require_operator 相同，用于管理员功能。
    """
    return await require_operator(current_user)
