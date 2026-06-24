"""
模板库平台服务 (template_platform_service.py)

提供模板库平台管理相关的业务逻辑（3级分类标签体系的顶层）。

Author: Claude Code
Date: 2025
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, DuplicateResourceError
from app.models import (
    TemplatePlatform,
    TemplateCategory,
    TemplateTag,
    TemplateTagRel,
    Template,
)


class TemplatePlatformService:
    """
    模板库平台服务类
    
    管理模板库3层分类标签体系的顶层：
    TemplatePlatform -> TemplateCategory -> TemplateTag -> Template
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # 平台基础 CRUD
    # ============================================
    async def create_platform(
        self,
        name: str,
        owner_operator_id: int,
        created_by: int,
        description: Optional[str] = None,
        color: Optional[str] = None,
        platform_code: Optional[str] = None,
        sort_order: int = 0,
    ) -> TemplatePlatform:
        """
        创建模板平台
        
        检查同一创作管理员下是否已有同名平台
        """
        # 检查重复
        existing = await self.db.execute(
            select(TemplatePlatform).where(
                and_(
                    TemplatePlatform.name == name,
                    TemplatePlatform.owner_operator_id == owner_operator_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateResourceError(f"该平台名称 '{name}' 已存在")

        platform = TemplatePlatform(
            name=name,
            description=description,
            color=color,
            platform_code=platform_code,
            sort_order=sort_order,
            created_by=created_by,
            owner_operator_id=owner_operator_id,
        )
        self.db.add(platform)
        await self.db.commit()
        await self.db.refresh(platform)
        return platform

    async def get_platforms(
        self,
        owner_operator_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> List[TemplatePlatform]:
        """
        获取模板平台列表
        
        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
            keyword: 搜索关键词（匹配名称或描述）
        """
        query = select(TemplatePlatform).options(
            selectinload(TemplatePlatform.categories),
        )

        if owner_operator_id is not None:
            query = query.where(TemplatePlatform.owner_operator_id == owner_operator_id)

        if keyword:
            query = query.where(
                or_(
                    TemplatePlatform.name.contains(keyword),
                    TemplatePlatform.description.contains(keyword),
                )
            )

        query = query.order_by(TemplatePlatform.sort_order, TemplatePlatform.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_platform(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[TemplatePlatform]:
        """
        获取模板平台详情
        
        Args:
            platform_id: 平台ID
            owner_operator_id: 创作管理员ID，None表示超级管理员（可查看所有）
        """
        query = select(TemplatePlatform).where(TemplatePlatform.id == platform_id)

        if owner_operator_id is not None:
            query = query.where(TemplatePlatform.owner_operator_id == owner_operator_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_platform(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
        **kwargs
    ) -> TemplatePlatform:
        """
        更新模板平台
        
        Args:
            platform_id: 平台ID
            owner_operator_id: 创作管理员ID，None表示超级管理员
            **kwargs: 可更新字段 (name, description, color, platform_code, sort_order, rules_config_json)
        """
        platform = await self.get_platform(platform_id, owner_operator_id)
        if not platform:
            raise NotFoundError("平台不存在")

        # 如果更新名称，检查重复
        if "name" in kwargs and kwargs["name"] != platform.name:
            existing = await self.db.execute(
                select(TemplatePlatform).where(
                    and_(
                        TemplatePlatform.name == kwargs["name"],
                        TemplatePlatform.owner_operator_id == platform.owner_operator_id,
                        TemplatePlatform.id != platform_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise DuplicateResourceError(f"该平台名称 '{kwargs['name']}' 已存在")

        allowed_fields = ["name", "description", "color", "platform_code", "sort_order", "rules_config_json"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(platform, field, value)

        platform.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(platform)
        return platform

    async def delete_platform(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        删除模板平台（级联删除关联的分类和标签）
        
        删除前检查：
        - 分类下是否有模板关联
        """
        platform = await self.get_platform(platform_id, owner_operator_id)
        if not platform:
            raise NotFoundError("平台不存在")

        # 检查分类下是否有内容关联
        for category in platform.categories:
            template_count = await self.db.scalar(
                select(func.count(func.distinct(TemplateTagRel.template_id)))
                .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
                .where(TemplateTag.category_id == category.id)
            )
            if template_count and template_count > 0:
                raise ValueError(
                    f"平台下的分类 '{category.name}' 有 {template_count} 个模板关联，"
                    f"请先迁移或删除标签"
                )

        await self.db.delete(platform)
        await self.db.commit()
        return True

    # ============================================
    # 平台树形结构 API
    # ============================================
    async def get_platform_tree(
        self,
        owner_operator_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取模板平台分类标签完整树形结构

        返回格式（与前端 CategoryTreeResponse 匹配）:
        {
            "platforms": [
                {
                    "id": 1,
                    "name": "抖音",
                    "color": "#409EFF",
                    "category_count": 2,
                    "categories": [
                        {
                            "id": 1,
                            "name": "搞笑",
                            "color": "#67C23A",
                            "template_count": 5,
                            "tag_count": 3,
                            "tags": [
                                { "id": 1, "name": "段子", "color": "#909399", "template_count": 3 }
                            ]
                        }
                    ]
                }
            ],
            "template_total": 0
        }
        """
        import logging
        logger = logging.getLogger(__name__)

        # 加载平台数据
        try:
            query = select(TemplatePlatform).where(
                TemplatePlatform.owner_operator_id == owner_operator_id
            )

            # 尝试加载关联数据
            try:
                query = query.options(
                    selectinload(TemplatePlatform.categories)
                    .selectinload(TemplateCategory.tags)
                )
            except Exception as e:
                logger.warning(f"加载关联数据失败: {e}")

            query = query.order_by(TemplatePlatform.sort_order, TemplatePlatform.name)
            result = await self.db.execute(query)
            platforms = result.scalars().all()
        except Exception as e:
            logger.error(f"加载平台数据失败: {e}")
            return {
                "platforms": [],
                "template_total": 0
            }

        # 获取所有标签的关联数量统计
        template_tag_counts = await self._get_template_tag_counts(owner_operator_id)

        # 构建树形结构
        platform_items = []
        total_templates = 0

        for platform in platforms:
            categories_list = []
            platform_template_count = 0

            for category in platform.categories:
                category_template_count = 0
                tags_list = []

                for tag in category.tags:
                    count = template_tag_counts.get(tag.id, 0)
                    tag_data = {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "template_count": count,
                        "created_at": str(tag.created_at) if tag.created_at else None,
                    }
                    tags_list.append(tag_data)
                    category_template_count += count

                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "color": category.color,
                    "template_count": category_template_count,
                    "tag_count": len(tags_list),
                    "tags": tags_list,
                }
                categories_list.append(category_data)
                platform_template_count += category_template_count

            total_templates += platform_template_count

            platform_data = {
                "id": platform.id,
                "name": platform.name,
                "description": platform.description,
                "color": platform.color,
                "category_count": len(platform.categories),
                "template_count": platform_template_count,
                "categories": categories_list,
            }
            platform_items.append(platform_data)

        return {
            "platforms": platform_items,
            "template_total": total_templates,
        }

    async def _get_template_tag_counts(
        self,
        owner_operator_id: Optional[int] = None,
    ) -> Dict[int, int]:
        """获取模板标签关联数量统计"""
        try:
            query = select(
                TemplateTagRel.tag_id,
                func.count().label("count")
            ).group_by(TemplateTagRel.tag_id)

            if owner_operator_id is not None:
                query = query.join(
                    Template,
                    Template.id == TemplateTagRel.template_id
                ).where(Template.owner_operator_id == owner_operator_id)

            result = await self.db.execute(query)
            return {row[0]: row[1] for row in result.all()}
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"获取模板标签统计失败: {e}")
            return {}

    # ============================================
    # 统计查询
    # ============================================
    async def get_platform_stats(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取模板平台统计信息
        
        Returns:
            {
                "platform_id": int,
                "category_count": int,
                "tag_count": int,
                "total_templates": int,
            }
        """
        platform = await self.get_platform(platform_id, owner_operator_id)
        if not platform:
            raise NotFoundError("平台不存在")

        # 统计分类数量
        category_count = len(platform.categories)

        # 统计标签数量
        tag_count = sum(len(cat.tags) for cat in platform.categories)

        # 统计关联内容数量
        total_templates = await self.db.scalar(
            select(func.count(func.distinct(TemplateTagRel.template_id)))
            .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
            .join(TemplateCategory, TemplateTag.category_id == TemplateCategory.id)
            .where(TemplateCategory.template_platform_id == platform_id)
        ) or 0

        return {
            "platform_id": platform_id,
            "category_count": category_count,
            "tag_count": tag_count,
            "total_templates": total_templates,
        }
