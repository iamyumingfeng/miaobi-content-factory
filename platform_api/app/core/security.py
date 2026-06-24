"""
安全工具模块 (security.py)

提供密码哈希、JWT 令牌生成和验证等安全功能。

Dependencies:
    - bcrypt: 密码哈希
    - python-jose: JWT 处理
    - app.core.config: 配置管理

Author: Claude Code
Date: 2025
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import bcrypt
from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()

# Refresh token 有效期（7天）
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================
# 密码相关函数
# ============================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        bool: 密码正确返回 True
    """
    # 确保密码不超过72字节（bcrypt限制）
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    # 确保密码不超过72字节（bcrypt限制）
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# ============================================
# JWT 令牌相关函数
# ============================================
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 过期时间增量，不传则使用默认配置

    Returns:
        str: JWT 令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return encoded_jwt


def create_refresh_token(
    user_id: int, user_type: str, userid: str, expires_delta: Optional[timedelta] = None
) -> Tuple[str, str, datetime]:
    """
    创建刷新令牌

    Args:
        user_id: 用户数据库 ID
        user_type: 用户类型
        userid: 用户登录 ID
        expires_delta: 过期时间增量，不传则使用默认配置

    Returns:
        Tuple[str, str, datetime]: (refresh_token, jti, expires_at)
    """
    jti = secrets.token_urlsafe(32)

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(user_id),
        "user_type": user_type,
        "userid": userid,
        "jti": jti,
        "type": "refresh",
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return encoded_jwt, jti, expire


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证访问令牌

    Args:
        token: JWT 令牌字符串

    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，无效返回 None
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    验证访问令牌并返回数据

    Args:
        token: JWT 令牌字符串

    Returns:
        Tuple[bool, Optional[Dict]]: (是否有效, 解码后的数据)
    """
    payload = decode_access_token(token)
    if payload is None:
        return False, None

    # 检查过期时间
    exp = payload.get("exp")
    if exp is None:
        return False, None

    if datetime.utcnow() > datetime.fromtimestamp(exp):
        return False, None

    return True, payload


def refresh_access_token(
    refresh_token: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    使用 refresh token 刷新 access token

    Args:
        refresh_token: Refresh Token 字符串

    Returns:
        Tuple[Optional[str], Optional[Dict]]: (新的 access_token, 解码的用户数据)
        如果 refresh token 无效，返回 (None, None)
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # 验证是 refresh token 类型
        if payload.get("type") != "refresh":
            return None, None

        # 提取用户信息
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        userid = payload.get("userid")
        jti = payload.get("jti")

        if not all([user_id, user_type, userid, jti]):
            return None, None

        # 创建新的 access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        new_access_token = create_access_token(
            data={
                "sub": user_id,
                "user_type": user_type,
                "userid": userid,
            },
            expires_delta=access_token_expires,
        )

        return new_access_token, {
            "user_id": int(user_id),
            "user_type": user_type,
            "userid": userid,
            "jti": jti,
        }

    except JWTError:
        return None, None


def create_tokens_for_user(
    user_id: int, user_type: str, userid: str, nickname: Optional[str] = None
) -> Dict[str, Any]:
    """
    为用户创建访问令牌和刷新令牌

    Args:
        user_id: 用户数据库 ID
        user_type: 用户类型（super_admin/operator/sub_user）
        userid: 用户登录 ID
        nickname: 用户昵称（可选）

    Returns:
        Dict[str, Any]: 包含令牌和用户信息的字典
    """
    # 创建 access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user_id),
            "user_type": user_type,
            "userid": userid,
        },
        expires_delta=access_token_expires,
    )

    # 创建 refresh token
    refresh_token, jti, refresh_expires_at = create_refresh_token(
        user_id=user_id, user_type=user_type, userid=userid
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "jti": jti,
        "refresh_expires_at": refresh_expires_at.isoformat(),
        "user": {
            "id": user_id,
            "userid": userid,
            "nickname": nickname,
            "role": user_type,
        },
    }


# ============================================
# 微信相关安全工具
# ============================================
def generate_wechat_state() -> str:
    """
    生成微信防 CSRF state 参数

    Returns:
        str: 随机字符串
    """
    return secrets.token_urlsafe(32)


def generate_nonce(length: int = 16) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        str: 随机字符串
    """
    import string

    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_userid(prefix: str = "u") -> str:
    """
    生成用户 ID（用于登录）

    Args:
        prefix: 用户ID前缀，不同角色使用不同前缀
               - "S": 超级管理员 (Super Admin)
               - "O": 创作管理员 (Operator)
               - "U": 创作者 (Sub User)

    Returns:
        str: 随机用户 ID，格式类似：O_xxxxx
    """
    return f"{prefix}_{secrets.token_urlsafe(12)}"


def generate_invitation_code() -> str:
    """
    生成邀请码

    Returns:
        str: 6 位大写字母和数字的邀请码
    """
    import string

    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(6))
