"""
用户 Schema (users.py)

包含用户管理相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseSchema


class UserBase(BaseModel):
    """
    用户基础信息
    """
    model_config = {"from_attributes": True}

    userid: str = Field("", description="用户ID", min_length=0, max_length=64)
    nickname: str = Field(..., description="管理备注名", min_length=1, max_length=100)


class SuperAdminBase(UserBase):
    """
    超级管理员基础信息
    """
    status: str = Field(default="active", description="状态：active / disabled")


class SuperAdminCreate(SuperAdminBase):
    """
    创建超级管理员请求
    """
    password: str = Field(..., description="密码", min_length=6, max_length=128)


class SuperAdminUpdate(BaseModel):
    """
    更新超级管理员请求
    """
    nickname: Optional[str] = Field(default=None, description="昵称", min_length=1, max_length=100)
    status: Optional[str] = Field(default=None, description="状态：active / disabled")


class SuperAdminResponse(SuperAdminBase, BaseSchema):
    """
    超级管理员响应
    """
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    wechat_openid: Optional[str] = Field(default=None, description="微信OpenID")
    wechat_unionid: Optional[str] = Field(default=None, description="微信UnionID")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")


class OperatorBase(UserBase):
    """
    创作管理员基础信息
    """
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    status: str = Field(default="active", description="状态：active / disabled")
    user_positioning: Optional[str] = Field(default=None, description="账号的自媒体运营定位")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")


class OperatorCreate(BaseModel):
    """
    创建创作管理员请求
    """
    nickname: str = Field(..., description="管理备注名", min_length=1, max_length=100)
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    password: str = Field(..., description="密码", min_length=6, max_length=128)
    user_positioning: Optional[str] = Field(default=None, description="账号的自媒体运营定位")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")


class OperatorUpdate(BaseModel):
    """
    更新创作管理员请求
    """
    nickname: Optional[str] = Field(default=None, description="管理备注名", min_length=1, max_length=100)
    display_name: Optional[str] = Field(default=None, description="自定义昵称", min_length=1, max_length=100)
    status: Optional[str] = Field(default=None, description="状态：online / offline / disabled")
    user_positioning: Optional[str] = Field(default=None, description="账号的自媒体运营定位")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")


class OperatorResponse(OperatorBase, BaseSchema):
    """
    创作管理员响应
    """
    model_config = {"from_attributes": True}

    created_by: Optional[int] = Field(default=None, description="创建者超级管理员ID")
    wechat_openid: Optional[str] = Field(default=None, description="微信OpenID")
    wechat_unionid: Optional[str] = Field(default=None, description="微信UnionID")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    role: str = Field(default="operator", description="角色")


class SubUserBase(UserBase):
    """
    创作者基础信息
    """
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    status: str = Field(default="active", description="状态：active / disabled")
    # 要点1【粉丝画像】：年龄、职业、地域、核心需求、偏好、禁忌等
    fan_profile: Optional[str] = Field(default=None, description="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）")
    # 要点2【账号定位】：核心赛道、核心价值、目标受众匹配、账号层级等
    user_positioning: Optional[str] = Field(default=None, description="账号定位（核心赛道/价值/受众/层级等）")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")
    # 要点3【内容风格】：语气、排版逻辑、呈现形式、核心调性、固定句式/口头禅等
    content_style: Optional[str] = Field(default=None, description="内容风格（语气/排版/调性/句式等）")
    account_type: Optional[str] = Field(default=None, description="账号类型")


class SubUserCreate(BaseModel):
    """
    创建创作者请求
    """
    nickname: str = Field(..., description="管理备注名", min_length=1, max_length=100)
    display_name: Optional[str] = Field(default=None, description="自定义昵称")
    password: Optional[str] = Field(default=None, description="密码（留空则自动生成）", min_length=6, max_length=128)
    # 要点1【粉丝画像】：年龄、职业、地域、核心需求、偏好、禁忌等
    fan_profile: Optional[str] = Field(default=None, description="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）")
    # 要点2【账号定位】：核心赛道、核心价值、目标受众匹配、账号层级等
    user_positioning: Optional[str] = Field(default=None, description="账号定位（核心赛道/价值/受众/层级等）")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")
    # 要点3【内容风格】：语气、排版逻辑、呈现形式、核心调性、固定句式/口头禅等
    content_style: Optional[str] = Field(default=None, description="内容风格（语气/排版/调性/句式等）")
    account_type: Optional[str] = Field(default=None, description="账号类型")
    tag_ids: Optional[List[int]] = Field(default=None, description="用户标签ID列表（用于分类管理）")


class SubUserUpdate(BaseModel):
    """
    更新创作者请求
    """
    nickname: Optional[str] = Field(default=None, description="管理备注名", min_length=1, max_length=100)
    display_name: Optional[str] = Field(default=None, description="自定义昵称", max_length=100)
    status: Optional[str] = Field(default=None, description="状态：online / offline / disabled")
    # 要点1【粉丝画像】：年龄、职业、地域、核心需求、偏好、禁忌等
    fan_profile: Optional[str] = Field(default=None, description="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）")
    # 要点2【账号定位】：核心赛道、核心价值、目标受众匹配、账号层级等
    user_positioning: Optional[str] = Field(default=None, description="账号定位（核心赛道/价值/受众/层级等）")
    user_category: Optional[str] = Field(default=None, description="账号的运营分类")
    # 要点3【内容风格】：语气、排版逻辑、呈现形式、核心调性、固定句式/口头禅等
    content_style: Optional[str] = Field(default=None, description="内容风格（语气/排版/调性/句式等）")
    account_type: Optional[str] = Field(default=None, description="账号类型")
    tag_ids: Optional[List[int]] = Field(default=None, description="用户标签ID列表（用于分类管理）")


class SubUserResponse(SubUserBase, BaseSchema):
    """
    创作者响应
    """
    owner_operator_id: int = Field(..., description="所属创作管理员ID")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    managed_by: Optional[int] = Field(default=None, description="当前管理者创作管理员ID")
    wechat_openid: Optional[str] = Field(default=None, description="微信OpenID")
    wechat_unionid: Optional[str] = Field(default=None, description="微信UnionID")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    tags: Optional[List[dict]] = Field(default=None, description="用户标签列表")


class UserTagBase(BaseModel):
    """
    用户标签基础信息
    """
    name: str = Field(..., description="标签名称", min_length=1, max_length=100)
    tag_type: str = Field(..., description="标签类型：operator_tag / subuser_tag")
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")


class UserTagCreate(UserTagBase):
    """
    创建用户标签请求
    """
    pass


class UserTagUpdate(BaseModel):
    """
    更新用户标签请求
    """
    name: Optional[str] = Field(default=None, description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")


class UserTagResponse(UserTagBase, BaseSchema):
    """
    用户标签响应
    """
    created_by: int = Field(..., description="创建者用户ID")


class UserTransferRequest(BaseModel):
    """
    用户转移请求（超级管理员）
    """
    user_ids: List[int] = Field(..., description="要转移的用户ID列表")
    from_operator_id: int = Field(..., description="源创作管理员ID")
    to_operator_id: int = Field(..., description="目标创作管理员ID")
    transfer_reason: Optional[str] = Field(default=None, description="转移原因")


class ResetPasswordRequest(BaseModel):
    """
    重置密码请求（创作管理员）
    """
    new_password: str = Field(..., description="新密码", min_length=6, max_length=128)
