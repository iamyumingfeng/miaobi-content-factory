"""
素材库平台服务 (material_platform_service.py)

提供素材库平台管理相关的业务逻辑（3级分类标签体系的顶层）。

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
    MaterialPlatform,
    MaterialCategory,
    MaterialTag,
    MaterialTagRel,
    Material,
)


class MaterialPlatformService:
    """
    素材库平台服务类

    管理素材库3层分类标签体系的顶层：
    MaterialPlatform -> MaterialCategory -> MaterialTag -> Material
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_category_no_tag_count(self, category_id: int) -> int:
        """
        获取指定分类下无标签的素材数量

        素材必须通过标签关联到分类，没有标签的素材不属于任何分类。
        所以"无标签"实际上是指素材没有关联任何标签。
        这里返回 0，因为无法确定无标签素材属于哪个分类。
        """
        return 0

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
    ) -> MaterialPlatform:
        """
        创建素材平台
        
        检查同一创作管理员下是否已有同名平台
        """
        # 检查重复
        existing = await self.db.execute(
            select(MaterialPlatform).where(
                and_(
                    MaterialPlatform.name == name,
                    MaterialPlatform.owner_operator_id == owner_operator_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateResourceError(f"该平台名称 '{name}' 已存在")

        platform = MaterialPlatform(
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
    ) -> List[MaterialPlatform]:
        """
        获取素材平台列表
        
        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
            keyword: 搜索关键词（匹配名称或描述）
        """
        query = select(MaterialPlatform).options(
            selectinload(MaterialPlatform.categories),
        )

        if owner_operator_id is not None:
            query = query.where(MaterialPlatform.owner_operator_id == owner_operator_id)

        if keyword:
            query = query.where(
                or_(
                    MaterialPlatform.name.contains(keyword),
                    MaterialPlatform.description.contains(keyword),
                )
            )

        query = query.order_by(MaterialPlatform.sort_order, MaterialPlatform.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_platform(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[MaterialPlatform]:
        """
        获取素材平台详情
        
        Args:
            platform_id: 平台ID
            owner_operator_id: 创作管理员ID，None表示超级管理员（可查看所有）
        """
        query = select(MaterialPlatform).options(
            selectinload(MaterialPlatform.categories),
        ).where(MaterialPlatform.id == platform_id)

        if owner_operator_id is not None:
            query = query.where(MaterialPlatform.owner_operator_id == owner_operator_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_platform(
        self,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
        **kwargs
    ) -> MaterialPlatform:
        """
        更新素材平台
        
        Args:
            platform_id: 平台ID
            owner_operator_id: 创作管理员ID，None表示超级管理员
            **kwargs: 可更新字段 (name, description, color, platform_code, sort_order)
        """
        platform = await self.get_platform(platform_id, owner_operator_id)
        if not platform:
            raise NotFoundError("平台不存在")

        # 如果更新名称，检查重复
        if "name" in kwargs and kwargs["name"] != platform.name:
            existing = await self.db.execute(
                select(MaterialPlatform).where(
                    and_(
                        MaterialPlatform.name == kwargs["name"],
                        MaterialPlatform.owner_operator_id == platform.owner_operator_id,
                        MaterialPlatform.id != platform_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise DuplicateResourceError(f"该平台名称 '{kwargs['name']}' 已存在")

        allowed_fields = ["name", "description", "color", "platform_code", "sort_order"]
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
        删除素材平台（级联删除关联的分类和标签）
        
        删除前检查：
        - 平台下是否有素材关联
        """
        platform = await self.get_platform(platform_id, owner_operator_id)
        if not platform:
            raise NotFoundError("平台不存在")

        # 检查平台下是否有素材关联（一次性查询所有分类）
        if platform.categories:
            category_ids = [cat.id for cat in platform.categories]
            material_count = await self.db.scalar(
                select(func.count(func.distinct(MaterialTagRel.material_id)))
                .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
                .where(MaterialTag.category_id.in_(category_ids))
            )
            if material_count and material_count > 0:
                raise ValueError(
                    f"平台下有 {material_count} 个素材关联，请先迁移或删除素材"
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
        获取素材平台分类标签完整树形结构

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
                            "material_count": 5,
                            "tag_count": 3,
                            "tags": [
                                { "id": 1, "name": "段子", "color": "#909399", "material_count": 3 }
                            ]
                        }
                    ]
                }
            ],
            "material_total": 0
        }
        """
        import logging
        logger = logging.getLogger(__name__)

        # 加载平台数据
        try:
            query = select(MaterialPlatform).where(
                MaterialPlatform.owner_operator_id == owner_operator_id
            )

            # 尝试加载关联数据
            try:
                query = query.options(
                    selectinload(MaterialPlatform.categories)
                    .selectinload(MaterialCategory.tags)
                )
            except Exception as e:
                logger.warning(f"加载关联数据失败: {e}")

            query = query.order_by(MaterialPlatform.sort_order, MaterialPlatform.name)
            result = await self.db.execute(query)
            platforms = result.scalars().all()
        except Exception as e:
            logger.error(f"加载平台数据失败: {e}")
            return {
                "platforms": [],
                "material_total": 0
            }

        # 获取所有标签的关联数量统计
        material_tag_counts = await self._get_material_tag_counts(owner_operator_id)

        # 构建树形结构
        platform_items = []
        total_materials = 0

        for platform in platforms:
            categories_list = []
            platform_material_count = 0

            for category in platform.categories:
                category_material_count = 0
                tags_list = []
                tagged_material_count = 0

                for tag in category.tags:
                    count = material_tag_counts.get(tag.id, 0)
                    tag_data = {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "material_count": count,
                        "created_at": str(tag.created_at) if tag.created_at else None,
                    }
                    tags_list.append(tag_data)
                    category_material_count += count
                    tagged_material_count += count

                # 计算该分类下无标签素材数量
                category_no_tag_count = await self.db.scalar(
                    select(func.count(func.distinct(MaterialTagRel.material_id)))
                    .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
                    .join(Material, Material.id == MaterialTagRel.material_id)
                    .where(MaterialTag.category_id == category.id)
                ) or 0
                # 无标签 = 该分类下总素材数 - 有标签的素材数
                # 但这里我们无法直接获取分类总素材数，所以用标签统计推导
                # 实际上 "无标签" 指的是没有关联任何标签的素材
                # 需要查询该分类下所有素材，排除有标签关联的
                no_tag_material_count = await self._get_category_no_tag_count(category.id)

                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "color": category.color,
                    "material_count": category_material_count,
                    "no_tag_count": no_tag_material_count,
                    "tag_count": len(tags_list),
                    "tags": tags_list,
                }
                categories_list.append(category_data)
                platform_material_count += category_material_count + no_tag_material_count

            total_materials += platform_material_count

            platform_data = {
                "id": platform.id,
                "name": platform.name,
                "description": platform.description,
                "color": platform.color,
                "category_count": len(platform.categories),
                "material_count": platform_material_count,
                "categories": categories_list,
            }
            platform_items.append(platform_data)

        return {
            "platforms": platform_items,
            "material_total": total_materials,
        }

    async def _get_material_tag_counts(
        self,
        owner_operator_id: Optional[int] = None,
    ) -> Dict[int, int]:
        """获取素材标签关联数量统计"""
        try:
            query = select(
                MaterialTagRel.tag_id,
                func.count().label("count")
            ).group_by(MaterialTagRel.tag_id)

            if owner_operator_id is not None:
                query = query.join(
                    Material,
                    Material.id == MaterialTagRel.material_id
                ).where(Material.owner_operator_id == owner_operator_id)

            result = await self.db.execute(query)
            return {row[0]: row[1] for row in result.all()}
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"获取素材标签统计失败: {e}")
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
        获取素材平台统计信息
        
        Returns:
            {
                "platform_id": int,
                "category_count": int,
                "tag_count": int,
                "total_materials": int,
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
        total_materials = await self.db.scalar(
            select(func.count(func.distinct(MaterialTagRel.material_id)))
            .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
            .join(MaterialCategory, MaterialTag.category_id == MaterialCategory.id)
            .where(MaterialCategory.material_platform_id == platform_id)
        ) or 0

        return {
            "platform_id": platform_id,
            "category_count": category_count,
            "tag_count": tag_count,
            "total_materials": total_materials,
        }
