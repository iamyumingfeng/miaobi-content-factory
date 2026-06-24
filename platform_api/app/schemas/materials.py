"""
素材 Schema (materials.py)

包含素材管理相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema


class MaterialTagBase(BaseModel):
    """
    素材标签基础信息
    """

    name: str = Field(..., description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")


class MaterialTagCreate(MaterialTagBase):
    """
    创建素材标签请求（3级结构）

    CategoryPlatform -> MaterialCategory -> MaterialTag
    """

    category_id: Optional[int] = Field(
        default=None, description="所属分类ID（NULL表示未分类，属于平台层级）"
    )


class MaterialTagUpdate(BaseModel):
    """
    更新素材标签请求
    """

    name: Optional[str] = Field(
        default=None, description="标签名称", min_length=1, max_length=100
    )
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")


class MaterialTagResponse(MaterialTagBase, BaseSchema):
    """
    素材标签响应（3级结构）
    """

    model_config = {"from_attributes": True}

    is_system: bool = Field(default=False, description="是否系统默认标签（不可删除）")
    category_id: Optional[int] = Field(default=None, description="所属分类ID")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(
        default=None,
        validation_alias="owner_operator_id",
        description="所属创作管理员ID",
    )


class MaterialCategoryBase(BaseModel):
    """
    素材分类基础信息（3级结构中间层）
    """

    name: str = Field(..., description="分类名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="分类描述")
    color: Optional[str] = Field(default=None, description="分类颜色")
    sort_order: int = Field(default=0, description="排序序号")


class MaterialCategoryCreate(MaterialCategoryBase):
    """
    创建素材分类请求

    CategoryPlatform -> MaterialCategory -> MaterialTag
    """

    platform_id: int = Field(..., description="所属平台ID")


class MaterialCategoryUpdate(BaseModel):
    """
    更新素材分类请求
    """

    name: Optional[str] = Field(
        default=None, description="分类名称", min_length=1, max_length=100
    )
    description: Optional[str] = Field(default=None, description="分类描述")
    color: Optional[str] = Field(default=None, description="分类颜色")
    sort_order: Optional[int] = Field(default=None, description="排序序号")


class MaterialCategoryResponse(MaterialCategoryBase, BaseSchema):
    """
    素材分类响应
    """

    model_config = {"from_attributes": True}

    platform_id: int = Field(..., description="所属平台ID")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(
        default=None,
        validation_alias="owner_operator_id",
        description="所属创作管理员ID",
    )
    tag_count: int = Field(default=0, description="分类下标签数量")


class MaterialAttachmentBase(BaseModel):
    """
    素材附件基础信息
    """

    file_type: str = Field(..., description="文件类型：image / video")
    file_url: str = Field(..., description="文件URL", max_length=500)
    file_name: str = Field(..., description="文件名", max_length=255)
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    sort_order: int = Field(default=0, description="排序")
    width: Optional[int] = Field(default=None, description="图片/视频宽度")
    height: Optional[int] = Field(default=None, description="图片/视频高度")
    duration: Optional[float] = Field(default=None, description="视频时长（秒）")
    thumbnail_url: Optional[str] = Field(default=None, description="缩略图URL")


class MaterialAttachmentCreate(MaterialAttachmentBase):
    """
    创建素材附件请求
    """

    pass


class MaterialAttachmentUpdate(BaseModel):
    """
    更新素材附件请求
    """

    file_name: Optional[str] = Field(default=None, description="文件名", max_length=255)
    sort_order: Optional[int] = Field(default=None, description="排序")


class MaterialAttachmentResponse(MaterialAttachmentBase, BaseSchema):
    """
    素材附件响应
    """

    material_id: int = Field(..., description="素材ID")


class MaterialBase(BaseModel):
    """
    素材基础信息（对标素材）
    """

    title: str = Field(..., description="素材标题", min_length=1, max_length=500)
    content: str = Field(..., description="素材内容（必填）", min_length=1)
    topic: str = Field(
        ..., description="素材话题（必选）", min_length=1, max_length=255
    )
    text_content: Optional[str] = Field(
        default=None, description="文本内容（旧字段，保留兼容）"
    )
    source_url: Optional[str] = Field(
        default=None, description="来源URL", max_length=500
    )
    source_type: str = Field(
        default="upload", description="来源类型：upload / link / description"
    )
    content_type: str = Field(
        default="text", description="内容类型：text / image_text / video_text / mix"
    )
    status: str = Field(default="available", description="状态：available / disabled")


class MaterialCreate(BaseModel):
    """
    创建素材请求（对标素材）
    """

    title: str = Field(..., description="素材标题", min_length=1, max_length=500)
    content: str = Field(..., description="素材内容（必填）", min_length=1)
    topic: str = Field(
        ..., description="素材话题（必选）", min_length=1, max_length=255
    )
    text_content: Optional[str] = Field(
        default=None, description="文本内容（旧字段，保留兼容）"
    )
    source_url: Optional[str] = Field(
        default=None, description="来源URL", max_length=500
    )
    source_type: str = Field(
        default="upload", description="来源类型：upload / link / description"
    )
    content_type: str = Field(
        default="text", description="内容类型：text / image_text / video_text / mix"
    )
    tag_ids: Optional[List[int]] = Field(default=None, description="标签ID列表")
    creative_seed_id: Optional[int] = Field(
        default=None, description="关联的创意种子ID"
    )
    product_selling_points: Optional[str] = Field(
        default=None, description="产品卖点描述"
    )


class MaterialUpdate(BaseModel):
    """
    更新素材请求
    """

    title: Optional[str] = Field(
        default=None, description="素材标题", min_length=1, max_length=500
    )
    content: Optional[str] = Field(default=None, description="素材内容", min_length=1)
    topic: Optional[str] = Field(
        default=None, description="素材话题", min_length=1, max_length=255
    )
    text_content: Optional[str] = Field(default=None, description="文本内容")
    source_url: Optional[str] = Field(
        default=None, description="来源URL", max_length=500
    )
    source_type: Optional[str] = Field(default=None, description="来源类型")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    tag_ids: Optional[List[int]] = Field(default=None, description="标签ID列表")
    status: Optional[str] = Field(default=None, description="状态")
    creative_seed_id: Optional[int] = Field(
        default=None, description="关联的创意种子ID"
    )
    product_selling_points: Optional[str] = Field(
        default=None, description="产品卖点描述"
    )


class MaterialResponse(MaterialBase, BaseSchema):
    """
    素材响应（对标素材）
    """

    content: str = Field(..., description="素材内容")
    topic: str = Field(..., description="素材话题")
    image_count: int = Field(default=0, description="图片数量")
    video_count: int = Field(default=0, description="视频数量")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(default=None, description="创作管理员ID")
    attachments: Optional[List[MaterialAttachmentResponse]] = Field(
        default=None, description="素材附件列表"
    )
    tags: Optional[List[MaterialTagResponse]] = Field(
        default=None, description="素材标签列表"
    )
    is_favorite: Optional[bool] = Field(default=False, description="是否收藏")
    category: Optional[Dict[str, Any]] = Field(default=None, description="所属分类")
    platform: Optional[Dict[str, Any]] = Field(default=None, description="所属平台")
    creative_seed_id: Optional[int] = Field(
        default=None, description="关联的创意种子ID"
    )
    product_selling_points: Optional[str] = Field(
        default=None, description="产品卖点描述"
    )


class MaterialCopyRequest(BaseModel):
    """
    复制素材请求
    """

    new_title: Optional[str] = Field(default=None, description="新素材标题")
    target_operator_id: Optional[int] = Field(
        default=None, description="目标管理员ID（超级管理员复制给其他管理员时使用）"
    )
    tag_ids: Optional[List[int]] = Field(
        default=None, description="目标标签ID列表（为空或未传则不关联标签）"
    )
