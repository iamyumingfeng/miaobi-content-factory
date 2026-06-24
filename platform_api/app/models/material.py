"""
素材模型 (material.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, Text, Integer, ForeignKey, JSON, Float, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaterialPlatform(Base):
    """
    素材平台表 - 素材库独立平台（3层结构的顶层）
    
    MaterialPlatform -> MaterialCategory -> MaterialTag -> Material
    """
    __tablename__ = "material_platform"
    __table_args__ = (
        UniqueConstraint('owner_operator_id', 'name', name='uq_material_platform_owner_name'),
        Index('ix_material_platform_owner', 'owner_operator_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="平台名称")
    description = Column(String(500), nullable=True, comment="平台描述")
    color = Column(String(20), nullable=True, comment="平台颜色")
    platform_code = Column(String(50), nullable=True, comment="平台代码（如 xhs, dy）")
    config_json = Column(JSON, nullable=True, comment="平台配置JSON（预留扩展）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重")
    created_by = Column(BigInteger, ForeignKey("operator.id"), nullable=True, comment="创建者创作管理员ID")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, comment="所属创作管理员ID（数据隔离用）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    categories = relationship(
        "MaterialCategory",
        back_populates="platform",
        cascade="all, delete-orphan",
        foreign_keys="MaterialCategory.material_platform_id"
    )

    def __repr__(self):
        return f"<MaterialPlatform(id={self.id}, name={self.name})>"


class MaterialCategory(Base):
    """
    素材分类表 - 3层结构的中间层

    MaterialPlatform -> MaterialCategory -> MaterialTag -> Material
    """
    __tablename__ = "material_category"
    __table_args__ = (
        UniqueConstraint('owner_operator_id', 'name', name='uq_material_category_owner_name'),
        Index('ix_material_category_platform', 'material_platform_id'),
        Index('ix_material_category_owner', 'owner_operator_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(String(500), nullable=True, comment="分类描述")
    color = Column(String(20), nullable=True, comment="分类颜色")
    material_platform_id = Column(BigInteger, ForeignKey("material_platform.id"), nullable=False, comment="所属素材平台ID")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, comment="所属创作管理员ID（数据隔离用）")
    created_by = Column(BigInteger, ForeignKey("operator.id"), nullable=True, comment="创建者创作管理员ID")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    platform = relationship("MaterialPlatform", back_populates="categories", foreign_keys=[material_platform_id])
    tags = relationship(
        "MaterialTag",
        back_populates="category",
        cascade="all, delete-orphan",
        foreign_keys="MaterialTag.category_id"
    )

    def __repr__(self):
        return f"<MaterialCategory(id={self.id}, name={self.name})>"


class MaterialTag(Base):
    """
    素材标签表 - 3层结构的叶子层
    
    MaterialPlatform -> MaterialCategory -> MaterialTag
    
    改造说明:
    - 原 parent_id (自引用) -> 现 category_id (关联 MaterialCategory)
    - 实现从 2层(平台->标签) 到 3层(平台->分类->标签) 的升级
    """
    __tablename__ = "material_tag"
    __table_args__ = (
        UniqueConstraint('category_id', 'name', name='uq_material_tag_category_name'),
        Index('ix_material_tag_category', 'category_id'),
        Index('ix_material_tag_owner', 'owner_operator_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(100), nullable=False, comment="标签名称")
    description = Column(String(500), nullable=True, comment="标签描述")
    color = Column(String(20), nullable=True, comment="标签颜色")
    is_system = Column(
        sa.Boolean(),
        nullable=False,
        default=False,
        comment="是否系统默认标签（不可删除）"
    )
    # 🔥 改造: 从 parent_id 改为 category_id
    category_id = Column(
        BigInteger,
        ForeignKey("material_category.id"),
        nullable=True,  # 暂时允许NULL以便迁移，迁移完成后改为False
        comment="所属分类ID"
    )
    # 原 parent_id 字段在迁移脚本中删除
    created_by = Column(BigInteger, ForeignKey("operator.id"), nullable=True, comment="创建者创作管理员ID")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, comment="所属创作管理员ID（数据隔离用）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    category = relationship("MaterialCategory", back_populates="tags", foreign_keys=[category_id])

    def __repr__(self):
        return f"<MaterialTag(id={self.id}, name={self.name})>"


class MaterialTagRel(Base):
    """
    素材标签关联表
    """
    __tablename__ = "material_tag_rel"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    material_id = Column(BigInteger, ForeignKey("material.id"), nullable=False, comment="素材ID")
    tag_id = Column(BigInteger, ForeignKey("material_tag.id"), nullable=False, comment="标签ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<MaterialTagRel(id={self.id}, material_id={self.material_id}, tag_id={self.tag_id})>"


class MaterialFavorite(Base):
    """
    素材收藏表
    """
    __tablename__ = "material_favorite"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    material_id = Column(BigInteger, ForeignKey("material.id"), nullable=False, comment="素材ID")
    user_id = Column(BigInteger, nullable=False, comment="收藏用户ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<MaterialFavorite(id={self.id}, material_id={self.material_id}, user_id={self.user_id})>"


class MaterialAttachment(Base):
    """
    素材附件表
    """
    __tablename__ = "material_attachment"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    material_id = Column(BigInteger, ForeignKey("material.id"), nullable=False, comment="素材ID")
    file_type = Column(
        Enum("image", "video", name="material_attachment_type_enum"),
        nullable=False,
        comment="文件类型：image（图片）/ video（视频）"
    )
    file_url = Column(String(500), nullable=False, comment="腾讯云COS文件URL")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    width = Column(Integer, nullable=True, comment="图片/视频宽度（像素）")
    height = Column(Integer, nullable=True, comment="图片/视频高度（像素）")
    duration = Column(Float, nullable=True, comment="视频时长（秒）")
    thumbnail_url = Column(String(500), nullable=True, comment="缩略图URL")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    material = relationship("Material", back_populates="attachments", foreign_keys=[material_id])

    def __repr__(self):
        return f"<MaterialAttachment(id={self.id}, material_id={self.material_id}, file_type={self.file_type})>"


class Material(Base):
    """
    素材表
    """
    __tablename__ = "material"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    title = Column(String(500), nullable=False, comment="素材标题（拟题）")
    text_content = Column(Text, nullable=True, comment="文本内容")
    source_url = Column(String(500), nullable=True, comment="来源URL")
    source_type = Column(
        Enum("upload", "link", "description", name="materialsource_type_enum"),
        nullable=False,
        default="upload",
        comment="来源类型：upload（上传）/ link（链接）/ description（描述）"
    )
    content_type = Column(
        Enum("text", "image_text", "video_text", "mix", name="materialcontent_type_enum"),
        nullable=False,
        default="text",
        comment="内容类型：text（纯文本）/ image_text（图文）/ video_text（视频）/ mix（混合）"
    )
    image_count = Column(Integer, nullable=False, default=0, comment="图片数量（冗余字段，提高查询效率）")
    video_count = Column(Integer, nullable=False, default=0, comment="视频数量（冗余字段，提高查询效率）")
    status = Column(
        Enum("available", "disabled", name="materialstatus_enum"),
        nullable=False,
        default="available",
        comment="状态：available（可用）/ disabled（已禁用）"
    )
    created_by = Column(BigInteger, ForeignKey("operator.id"), nullable=True, comment="上传者创作管理员ID")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, index=True, comment="所属创作管理员ID（数据隔离用）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    content = Column(Text, nullable=False, comment="素材内容")
    topic = Column(String(255), nullable=False, comment="素材主题")
    library_type = Column(
        Enum("creation", "benchmark", name="materiallibrary_type_enum"),
        nullable=False,
        default="benchmark",
        comment="素材库类型：creation（创作库）/ benchmark（对标库）"
    )
    # 创意种子关联
    creative_seed_id = Column(
        BigInteger,
        ForeignKey("creative_seed.id"),
        nullable=True,
        comment="关联的创意种子ID（用于指定开头/情感/结尾模式）"
    )
    product_selling_points = Column(
        Text,
        nullable=True,
        comment="产品卖点描述（用于文案生成时强调重点）"
    )

    # 关联关系
    generation_tasks = relationship("GenerationTask", back_populates="material", foreign_keys="GenerationTask.material_id")
    attachments = relationship(
        "MaterialAttachment",
        back_populates="material",
        foreign_keys="MaterialAttachment.material_id",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Material(id={self.id}, title={self.title})>"
