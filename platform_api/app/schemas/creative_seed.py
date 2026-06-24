"""
创意种子库 Schema (creative_seed.py)

定义创意种子库的请求和响应数据模型。

Author: Claude Code
Date: 2026
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CreativeSeedTypeEnum(str, Enum):
    """种子类型枚举"""

    OPENING = "opening"  # 开头模式
    EMOTION = "emotion"  # 情感基调
    ENDING = "ending"  # 结尾模式


class CreativeSeedStatusEnum(str, Enum):
    """种子状态枚举"""

    ENABLED = "enabled"
    DISABLED = "disabled"


class CreativeSeedBase(BaseModel):
    """创意种子基础模型"""

    name: str = Field(..., max_length=100, description="种子名称")
    seed_type: CreativeSeedTypeEnum = Field(..., description="种子类型")
    template: str = Field(
        ..., description="模板示例（JSON数组格式，如：['示例1', '示例2']）"
    )
    description: Optional[str] = Field(None, description="使用说明")
    forbidden_patterns: Optional[List[str]] = Field(
        default_factory=list, description="禁止使用的模式"
    )
    example_phrases: Optional[List[str]] = Field(
        default_factory=list, description="典型表达示例"
    )
    avoid_phrases: Optional[List[str]] = Field(
        default_factory=list, description="避免的表达"
    )
    category: Optional[str] = Field("通用", max_length=50, description="适用品类")
    status: CreativeSeedStatusEnum = Field(
        CreativeSeedStatusEnum.ENABLED, description="状态"
    )


class CreativeSeedCreate(CreativeSeedBase):
    """创建创意种子请求"""

    pass


class CreativeSeedUpdate(BaseModel):
    """更新创意种子请求"""

    name: Optional[str] = Field(None, max_length=100)
    seed_type: Optional[CreativeSeedTypeEnum] = None
    template: Optional[str] = Field(None, description="模板示例（JSON数组格式）")
    description: Optional[str] = None
    forbidden_patterns: Optional[List[str]] = None
    example_phrases: Optional[List[str]] = None
    avoid_phrases: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[CreativeSeedStatusEnum] = None


class CreativeSeedResponse(CreativeSeedBase):
    """创意种子响应"""

    id: int
    is_system: bool = Field(False, description="是否系统预置")
    owner_operator_id: Optional[int] = None
    use_count: int = Field(0, description="使用次数")
    success_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreativeSeedListResponse(BaseModel):
    """创意种子列表响应"""

    items: List[CreativeSeedResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreativeSeedSelectResponse(BaseModel):
    """创意种子选择响应（用于下拉选择）"""

    id: int
    name: str
    seed_type: CreativeSeedTypeEnum
    template: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class CreativeSeedGroupResponse(BaseModel):
    """按类型分组的创意种子响应"""

    opening: List[CreativeSeedSelectResponse] = Field(
        default_factory=list, description="开头模式列表"
    )
    emotion: List[CreativeSeedSelectResponse] = Field(
        default_factory=list, description="情感基调列表"
    )
    ending: List[CreativeSeedSelectResponse] = Field(
        default_factory=list, description="结尾模式列表"
    )
