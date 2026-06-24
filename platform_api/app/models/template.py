"""
模板模型 (template.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (JSON, BigInteger, Boolean, Column, DateTime, Enum,
                        Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TemplateCategory(Base):
    """
    模板分类表 - 3层结构的中间层

    TemplatePlatform -> TemplateCategory -> TemplateTag -> Template
    """

    __tablename__ = "template_category"
    __table_args__ = (
        UniqueConstraint(
            "owner_operator_id", "name", name="uq_template_category_owner_name"
        ),
        Index("ix_template_category_platform", "template_platform_id"),
        Index("ix_template_category_owner", "owner_operator_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(String(500), nullable=True, comment="分类描述")
    color = Column(String(20), nullable=True, comment="分类颜色")
    template_platform_id = Column(
        BigInteger,
        ForeignKey("template_platform.id"),
        nullable=False,
        comment="所属模板平台ID",
    )
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=False,
        comment="所属创作管理员ID（数据隔离用）",
    )
    created_by = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=True,
        comment="创建者创作管理员ID",
    )
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关联关系
    platform = relationship(
        "TemplatePlatform",
        back_populates="categories",
        foreign_keys=[template_platform_id],
    )
    tags = relationship(
        "TemplateTag",
        back_populates="category",
        cascade="all, delete-orphan",
        foreign_keys="TemplateTag.category_id",
    )

    def __repr__(self):
        return f"<TemplateCategory(id={self.id}, name={self.name})>"


class TemplateTag(Base):
    """
    模板标签表 - 3层结构的叶子层

    CategoryPlatform -> TemplateCategory -> TemplateTag

    改造说明:
    - 原 platform_id (关联 template_platform) -> 现 category_id (关联 TemplateCategory)
    - 实现从 2层(平台->标签) 到 3层(平台->分类->标签) 的升级
    """

    __tablename__ = "template_tag"
    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_template_tag_category_name"),
        Index("ix_template_tag_category", "category_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="标签名称")
    description = Column(String(500), nullable=True, comment="标签描述")
    color = Column(String(20), nullable=True, comment="标签颜色")
    # 🔥 改造: 从 platform_id 改为 category_id
    category_id = Column(
        BigInteger,
        ForeignKey("template_category.id"),
        nullable=True,  # 暂时允许NULL以便迁移，迁移完成后改为False
        comment="所属分类ID",
    )
    # 原 platform_id 字段在迁移脚本中处理
    is_system = Column(
        Boolean, nullable=False, default=False, comment="是否系统默认标签"
    )
    created_by = Column(
        BigInteger, ForeignKey("operator.id"), nullable=False, comment="创建者管理员ID"
    )
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=False,
        index=True,
        comment="所属创作管理员ID（数据隔离用）",
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关联关系
    category = relationship(
        "TemplateCategory", back_populates="tags", foreign_keys=[category_id]
    )

    def __repr__(self):
        return f"<TemplateTag(id={self.id}, name={self.name})>"


class TemplateTagRel(Base):
    """
    模板标签关联表
    """

    __tablename__ = "template_tag_rel"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    template_id = Column(
        BigInteger, ForeignKey("template.id"), nullable=False, comment="模板ID"
    )
    tag_id = Column(
        BigInteger, ForeignKey("template_tag.id"), nullable=False, comment="标签ID"
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    def __repr__(self):
        return f"<TemplateTagRel(id={self.id}, template_id={self.template_id}, tag_id={self.tag_id})>"


class Template(Base):
    """
    模板表 - 爆款模板库

    改造说明：
    - 原提示词创意(description)字段保留，作为"创作方向说明"
    - 新增爆款类型字段，支持种草/测评/教程等多种模板类型
    - 关联创意种子，支持指定开头/情感/结尾模式
    - 产品卖点字段，用于文案生成时强调重点
    """

    __tablename__ = "template"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(255), nullable=False, comment="模板名称")
    description = Column(
        String(1000), nullable=True, comment="创作方向说明（原提示词创意）"
    )
    content_type = Column(
        Enum("text", "image_text", "video_text", name="template_content_type_enum"),
        nullable=False,
        comment="内容类型：text（纯文本）/ image_text（图文）/ video_text（视频）",
    )
    prompt_template = Column(
        Text, nullable=True, comment="Prompt模板（支持变量占位符）"
    )
    variables_json = Column(JSON, nullable=True, comment="变量定义JSON")
    style_reference = Column(String(1000), nullable=True, comment="风格场景参考描述")
    platform_rules_json = Column(JSON, nullable=True, comment="平台适配规则JSON")
    status = Column(
        Enum("enabled", "disabled", name="template_status_enum"),
        nullable=False,
        default="enabled",
        comment="状态：enabled（已启用）/ disabled（已禁用）",
    )
    platform_id = Column(
        BigInteger,
        ForeignKey("template_platform.id"),
        nullable=True,
        comment="关联模板平台ID",
    )
    original_template_id = Column(
        BigInteger,
        ForeignKey("template.id"),
        nullable=True,
        comment="原始模板ID（用于追踪克隆关系）",
    )
    created_by = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=True,
        comment="创建者创作管理员ID",
    )
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=False,
        index=True,
        comment="所属创作管理员ID（数据隔离用）",
    )
    image_count = Column(
        Integer, nullable=False, default=0, comment="图片数量（冗余字段，提高查询效率）"
    )
    video_count = Column(
        Integer, nullable=False, default=0, comment="视频数量（冗余字段，提高查询效率）"
    )
    # 图片尺寸比例：1:1(2048x2048), 4:3(2304x1728), 16:9(2560x1440), 3:4(1728x2304), 9:16(1440x2560)
    image_size_ratio = Column(
        String(20), nullable=True, comment="图片尺寸比例：1:1/4:3/16:9/3:4/9:16"
    )
    # 是否添加水印
    add_watermark = Column(
        Boolean, nullable=False, default=True, comment="是否添加水印"
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # ===== 爆款模板新增字段 =====
    # 爆款类型（20种 + auto随机）
    # 使用字符串类型：具体类型值 或 "auto" 表示随机选择
    viral_type = Column(
        String(50),
        nullable=True,
        default="seeding",
        comment="爆款类型：具体类型值 或 'auto' 表示随机选择",
    )
    # 创意种子关联（可指定或随机）
    # 使用字符串类型存储："auto"表示随机选择，数字字符串表示指定种子ID
    opening_seed_id = Column(
        String(50),
        nullable=True,
        default="auto",
        comment="开头模式：'auto'表示随机，数字字符串表示指定种子ID",
    )
    emotion_seed_id = Column(
        String(50),
        nullable=True,
        default="auto",
        comment="情感基调：'auto'表示随机，数字字符串表示指定种子ID",
    )
    ending_seed_id = Column(
        String(50),
        nullable=True,
        default="auto",
        comment="结尾模式：'auto'表示随机，数字字符串表示指定种子ID",
    )
    # 产品卖点（模板级别的卖点说明）
    product_selling_points = Column(
        Text, nullable=True, comment="产品卖点描述（用于文案生成时强调重点）"
    )
    # 产品名称（必填，用于提示词中明确推广的产品）
    product_name = Column(
        String(255),
        nullable=False,
        comment="产品名称（用于提示词中明确推广的产品，防止与对标素材混淆）",
    )
    # 爆款指数（基于历史数据计算）
    viral_score = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="爆款指数（0-100，基于历史互动/转化数据计算）",
    )
    # 爆款标签
    viral_tags = Column(
        JSON,
        nullable=True,
        comment='爆款标签JSON数组，如：["高互动", "高转化", "高曝光"]',
    )
    # 统计字段
    use_count = Column(BigInteger, nullable=False, default=0, comment="使用次数统计")
    success_count = Column(
        BigInteger, nullable=False, default=0, comment="成功生成次数（通过去重的数量）"
    )

    # 关联关系
    platform = relationship("TemplatePlatform", foreign_keys=[platform_id])
    generation_task_templates = relationship(
        "GenerationTaskTemplate",
        back_populates="template",
        foreign_keys="GenerationTaskTemplate.template_id",
    )
    generation_items = relationship(
        "GenerationItem",
        back_populates="template",
        foreign_keys="GenerationItem.template_id",
    )
    attachments = relationship(
        "TemplateAttachment",
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name})>"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content_type": self.content_type,
            "prompt_template": self.prompt_template,
            "variables_json": self.variables_json,
            "style_reference": self.style_reference,
            "platform_rules_json": self.platform_rules_json,
            "status": self.status,
            "platform_id": self.platform_id,
            "original_template_id": self.original_template_id,
            "created_by": self.created_by,
            "owner_operator_id": self.owner_operator_id,
            "image_count": self.image_count,
            "video_count": self.video_count,
            "image_size_ratio": self.image_size_ratio,
            "add_watermark": self.add_watermark,
            "viral_type": self.viral_type,
            "opening_seed_id": self.opening_seed_id,
            "emotion_seed_id": self.emotion_seed_id,
            "ending_seed_id": self.ending_seed_id,
            "product_selling_points": self.product_selling_points,
            "viral_score": self.viral_score,
            "viral_tags": self.viral_tags,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_creative_seed_config(self) -> Dict[str, Any]:
        """
        获取创意种子配置

        Returns:
            Dict: 包含指定种子ID和随机策略的配置
        """
        return {
            "opening_seed_id": self.opening_seed_id,
            "emotion_seed_id": self.emotion_seed_id,
            "ending_seed_id": self.ending_seed_id,
            "viral_type": self.viral_type,
            "product_selling_points": self.product_selling_points,
        }


class TemplateAttachment(Base):
    """
    模板附件表
    """

    __tablename__ = "template_attachment"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    template_id = Column(
        BigInteger, ForeignKey("template.id"), nullable=False, comment="模板ID"
    )
    file_type = Column(
        Enum("image", "video", name="template_attachment_type_enum"),
        nullable=False,
        comment="文件类型：image（图片）/ video（视频）",
    )
    file_url = Column(String(500), nullable=False, comment="腾讯云COS文件URL")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    width = Column(Integer, nullable=True, comment="图片/视频宽度（像素）")
    height = Column(Integer, nullable=True, comment="图片/视频高度（像素）")
    duration = Column(Float, nullable=True, comment="视频时长（秒）")
    thumbnail_url = Column(String(500), nullable=True, comment="缩略图URL")
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关联关系
    template = relationship(
        "Template", back_populates="attachments", foreign_keys=[template_id]
    )

    def __repr__(self):
        return f"<TemplateAttachment(id={self.id}, template_id={self.template_id}, file_type={self.file_type})>"
