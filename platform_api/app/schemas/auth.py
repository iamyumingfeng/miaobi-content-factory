"""
认证 Schema (auth.py)

包含认证相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """
    登录请求
    """

    userid: str = Field(..., description="用户ID", min_length=1, max_length=64)
    password: str = Field(..., description="密码", min_length=1, max_length=128)


class UsernamePasswordLoginRequest(BaseModel):
    """
    账号密码登录请求
    """

    userid: str = Field(..., description="用户ID", min_length=1, max_length=64)
    password: str = Field(..., description="密码", min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """
    令牌响应
    """

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserInfo(BaseModel):
    """
    用户信息
    """

    id: int = Field(..., description="用户ID")
    userid: str = Field(..., description="登录用户ID")
    nickname: Optional[str] = Field(default=None, description="昵称")
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    role: str = Field(..., description="用户角色：super_admin / operator / sub_user")


class LoginResponse(BaseModel):
    """
    登录响应
    """

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间（秒）")
    refresh_expires_in: int = Field(..., description="刷新令牌过期时间（秒）")
    user: UserInfo = Field(..., description="用户信息")


class RefreshTokenResponse(BaseModel):
    """
    刷新令牌响应
    """

    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class ChangePasswordRequest(BaseModel):
    """
    修改密码请求
    """

    old_password: str = Field(..., description="原密码", min_length=1, max_length=128)
    new_password: str = Field(..., description="新密码", min_length=6, max_length=128)
    confirm_password: str = Field(..., description="确认新密码")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """验证两次输入的密码是否一致"""
        # 获取 new_password 的值（通过 info.data）
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class UpdateDisplayNameRequest(BaseModel):
    """
    更新自定义昵称请求
    """

    display_name: Optional[str] = Field(None, description="自定义昵称", max_length=100)

    @field_validator("display_name")
    @classmethod
    def display_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """验证昵称不为空字符串"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("昵称不能为空")
        return v


class RefreshTokenRequest(BaseModel):
    """
    刷新令牌请求
    """

    refresh_token: str = Field(..., description="刷新令牌", min_length=1)
