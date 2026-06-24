"""
系统设置 Schema (settings.py)

包含系统设置相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ModelConfigBase(BaseModel):
    """
    模型配置基础
    """

    platform: str = Field(
        ...,
        description="平台：bailian / volcano / moonshot / zhipu / jimeng / kling等",
        max_length=100,
    )
    model_id: str = Field(..., description="模型ID", max_length=255)
    model_name: str = Field(..., description="模型名称", max_length=255)
    model_type: str = Field(
        ..., description="模型类型：llm / image / video / embedding"
    )
    base_url: Optional[str] = Field(None, description="Base URL", max_length=1024)
    api_endpoint: Optional[str] = Field(None, description="API端点", max_length=1024)
    is_default: bool = Field(default=False, description="是否默认")
    max_concurrency: int = Field(default=5, description="最大并发数", ge=1, le=100000)
    config_json: Optional[dict] = Field(None, description="配置JSON（包含API Key等）")
    status: str = Field(default="active", description="状态：active / inactive")


class ModelConfigCreate(ModelConfigBase):
    """
    创建模型配置
    """

    pass


class ModelConfigUpdate(BaseModel):
    """
    更新模型配置
    """

    platform: Optional[str] = Field(None, description="平台", max_length=100)
    model_id: Optional[str] = Field(None, description="模型ID", max_length=255)
    model_name: Optional[str] = Field(None, description="模型名称", max_length=255)
    model_type: Optional[str] = Field(
        None, description="模型类型：llm / image / video / embedding"
    )
    base_url: Optional[str] = Field(None, description="Base URL", max_length=500)
    api_endpoint: Optional[str] = Field(None, description="API端点", max_length=500)
    is_default: Optional[bool] = Field(None, description="是否默认")
    max_concurrency: Optional[int] = Field(
        None, description="最大并发数", ge=1, le=100000
    )
    config_json: Optional[dict] = Field(None, description="配置JSON（包含API Key等）")
    status: Optional[str] = Field(None, description="状态：active / inactive")


class ModelConfigResponse(ModelConfigBase):
    """
    模型配置响应
    """

    id: int = Field(..., description="主键")
    is_system: bool = Field(..., description="是否系统预置模型")
    created_by: Optional[int] = Field(None, description="创建者超级管理员ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class UserDefaultModelBase(BaseModel):
    """
    用户默认模型设置基础
    """

    model_type: str = Field(
        ..., description="模型类型：llm / image / video / embedding"
    )
    model_config_id: Optional[int] = Field(
        None, description="关联的模型配置ID，NULL表示自动选择"
    )


class UserDefaultModelUpdate(BaseModel):
    """
    更新用户默认模型设置
    """

    llm_model_config_id: Optional[int] = Field(
        None, description="文本模型配置ID，None表示自动选择"
    )
    image_model_config_id: Optional[int] = Field(
        None, description="图片模型配置ID，None表示自动选择"
    )
    video_model_config_id: Optional[int] = Field(
        None, description="视频模型配置ID，None表示自动选择"
    )
    embedding_model_config_id: Optional[int] = Field(
        None, description="Embedding模型配置ID，None表示自动选择"
    )


class UserDefaultModelResponse(BaseModel):
    """
    用户默认模型设置响应
    """

    llm_model_config_id: Optional[int] = Field(
        None, description="文本模型配置ID，None表示自动选择"
    )
    image_model_config_id: Optional[int] = Field(
        None, description="图片模型配置ID，None表示自动选择"
    )
    video_model_config_id: Optional[int] = Field(
        None, description="视频模型配置ID，None表示自动选择"
    )
    embedding_model_config_id: Optional[int] = Field(
        None, description="Embedding模型配置ID，None表示自动选择"
    )
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = {"from_attributes": True}
