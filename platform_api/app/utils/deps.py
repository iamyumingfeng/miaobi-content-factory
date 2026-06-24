"""
依赖注入模块 (deps.py)

提供 FastAPI 依赖注入函数。

Author: Claude Code
Date: 2025
"""

from typing import AsyncGenerator, Optional, Tuple
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.database import get_async_db
from app.core.security import decode_access_token
from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.models.super_admin import SuperAdmin
from app.models.operator import Operator
from app.models.sub_user import SubUser

# HTTP Bearer 安全方案
security = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    从 Bearer Token 中获取 payload（不抛出异常）

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        Optional[dict]: Token payload 或 None
    """
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        return payload
    except JWTError:
        return None


async def get_token_payload_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """
    从 Bearer Token 中获取 payload（要求必须有效）

    同时验证用户状态，被禁用的用户将被拒绝访问。

    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话

    Returns:
        dict: Token payload

    Raises:
        AuthenticationError: 未提供 token 或 token 无效
        AccountLockedError: 账号已被禁用
    """
    from sqlalchemy import select
    from app.core.exceptions import AccountLockedError

    if not credentials:
        raise AuthenticationError(message="未提供认证令牌")

    try:
        payload = decode_access_token(credentials.credentials)
        if not payload:
            raise InvalidTokenError()
        
        # 检查用户状态是否被禁用
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if user_id and user_type:
            user_status = None
            if user_type == "super_admin":
                result = await db.execute(select(SuperAdmin.status).where(SuperAdmin.id == int(user_id)))
                user_status = result.scalar_one_or_none()
            elif user_type == "operator":
                result = await db.execute(select(Operator.status).where(Operator.id == int(user_id)))
                user_status = result.scalar_one_or_none()
            elif user_type == "sub_user":
                result = await db.execute(select(SubUser.status).where(SubUser.id == int(user_id)))
                user_status = result.scalar_one_or_none()
            
            if user_status == "disabled":
                raise AccountLockedError("账号已被禁用")
        
        return payload
    except JWTError:
        raise InvalidTokenError()


async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    payload: dict = Depends(get_token_payload_required),
) -> Tuple[SuperAdmin | Operator | SubUser, str]:
    """
    获取当前用户（通用）

    根据 token 中的 user_type 获取对应的用户对象。

    Returns:
        Tuple[用户对象, 用户类型]: (用户实例, "super_admin" | "operator" | "sub_user")

    Raises:
        UserNotFoundError: 用户不存在
        AccountLockedError: 账号已被禁用
    """
    from sqlalchemy import select
    from app.core.exceptions import AccountLockedError

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    if not user_id or not user_type:
        raise InvalidTokenError()

    user = None
    if user_type == "super_admin":
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == int(user_id)))
        user = result.scalar_one_or_none()
        # 检查超级管理员状态
        if user and user.status == "disabled":
            raise AccountLockedError("账号已被禁用")
    elif user_type == "operator":
        result = await db.execute(select(Operator).where(Operator.id == int(user_id)))
        user = result.scalar_one_or_none()
        # 检查创作管理员状态
        if user and user.status == "disabled":
            raise AccountLockedError("账号已被禁用")
    elif user_type == "sub_user":
        result = await db.execute(select(SubUser).where(SubUser.id == int(user_id)))
        user = result.scalar_one_or_none()
        # 检查创作者状态
        if user and user.status == "disabled":
            raise AccountLockedError("账号已被禁用")

    if not user:
        raise UserNotFoundError()

    return user, user_type


async def get_current_super_admin(
    db: AsyncSession = Depends(get_async_db),
    payload: dict = Depends(get_token_payload_required),
) -> SuperAdmin:
    """
    获取当前超级管理员

    Returns:
        SuperAdmin: 超级管理员对象

    Raises:
        AuthorizationError: 用户不是超级管理员
    """
    from sqlalchemy import select
    from app.core.exceptions import AuthorizationError

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    if user_type != "super_admin":
        raise AuthorizationError(message="需要超级管理员权限")

    result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError()

    return user


async def get_super_admin_required(
    payload: dict = Depends(get_token_payload_required),
) -> dict:
    """
    验证当前用户是否为超级管理员（仅验证权限，不返回用户对象）

    用于需要超级管理员权限的 API 接口，返回 token payload。

    Returns:
        dict: Token payload

    Raises:
        AuthorizationError: 用户不是超级管理员
    """
    from app.core.exceptions import AuthorizationError

    user_type = payload.get("user_type")

    if user_type != "super_admin":
        raise AuthorizationError(message="需要超级管理员权限")

    return payload


async def get_current_operator(
    db: AsyncSession = Depends(get_async_db),
    payload: dict = Depends(get_token_payload_required),
) -> Operator:
    """
    获取当前创作管理员

    Returns:
        Operator: 创作管理员对象

    Raises:
        AuthorizationError: 用户不是创作管理员
    """
    from sqlalchemy import select
    from app.core.exceptions import AuthorizationError

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    if user_type not in ["super_admin", "operator"]:
        raise AuthorizationError(message="需要创作管理员权限")

    if user_type == "super_admin":
        # 超级管理员模拟创作管理员（用于调试）
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == int(user_id)))
        admin = result.scalar_one_or_none()
        if not admin:
            raise UserNotFoundError()
        # 返回一个临时的 Operator 对象（仅用于权限判断）
        return Operator(
            id=admin.id,
            userid=admin.userid,
            nickname=admin.nickname,
            hashed_password=admin.hashed_password,
            is_active=True,
            created_at=admin.created_at,
        )

    result = await db.execute(select(Operator).where(Operator.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError()

    return user


async def get_current_sub_user(
    db: AsyncSession = Depends(get_async_db),
    payload: dict = Depends(get_token_payload_required),
) -> SubUser:
    """
    获取当前创作者

    Returns:
        SubUser: 创作者对象

    Raises:
        AuthorizationError: 用户不是创作者
    """
    from sqlalchemy import select
    from app.core.exceptions import AuthorizationError

    user_id = payload.get("sub")
    user_type = payload.get("user_type")

    if user_type != "sub_user":
        raise AuthorizationError(message="需要创作者权限")

    result = await db.execute(select(SubUser).where(SubUser.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError()

    return user


async def get_optional_current_user(
    db: AsyncSession = Depends(get_async_db),
    payload: Optional[dict] = Depends(get_token_payload),
) -> Optional[Tuple[SuperAdmin | Operator | SubUser, str]]:
    """
    尝试获取当前用户（可选，不强制认证）

    Returns:
        Optional[Tuple[用户对象, 用户类型]]: 用户和类型或 None
    """
    if not payload:
        return None

    try:
        return await get_current_user(db, payload)
    except Exception:
        return None


async def get_websocket_user(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db),
) -> Optional[Tuple[SuperAdmin | Operator | SubUser, str]]:
    """
    从 WebSocket 连接中获取用户

    Args:
        websocket: WebSocket 连接
        db: 数据库会话

    Returns:
        Optional[Tuple[用户对象, 用户类型]]: 用户和类型或 None
    """
    from sqlalchemy import select

    # 从查询参数或 header 中获取 token
    token = websocket.query_params.get("token")
    if not token:
        # 尝试从 Authorization header 获取
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return None

    try:
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        user_type = payload.get("user_type")

        if not user_id or not user_type:
            return None

        user = None
        if user_type == "super_admin":
            result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == int(user_id)))
            user = result.scalar_one_or_none()
        elif user_type == "operator":
            result = await db.execute(select(Operator).where(Operator.id == int(user_id)))
            user = result.scalar_one_or_none()
        elif user_type == "sub_user":
            result = await db.execute(select(SubUser).where(SubUser.id == int(user_id)))
            user = result.scalar_one_or_none()

        if user:
            return user, user_type
        return None
    except Exception:
        return None
