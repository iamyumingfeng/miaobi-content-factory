"""
模板 Schema (templates.py)

包含模板管理相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseSchema


class TemplatePlatformBase(BaseModel):
    """
    模板平台基础信息
    """
    name: str = Field(..., description="平台名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="平台颜色")
    sort_order: int = Field(default=0, description="排序")


class TemplatePlatformCreate(TemplatePlatformBase):
    """
    创建模板平台请求
    """
    pass


class TemplatePlatformUpdate(BaseModel):
    """
    更新模板平台请求
    """
    name: Optional[str] = Field(default=None, description="平台名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="平台颜色")
    sort_order: Optional[int] = Field(default=None, description="排序")


class TemplatePlatformResponse(TemplatePlatformBase, BaseSchema):
    """
    模板平台响应
    """
    is_system: bool = Field(default=False, description="是否系统默认平台（不可删除）")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(default=None, description="创作管理员ID")
    status: str = Field(default="active", description="状态：active / inactive")
    template_count: Optional[int] = Field(default=0, description="模板数量")


class TemplateCategoryBase(BaseModel):
    """
    模板分类基础信息（3级结构中间层）
    """
    name: str = Field(..., description="分类名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="分类描述")
    color: Optional[str] = Field(default=None, description="分类颜色")
    sort_order: int = Field(default=0, description="排序序号")


class TemplateCategoryCreate(TemplateCategoryBase):
    """
    创建模板分类请求

    CategoryPlatform -> TemplateCategory -> TemplateTag
    """
    platform_id: int = Field(..., description="所属平台ID")


class TemplateCategoryUpdate(BaseModel):
    """
    更新模板分类请求
    """
    name: Optional[str] = Field(default=None, description="分类名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="分类描述")
    color: Optional[str] = Field(default=None, description="分类颜色")
    sort_order: Optional[int] = Field(default=None, description="排序序号")


class TemplateCategoryResponse(TemplateCategoryBase, BaseSchema):
    """
    模板分类响应
    """
    model_config = {"from_attributes": True}

    platform_id: int = Field(..., description="所属平台ID")
    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(default=None, validation_alias="owner_operator_id", description="所属创作管理员ID")
    tag_count: int = Field(default=0, description="分类下标签数量")


class TemplateTagBase(BaseModel):
    """
    模板标签基础信息（3级结构）
    """
    name: str = Field(..., description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")


class TemplateTagCreate(TemplateTagBase):
    """
    创建模板标签请求（3级结构）

    CategoryPlatform -> TemplateCategory -> TemplateTag
    """
    category_id: Optional[int] = Field(default=None, description="所属分类ID（NULL表示未分类）")


class TemplateTagUpdate(BaseModel):
    """
    更新模板标签请求
    """
    name: Optional[str] = Field(default=None, description="标签名称", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="描述")
    color: Optional[str] = Field(default=None, description="标签颜色")
    category_id: Optional[int] = Field(default=None, description="所属分类ID")


class TemplateTagResponse(TemplateTagBase, BaseSchema):
    """
    模板标签响应（3级结构）
    """
    model_config = {"from_attributes": True}

    is_system: bool = Field(default=False, description="是否系统默认标签（不可删除）")
    category_id: Optional[int] = Field(default=None, description="所属分类ID")
    created_by: Optional[int] = Field(default=None, description="创建者用户ID")


class TemplateAttachmentBase(BaseModel):
    """
    模板附件基础信息
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


class TemplateAttachmentCreate(TemplateAttachmentBase):
    """
    创建模板附件请求
    """
    pass


class TemplateAttachmentUpdate(BaseModel):
    """
    更新模板附件请求
    """
    file_name: Optional[str] = Field(default=None, description="文件名", max_length=255)
    sort_order: Optional[int] = Field(default=None, description="排序")


class TemplateAttachmentResponse(TemplateAttachmentBase, BaseSchema):
    """
    模板附件响应
    """
    template_id: int = Field(..., description="模板ID")


class TemplateBase(BaseModel):
    """
    模板基础信息 - 爆款模板库
    """
    name: str = Field(..., description="模板名称", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="创作方向说明（原提示词创意）")
    content_type: str = Field(..., description="内容类型：text / image_text / video_text")
    prompt_template: Optional[str] = Field(default=None, description="提示词模板")
    variables_json: Optional[Dict[str, Any]] = Field(default=None, description="变量定义JSON")
    style_reference: Optional[str] = Field(default=None, description="风格参考")
    platform_rules_json: Optional[Dict[str, Any]] = Field(default=None, description="平台规则JSON")
    platform_id: Optional[int] = Field(default=None, description="所属平台ID")
    status: str = Field(default="enabled", description="状态：enabled / disabled")
    # 图片尺寸比例：1:1(2048x2048), 4:3(2304x1728), 16:9(2560x1440), 3:4(1728x2304), 9:16(1440x2560)
    image_size_ratio: Optional[str] = Field(default=None, description="图片尺寸比例：1:1/4:3/16:9/3:4/9:16")
    # 是否添加水印
    add_watermark: Optional[bool] = Field(default=True, description="是否添加水印")
    # ===== 爆款模板新增字段 =====
    # 爆款类型
    viral_type: Optional[str] = Field(
        default="seeding",
        description="爆款类型：seeding（种草）/review（测评）/tutorial（教程）/sharing（分享）/pain_point（痛点）/story（故事）"
    )
    # 创意种子关联（可指定或随机）
    # 支持：'auto' 表示随机选择，数字字符串表示指定种子ID
    opening_seed_id: Optional[str] = Field(default=None, description="开头模式：'auto'表示随机，数字字符串表示指定种子ID")
    emotion_seed_id: Optional[str] = Field(default=None, description="情感基调：'auto'表示随机，数字字符串表示指定种子ID")
    ending_seed_id: Optional[str] = Field(default=None, description="结尾模式：'auto'表示随机，数字字符串表示指定种子ID")
    # 产品名称（必填，用于提示词中明确推广的产品）
    product_name: str = Field(default=None, description="产品名称（用于提示词中明确推广的产品，防止与对标素材混淆）", min_length=1, max_length=255)
    # 产品卖点
    product_selling_points: Optional[str] = Field(default=None, description="产品卖点描述（用于文案生成时强调重点）")


class TemplateCreate(TemplateBase):
    """
    创建模板请求 - 爆款模板库
    """
    tag_ids: Optional[List[int]] = Field(default=None, description="标签ID列表")
    # 爆款标签（可选）
    viral_tags: Optional[List[str]] = Field(default=None, description="爆款标签列表，如：['高互动', '高转化', '高曝光']")


class TemplateUpdate(BaseModel):
    """
    更新模板请求 - 爆款模板库
    """
    name: Optional[str] = Field(default=None, description="模板名称", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="创作方向说明")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    prompt_template: Optional[str] = Field(default=None, description="提示词模板")
    variables_json: Optional[Dict[str, Any]] = Field(default=None, description="变量定义JSON")
    style_reference: Optional[str] = Field(default=None, description="风格参考")
    platform_rules_json: Optional[Dict[str, Any]] = Field(default=None, description="平台规则JSON")
    platform_id: Optional[int] = Field(default=None, description="所属平台ID")
    status: Optional[str] = Field(default=None, description="状态")
    tag_ids: Optional[List[int]] = Field(default=None, description="标签ID列表")
    # 图片尺寸比例：1:1(2048x2048), 4:3(2304x1728), 16:9(2560x1440), 3:4(1728x2304), 9:16(1440x2560)
    image_size_ratio: Optional[str] = Field(default=None, description="图片尺寸比例：1:1/4:3/16:9/3:4/9:16")
    # 是否添加水印
    add_watermark: Optional[bool] = Field(default=None, description="是否添加水印")
    # ===== 爆款模板新增字段 =====
    viral_type: Optional[str] = Field(default=None, description="爆款类型")
    # 支持：'auto' 表示随机选择，数字字符串表示指定种子ID
    opening_seed_id: Optional[str] = Field(default=None, description="开头模式：'auto'表示随机")
    emotion_seed_id: Optional[str] = Field(default=None, description="情感基调：'auto'表示随机")
    ending_seed_id: Optional[str] = Field(default=None, description="结尾模式：'auto'表示随机")
    product_name: Optional[str] = Field(default=None, description="产品名称", min_length=1, max_length=255)
    product_selling_points: Optional[str] = Field(default=None, description="产品卖点描述")
    viral_tags: Optional[List[str]] = Field(default=None, description="爆款标签列表")


class TemplateResponse(TemplateBase, BaseSchema):
    """
    模板响应 - 爆款模板库
    """
    model_config = {"from_attributes": True}

    created_by: Optional[int] = Field(default=None, description="创建者创作管理员ID")
    owner_admin_id: Optional[int] = Field(default=None, description="所属创作管理员ID")
    original_template_id: Optional[int] = Field(default=None, description="原模板ID（复制来源）")
    platform: Optional[TemplatePlatformResponse] = Field(default=None, description="所属平台")
    category: Optional[Dict[str, Any]] = Field(default=None, description="所属分类（从第一个标签获取）")
    tags: Optional[List[TemplateTagResponse]] = Field(default=None, description="模板标签列表")
    image_count: int = Field(default=0, description="图片数量")
    video_count: int = Field(default=0, description="视频数量")
    attachments: Optional[List[TemplateAttachmentResponse]] = Field(default=None, description="模板附件列表")
    # ===== 爆款模板统计字段 =====
    viral_score: Optional[float] = Field(default=0.0, description="爆款指数（0-100）")
    viral_tags: Optional[List[str]] = Field(default=None, description="爆款标签列表")
    use_count: int = Field(default=0, description="使用次数统计")
    success_count: int = Field(default=0, description="成功生成次数")
    # 创意种子详情（关联查询后填充）
    opening_seed: Optional[Dict[str, Any]] = Field(default=None, description="开头模式种子详情")
    emotion_seed: Optional[Dict[str, Any]] = Field(default=None, description="情感基调种子详情")
    ending_seed: Optional[Dict[str, Any]] = Field(default=None, description="结尾模式种子详情")


class TemplateCopyRequest(BaseModel):
    """
    复制模板请求
    """
    new_name: Optional[str] = Field(default=None, description="新模板名称")
    target_platform_id: Optional[int] = Field(default=None, description="目标平台ID")
    target_category_id: Optional[int] = Field(default=None, description="目标分类ID")
    target_tag_ids: Optional[List[int]] = Field(default=None, description="目标标签ID列表")
