"""
系统提示词模板 Schema

Author: Claude Code
Date: 2025
"""
from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseSchema


PLATFORM_OPTIONS = ["小红书", "抖音", "微信公众号", "快手", "视频号"]


class PromptTemplateBase(BaseModel):
    """
    提示词模板基础信息
    """
    name: str = Field(..., description="模板名称", max_length=200)
    template_type: str = Field(..., description="提示词类型：aigc_text_prompt_generator/aigc_image_prompt_generator")
    applicable_platforms: Optional[list[str]] = Field(default=None, description="适用平台列表")
    content: str = Field(..., description="提示词模板内容")
    variables_hint: Optional[str] = Field(default=None, description="可用变量说明")
    description: Optional[str] = Field(default=None, description="模板描述")
    is_default: bool = Field(default=False, description="是否为默认模板")
    status: str = Field(default="enabled", description="状态：enabled/disabled")


class PromptTemplateCreate(PromptTemplateBase):
    """
    创建提示词模板请求
    """
    pass


class PromptTemplateUpdate(BaseModel):
    """
    更新提示词模板请求
    """
    name: Optional[str] = Field(default=None, description="模板名称", max_length=200)
    applicable_platforms: Optional[list[str]] = Field(default=None, description="适用平台列表")
    content: Optional[str] = Field(default=None, description="提示词模板内容")
    variables_hint: Optional[str] = Field(default=None, description="可用变量说明")
    description: Optional[str] = Field(default=None, description="模板描述")
    is_default: Optional[bool] = Field(default=None, description="是否为默认模板")
    status: Optional[str] = Field(default=None, description="状态：enabled/disabled")


class PromptTemplateResponse(PromptTemplateBase, BaseSchema):
    """
    提示词模板响应
    """
    owner_operator_id: int = Field(..., description="所属创作管理员ID")
    owner_operator_name: Optional[str] = Field(default=None, description="所属创作管理员名称")


class PromptTemplateCopyRequest(BaseModel):
    """
    复制提示词模板请求
    """
    target_operator_ids: list[int] = Field(..., description="目标创作管理员ID列表", min_length=1)
