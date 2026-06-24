"""
平台分类 Schema 定义
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class PlatformBase(BaseModel):
    """平台基础 Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="平台名称")
    description: Optional[str] = Field(None, max_length=200, description="平台描述")
    color: Optional[str] = Field(None, max_length=7, description="平台颜色标识(HEX)")
    sort_order: int = Field(0, ge=0, description="排序序号")


class PlatformCreate(PlatformBase):
    """创建平台请求 Schema"""
    pass


class PlatformUpdate(BaseModel):
    """更新平台请求 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, max_length=7)
    sort_order: Optional[int] = Field(None, ge=0)


class PlatformResponse(PlatformBase):
    """平台响应 Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by: Optional[int] = None
    owner_operator_id: int
    created_at: datetime
    updated_at: datetime
    
    # 统计信息
    material_category_count: int = Field(0, description="素材分类数量")
    template_category_count: int = Field(0, description="模板分类数量")


# ==================== 树形结构 Schema (与前端匹配) ====================

class CategoryTreeTag(BaseModel):
    """标签树形结构项 (与前端 CategoryTreeTag 匹配)"""
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    material_count: Optional[int] = 0
    template_count: Optional[int] = 0
    created_at: Optional[str] = None


class CategoryTreeCategory(BaseModel):
    """分类树形结构项 (与前端 CategoryTreeCategory 匹配)"""
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    material_count: Optional[int] = 0
    template_count: Optional[int] = 0
    tag_count: int = 0  # 该分类下的标签数量
    tags: List[CategoryTreeTag] = []


class CategoryTreePlatform(BaseModel):
    """平台树形结构项 (与前端 CategoryTreePlatform 匹配)"""
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    material_category_count: Optional[int] = 0
    template_category_count: Optional[int] = 0
    category_count: int = 0  # 该平台的分类数量
    categories: List[CategoryTreeCategory] = []


class PlatformTreeResponse(BaseModel):
    """平台树形响应 (与前端 CategoryTreeResponse 匹配)"""
    platforms: List[CategoryTreePlatform]
    material_total: int
    template_total: int
