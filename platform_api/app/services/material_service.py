"""
素材管理服务 (material_service.py)

提供素材管理相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (MaterialNotFoundError, NotFoundError,
                                 SystemResourceError)
from app.models import (GenerationTask, Material, MaterialAttachment,
                        MaterialCategory, MaterialFavorite, MaterialTag,
                        MaterialTagRel)

logger = logging.getLogger(__name__)


class MaterialService:
    """
    素材管理服务类
    """

    # ============================================
    # 素材分类管理（3级结构中间层）
    # ============================================
    @staticmethod
    async def create_material_category(
        db: AsyncSession,
        name: str,
        material_platform_id: int,
        owner_operator_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        sort_order: int = 0,
    ) -> MaterialCategory:
        """创建素材分类"""
        # 检查同一平台下是否已有同名分类
        existing = await db.execute(
            select(MaterialCategory).where(
                and_(
                    MaterialCategory.name == name,
                    MaterialCategory.material_platform_id == material_platform_id,
                    MaterialCategory.owner_operator_id == owner_operator_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"该平台下已存在名为'{name}'的分类")

        category = MaterialCategory(
            name=name,
            material_platform_id=material_platform_id,
            description=description,
            color=color,
            sort_order=sort_order,
            created_by=created_by or owner_operator_id,
            owner_operator_id=owner_operator_id,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def list_material_categories(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        platform_id: Optional[int] = None,
    ) -> List[MaterialCategory]:
        """获取素材分类列表"""
        query = select(MaterialCategory)

        if owner_operator_id is not None:
            query = query.where(MaterialCategory.owner_operator_id == owner_operator_id)

        if platform_id is not None:
            query = query.where(MaterialCategory.material_platform_id == platform_id)

        query = query.order_by(MaterialCategory.sort_order, MaterialCategory.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_material_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[MaterialCategory]:
        """获取素材分类详情"""
        query = select(MaterialCategory).where(MaterialCategory.id == category_id)

        if owner_operator_id is not None:
            query = query.where(MaterialCategory.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_material_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
        **kwargs,
    ) -> MaterialCategory:
        """更新素材分类"""
        category = await MaterialService.get_material_category(
            db, category_id, owner_operator_id
        )
        if not category:
            raise NotFoundError(message="分类不存在")

        # 如果更新名称，检查重复
        if "name" in kwargs and kwargs["name"] != category.name:
            existing = await db.execute(
                select(MaterialCategory).where(
                    and_(
                        MaterialCategory.name == kwargs["name"],
                        MaterialCategory.material_platform_id
                        == category.material_platform_id,
                        MaterialCategory.owner_operator_id
                        == category.owner_operator_id,
                        MaterialCategory.id != category_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"该平台下已存在名为'{kwargs['name']}'的分类")

        for key, value in kwargs.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)

        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete_material_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """删除素材分类（级联删除标签）"""
        category = await MaterialService.get_material_category(
            db, category_id, owner_operator_id
        )
        if not category:
            raise NotFoundError(message="分类不存在")

        # 获取分类下标签关联的素材数量
        material_count = await db.scalar(
            select(func.count(func.distinct(MaterialTagRel.material_id)))
            .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
            .where(MaterialTag.category_id == category_id)
        )

        if material_count and material_count > 0:
            raise ValueError(
                f"该分类下有 {material_count} 个素材关联，请先迁移或删除标签"
            )

        await db.delete(category)
        await db.commit()
        return True

    @staticmethod
    async def count_tags_by_category(db: AsyncSession, category_id: int) -> int:
        """统计分类下的标签数量"""
        result = await db.scalar(
            select(func.count(MaterialTag.id)).where(
                MaterialTag.category_id == category_id
            )
        )
        return result or 0

    # ============================================
    # 素材标签管理（更新为3级结构）
    # ============================================
    @staticmethod
    async def create_material_tag(
        db: AsyncSession,
        name: str,
        owner_operator_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> MaterialTag:
        """
        创建素材标签（3级结构）

        CategoryPlatform -> MaterialCategory -> MaterialTag

        Args:
            category_id: 所属分类ID，None表示未分类标签
        """
        # 检查同一分类下是否已有同名标签
        if category_id is not None:
            existing = await db.execute(
                select(MaterialTag).where(
                    and_(
                        MaterialTag.name == name,
                        MaterialTag.category_id == category_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"该分类下已存在名为'{name}'的标签")

        tag = MaterialTag(
            name=name,
            description=description,
            color=color,
            created_by=created_by or owner_operator_id,
            owner_operator_id=owner_operator_id,
            category_id=category_id,
        )

        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def list_material_tags(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[MaterialTag]:
        """
        获取素材标签列表

        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
            category_id: 分类ID筛选，传具体值表示查询某分类下的标签
        """
        query = select(MaterialTag)

        if owner_operator_id is not None:
            query = query.where(MaterialTag.owner_operator_id == owner_operator_id)

        if category_id is not None:
            query = query.where(MaterialTag.category_id == category_id)

        query = query.order_by(
            MaterialTag.is_system.desc(), MaterialTag.created_at.desc()
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_material_tag(
        db: AsyncSession,
        tag_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[MaterialTag]:
        """
        获取素材标签详情
        """
        query = select(MaterialTag).where(MaterialTag.id == tag_id)

        if owner_operator_id:
            query = query.where(MaterialTag.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_material_tag(
        db: AsyncSession,
        tag_id: int,
        owner_operator_id: Optional[int],
        is_super_admin: bool = False,
        **kwargs,
    ) -> Optional[MaterialTag]:
        """
        更新素材标签

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可更新所有标签）
        """
        query = select(MaterialTag).where(MaterialTag.id == tag_id)

        if not is_super_admin and owner_operator_id is not None:
            query = query.where(MaterialTag.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise NotFoundError("标签不存在")

        allowed_fields = ["name", "description", "color"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(tag, field, value)

        tag.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def delete_material_tag(
        db: AsyncSession,
        tag_id: int,
        owner_operator_id: Optional[int],
        is_super_admin: bool = False,
    ) -> None:
        """
        删除素材标签（系统默认标签不可删除）

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可删除所有标签）
        """
        query = select(MaterialTag).where(MaterialTag.id == tag_id)

        if not is_super_admin and owner_operator_id is not None:
            query = query.where(MaterialTag.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise NotFoundError("标签不存在")

        # 检查是否为系统默认标签
        if tag.is_system:
            raise SystemResourceError("系统默认标签不可删除")

        await db.delete(tag)
        await db.commit()

    @staticmethod
    async def count_materials_by_tag(
        db: AsyncSession,
        tag_id: int,
    ) -> int:
        """
        统计标签下的素材数量
        """
        query = (
            select(func.count())
            .select_from(MaterialTagRel)
            .where(MaterialTagRel.tag_id == tag_id)
        )
        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def get_category_stats(
        db: AsyncSession,
        category_id: int,
    ) -> Dict[str, Any]:
        """
        获取分类统计信息

        Returns:
            {
                "category_id": int,
                "material_count": int,
                "tag_count": int,
            }
        """
        # 统计分类下的标签数量
        tag_count_result = await db.execute(
            select(func.count())
            .select_from(MaterialTag)
            .where(MaterialTag.category_id == category_id)
        )
        tag_count = tag_count_result.scalar() or 0

        # 统计分类下的素材数量（通过标签关联）
        material_count_result = await db.execute(
            select(func.count(func.distinct(MaterialTagRel.material_id)))
            .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
            .where(MaterialTag.category_id == category_id)
        )
        material_count = material_count_result.scalar() or 0

        return {
            "category_id": category_id,
            "material_count": material_count,
            "tag_count": tag_count,
        }

    @staticmethod
    async def get_tag_summary(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
    ) -> dict:
        """
        获取标签统计摘要

        Returns:
            {
                "total": int,  # 素材总数
                "no_tag_count": int,  # 无标签素材数量
                "tag_counts": { tag_id: count }  # 各标签素材数量
            }
        """
        # 1. 获取素材总数
        total_query = select(func.count()).select_from(Material)
        if owner_operator_id is not None:
            total_query = total_query.where(
                Material.owner_operator_id == owner_operator_id
            )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        # 2. 获取无标签素材数量
        no_tag_query = (
            select(func.count())
            .select_from(Material)
            .where(Material.id.not_in(select(MaterialTagRel.material_id).distinct()))
        )
        if owner_operator_id is not None:
            no_tag_query = no_tag_query.where(
                Material.owner_operator_id == owner_operator_id
            )
        no_tag_result = await db.execute(no_tag_query)
        no_tag_count = no_tag_result.scalar() or 0

        # 3. 获取各标签素材数量
        tag_count_query = select(
            MaterialTagRel.tag_id, func.count().label("count")
        ).group_by(MaterialTagRel.tag_id)

        # 如果需要按管理员过滤，需要 join Material 表
        if owner_operator_id is not None:
            tag_count_query = tag_count_query.join(
                Material, Material.id == MaterialTagRel.material_id
            ).where(Material.owner_operator_id == owner_operator_id)

        tag_count_result = await db.execute(tag_count_query)
        tag_counts = {row[0]: row[1] for row in tag_count_result.all()}

        return {
            "total": total,
            "no_tag_count": no_tag_count,
            "tag_counts": tag_counts,
        }

    @staticmethod
    async def get_material_ids_by_tag(
        db: AsyncSession,
        tag_id: int,
    ) -> List[int]:
        """
        获取标签下的所有素材ID列表
        """
        query = select(MaterialTagRel.material_id).where(
            MaterialTagRel.tag_id == tag_id
        )
        result = await db.execute(query)
        return [row[0] for row in result.all()]

    @staticmethod
    async def migrate_tag_materials(
        db: AsyncSession,
        source_tag_id: int,
        target_tag_id: int,
    ) -> int:
        """
        将源标签下的所有素材迁移到目标标签

        Returns:
            迁移的素材数量
        """
        # 获取源标签下的所有素材关联
        query = select(MaterialTagRel).where(MaterialTagRel.tag_id == source_tag_id)
        result = await db.execute(query)
        tag_rels = result.scalars().all()

        migrated_count = 0
        for rel in tag_rels:
            # 检查素材是否已有关联目标标签
            existing_query = select(MaterialTagRel).where(
                and_(
                    MaterialTagRel.material_id == rel.material_id,
                    MaterialTagRel.tag_id == target_tag_id,
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                # 已有关联目标标签，删除源标签关联
                await db.delete(rel)
            else:
                # 无关联目标标签，修改源标签关联为目标标签
                rel.tag_id = target_tag_id

            migrated_count += 1

        await db.commit()
        return migrated_count

    @staticmethod
    async def batch_migrate_materials(
        db: AsyncSession,
        material_ids: List[int],
        target_tag_id: int,
        source_tag_id: Optional[int] = None,
    ) -> int:
        """
        批量迁移素材到目标标签

        Args:
            material_ids: 要迁移的素材ID列表
            target_tag_id: 目标标签ID
            source_tag_id: 源标签ID（可选，如提供则只迁移该标签的关联）

        Returns:
            成功迁移的素材数量
        """
        if not material_ids:
            return 0

        migrated_count = 0

        for material_id in material_ids:
            # 如果指定了源标签，先删除源标签关联
            if source_tag_id is not None:
                source_query = select(MaterialTagRel).where(
                    and_(
                        MaterialTagRel.material_id == material_id,
                        MaterialTagRel.tag_id == source_tag_id,
                    )
                )
                source_result = await db.execute(source_query)
                source_rel = source_result.scalar_one_or_none()
                if source_rel:
                    await db.delete(source_rel)

            # 检查是否已有关联目标标签
            existing_query = select(MaterialTagRel).where(
                and_(
                    MaterialTagRel.material_id == material_id,
                    MaterialTagRel.tag_id == target_tag_id,
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if not existing:
                # 创建新的标签关联
                new_rel = MaterialTagRel(
                    material_id=material_id,
                    tag_id=target_tag_id,
                )
                db.add(new_rel)
                migrated_count += 1

        await db.commit()
        return migrated_count

    # ============================================
    # 素材管理
    # ============================================
    @staticmethod
    async def create_material(
        db: AsyncSession,
        title: str,
        owner_operator_id: int,
        created_by: int,
        content: str,
        topic: str,
        text_content: Optional[str] = None,
        source_url: Optional[str] = None,
        source_type: str = "upload",
        content_type: str = "text",
        library_type: str = "benchmark",
        tag_ids: Optional[List[int]] = None,
    ) -> Material:
        """
        创建素材
        """
        material = Material(
            title=title,
            content=content,
            topic=topic,
            text_content=text_content,
            source_url=source_url,
            source_type=source_type,
            content_type=content_type,
            library_type=library_type,
            created_by=created_by,
            owner_operator_id=owner_operator_id,
            status="available",
        )

        db.add(material)
        await db.flush()

        # 处理标签关联
        if tag_ids:
            for tag_id in tag_ids:
                tag_rel = MaterialTagRel(
                    material_id=material.id,
                    tag_id=tag_id,
                )
                db.add(tag_rel)

        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def list_materials(
        db: AsyncSession,
        owner_operator_id: Optional[int],
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
        library_type: Optional[str] = None,
        tag_id: Optional[int] = None,
        no_tag: Optional[bool] = None,
        category_id: Optional[int] = None,
        platform_id: Optional[int] = None,
        keyword: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        favorite_user_id: Optional[int] = None,
    ) -> tuple[List[Material], int]:
        """
        获取素材列表

        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
            category_id: 分类ID，用于筛选特定分类下的素材
            platform_id: 平台ID，用于筛选特定平台下的素材
        """
        query = select(Material).options(selectinload(Material.attachments))
        if owner_operator_id is not None:
            query = query.where(Material.owner_operator_id == owner_operator_id)

        if status:
            query = query.where(Material.status == status)

        if content_type:
            query = query.where(Material.content_type == content_type)

        if library_type:
            query = query.where(Material.library_type == library_type)

        if keyword:
            query = query.where(
                or_(
                    Material.title.contains(keyword),
                    Material.text_content.contains(keyword),
                )
            )

        if tag_id:
            query = query.join(
                MaterialTagRel,
                and_(
                    MaterialTagRel.material_id == Material.id,
                    MaterialTagRel.tag_id == tag_id,
                ),
            )

        if category_id is not None:
            # 按分类筛选：通过标签关联找到该分类下的素材
            query = (
                query.join(MaterialTagRel, MaterialTagRel.material_id == Material.id)
                .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
                .where(MaterialTag.category_id == category_id)
            )

        if platform_id is not None:
            # 按平台筛选：通过分类->标签关联找到该平台下的素材
            query = (
                query.join(MaterialTagRel, MaterialTagRel.material_id == Material.id)
                .join(MaterialTag, MaterialTagRel.tag_id == MaterialTag.id)
                .join(MaterialCategory, MaterialTag.category_id == MaterialCategory.id)
                .where(MaterialCategory.material_platform_id == platform_id)
            )

        if no_tag:
            # 仅筛选无标签的素材
            # 如果有 category_id，需要确保素材不属于该分类下的任何标签
            if category_id is not None:
                # 获取该分类下的所有标签ID
                tag_ids_subquery = select(MaterialTag.id).where(
                    MaterialTag.category_id == category_id
                )
                # 排除这些标签关联的素材
                tagged_materials_subquery = select(MaterialTagRel.material_id).where(
                    MaterialTagRel.tag_id.in_(tag_ids_subquery)
                )
                query = query.where(Material.id.not_in(tagged_materials_subquery))
            else:
                # 没有分类限制，筛选所有无标签素材
                subquery = select(MaterialTagRel.material_id).distinct()
                query = query.where(Material.id.not_in(subquery))

        if is_favorite is not None and favorite_user_id:
            if is_favorite:
                # 只查询收藏的素材
                query = query.join(
                    MaterialFavorite,
                    and_(
                        MaterialFavorite.material_id == Material.id,
                        MaterialFavorite.user_id == favorite_user_id,
                    ),
                )
            else:
                # 只查询未收藏的素材
                subquery = select(MaterialFavorite.material_id).where(
                    MaterialFavorite.user_id == favorite_user_id
                )
                query = query.where(Material.id.not_in(subquery))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(Material.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        # 动态转换 URL（旧数据可能存的是本地路径）
        from app.services.storage_service import get_storage_service

        storage = get_storage_service()
        for item in items:
            for attachment in item.attachments:
                attachment.file_url = storage.convert_url(attachment.file_url)
                if attachment.thumbnail_url:
                    attachment.thumbnail_url = storage.convert_url(
                        attachment.thumbnail_url
                    )

        return items, total

    @staticmethod
    async def get_material(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[Material]:
        """
        获取素材详情

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可查看所有素材）
        """
        query = select(Material).where(Material.id == material_id)

        if owner_operator_id is not None:
            query = query.where(Material.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_material(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: Optional[int],
        **kwargs,
    ) -> Optional[Material]:
        """
        更新素材

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可更新所有素材）
        """
        query = select(Material).where(Material.id == material_id)
        if owner_operator_id is not None:
            query = query.where(
                and_(
                    Material.id == material_id,
                    Material.owner_operator_id == owner_operator_id,
                )
            )

        result = await db.execute(query)
        material = result.scalar_one_or_none()
        if not material:
            raise MaterialNotFoundError()

        # 更新字段
        allowed_fields = [
            "title",
            "content",
            "topic",
            "text_content",
            "source_url",
            "source_type",
            "content_type",
            "status",
            "library_type",
        ]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(material, field, value)

        # 处理转移操作（特殊字段，用于超级管理员转移素材所有权）
        if (
            "owner_operator_id_new" in kwargs
            and kwargs["owner_operator_id_new"] is not None
        ):
            material.owner_operator_id = kwargs["owner_operator_id_new"]

        # 处理标签关联更新
        if "tag_ids" in kwargs:
            await MaterialService.update_material_tags(
                db, material_id, kwargs["tag_ids"]
            )

        material.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def update_material_tags(
        db: AsyncSession,
        material_id: int,
        tag_ids: Optional[List[int]],
    ) -> None:
        """
        更新素材的标签关联

        Args:
            tag_ids: 标签ID列表，为空列表表示删除所有标签，为None则不修改
        """
        if tag_ids is None:
            return

        # 获取当前所有标签关联
        query = select(MaterialTagRel).where(MaterialTagRel.material_id == material_id)
        result = await db.execute(query)
        existing_rels = result.scalars().all()
        existing_tag_ids = {rel.tag_id for rel in existing_rels}

        new_tag_ids = set(tag_ids)

        # 需要删除的关联
        to_delete = existing_tag_ids - new_tag_ids
        for rel in existing_rels:
            if rel.tag_id in to_delete:
                await db.delete(rel)

        # 需要新增的关联
        to_add = new_tag_ids - existing_tag_ids
        for tag_id in to_add:
            new_rel = MaterialTagRel(
                material_id=material_id,
                tag_id=tag_id,
            )
            db.add(new_rel)

    @staticmethod
    async def delete_material(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: Optional[int],
    ) -> bool:
        """
        删除素材（级联删除关联的附件、标签关联、收藏记录、物理文件）

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可删除所有素材）
        """
        from app.models import (MaterialAttachment, MaterialFavorite,
                                MaterialTagRel)
        from app.services.storage_service import (ResourceType,
                                                  get_storage_service)

        query = select(Material).where(Material.id == material_id)
        if owner_operator_id is not None:
            query = query.where(
                and_(
                    Material.id == material_id,
                    Material.owner_operator_id == owner_operator_id,
                )
            )

        result = await db.execute(query)
        material = result.scalar_one_or_none()
        if not material:
            raise MaterialNotFoundError()

        logger.info(
            f"[MaterialService] Deleting material: id={material_id}, owner_operator_id={owner_operator_id}"
        )

        # 0. 删除磁盘上的物理文件（原图 + 缩略图）
        try:
            storage = get_storage_service()
            storage.delete_material(
                owner_admin_id=material.owner_operator_id,
                resource_type=ResourceType.IMAGE,
                resource_id=material_id,
            )
            logger.info(
                f"[MaterialService] Deleted physical files for material_id={material_id}"
            )
        except Exception as e:
            logger.warning(f"[MaterialService] Failed to delete physical files: {e}")

        # 1. 删除关联的附件记录
        delete_attachments_query = delete(MaterialAttachment).where(
            MaterialAttachment.material_id == material_id
        )
        attachments_result = await db.execute(delete_attachments_query)
        logger.info(
            f"[MaterialService] Deleted attachments: count={attachments_result.rowcount}"
        )

        # 2. 删除标签关联
        delete_tag_rels_query = delete(MaterialTagRel).where(
            MaterialTagRel.material_id == material_id
        )
        tag_rels_result = await db.execute(delete_tag_rels_query)
        logger.info(
            f"[MaterialService] Deleted tag relations: count={tag_rels_result.rowcount}"
        )

        # 3. 删除收藏记录
        delete_favorites_query = delete(MaterialFavorite).where(
            MaterialFavorite.material_id == material_id
        )
        favorites_result = await db.execute(delete_favorites_query)
        logger.info(
            f"[MaterialService] Deleted favorites: count={favorites_result.rowcount}"
        )

        # 4. 最后删除素材
        await db.delete(material)
        await db.commit()
        logger.info(
            f"[MaterialService] Material deleted successfully: id={material_id}"
        )
        return True

    @staticmethod
    async def copy_material(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: int,
        new_title: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
    ) -> Optional[Material]:
        """
        复制素材

        Args:
            tag_ids: 指定新素材关联的标签ID列表，为空则复制原素材的标签关联
        """
        # 获取原素材（超级管理员可查看所有素材，所以传None）
        original = await MaterialService.get_material(db, material_id, None)
        if not original:
            raise MaterialNotFoundError()

        # 创建新素材
        material = Material(
            title=new_title or f"{original.title} (副本)",
            content=original.content,
            topic=original.topic,
            text_content=original.text_content,
            source_url=original.source_url,
            source_type=original.source_type,
            content_type=original.content_type,
            library_type=original.library_type,
            created_by=original.created_by,
            owner_operator_id=owner_operator_id,
            status="available",
        )

        db.add(material)
        await db.flush()

        # 处理标签关联
        if tag_ids is not None:
            # 使用指定的标签列表（包括空列表表示无标签）
            for tag_id in tag_ids:
                # 验证标签存在且属于目标管理员
                tag = await MaterialService.get_material_tag(
                    db, tag_id, owner_operator_id
                )
                if tag:
                    new_tag_rel = MaterialTagRel(
                        material_id=material.id,
                        tag_id=tag_id,
                    )
                    db.add(new_tag_rel)
        else:
            # 复制原素材的标签关联
            original_tag_rels = await db.execute(
                select(MaterialTagRel).where(MaterialTagRel.material_id == original.id)
            )
            for tag_rel in original_tag_rels.scalars().all():
                new_tag_rel = MaterialTagRel(
                    material_id=material.id,
                    tag_id=tag_rel.tag_id,
                )
                db.add(new_tag_rel)

        # 复制附件
        original_attachments = await db.execute(
            select(MaterialAttachment).where(
                MaterialAttachment.material_id == original.id
            )
        )
        for attachment in original_attachments.scalars().all():
            new_attachment = MaterialAttachment(
                material_id=material.id,
                file_type=attachment.file_type,
                file_url=attachment.file_url,
                file_name=attachment.file_name,
                file_size=attachment.file_size,
                sort_order=attachment.sort_order,
                width=attachment.width,
                height=attachment.height,
                duration=attachment.duration,
                thumbnail_url=attachment.thumbnail_url,
            )
            db.add(new_attachment)

        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def batch_transfer_materials(
        db: AsyncSession,
        material_ids: List[int],
        target_operator_id: int,
        target_tag_ids: List[int],
    ) -> dict:
        """
        批量迁移素材到目标管理员（超级管理员专用）

        将选中的素材完整迁移（含图片附件）到指定目标管理员，并设置新标签。
        迁移后原素材将被删除。

        Args:
            material_ids: 要迁移的素材ID列表
            target_operator_id: 目标管理员ID
            target_tag_ids: 目标标签ID列表

        Returns:
            {
                "total_count": 总数量,
                "success_count": 成功数量,
                "failed_count": 失败数量,
                "failed_ids": [失败的素材ID],
                "created_material_ids": [新创建的素材ID]
            }
        """
        total_count = len(material_ids)
        success_count = 0
        failed_count = 0
        failed_ids = []
        created_material_ids = []

        # 验证所有目标标签存在且属于目标管理员
        for tag_id in target_tag_ids:
            tag = await MaterialService.get_material_tag(db, tag_id, target_operator_id)
            if not tag:
                raise ValueError(f"标签 {tag_id} 不存在或不属于目标管理员")

        for material_id in material_ids:
            try:
                # 获取原素材（超级管理员可查看所有素材，所以传None）
                original = await MaterialService.get_material(db, material_id, None)
                if not original:
                    raise MaterialNotFoundError(f"素材 {material_id} 不存在")

                # 创建新素材记录
                new_material = Material(
                    title=original.title,
                    content=original.content,
                    topic=original.topic,
                    text_content=original.text_content,
                    source_url=original.source_url,
                    source_type=original.source_type,
                    content_type=original.content_type,
                    library_type=original.library_type,
                    created_by=original.created_by,
                    owner_operator_id=target_operator_id,
                    status=original.status,
                    image_count=original.image_count,
                    video_count=original.video_count,
                )

                db.add(new_material)
                await db.flush()

                # 设置新标签关联
                for tag_id in target_tag_ids:
                    new_tag_rel = MaterialTagRel(
                        material_id=new_material.id,
                        tag_id=tag_id,
                    )
                    db.add(new_tag_rel)

                # 复制附件
                original_attachments = await db.execute(
                    select(MaterialAttachment).where(
                        MaterialAttachment.material_id == original.id
                    )
                )
                for attachment in original_attachments.scalars().all():
                    new_attachment = MaterialAttachment(
                        material_id=new_material.id,
                        file_type=attachment.file_type,
                        file_url=attachment.file_url,
                        file_name=attachment.file_name,
                        file_size=attachment.file_size,
                        sort_order=attachment.sort_order,
                        width=attachment.width,
                        height=attachment.height,
                        duration=attachment.duration,
                        thumbnail_url=attachment.thumbnail_url,
                    )
                    db.add(new_attachment)

                # 删除原素材前：处理关联表（避免外键约束报错）
                # 1. 将生成任务指向新素材
                generation_tasks = await db.execute(
                    select(GenerationTask).where(
                        GenerationTask.material_id == original.id
                    )
                )
                for task in generation_tasks.scalars().all():
                    task.material_id = new_material.id

                # 2. 删除原素材的标签关联
                await db.execute(
                    delete(MaterialTagRel).where(
                        MaterialTagRel.material_id == original.id
                    )
                )

                # 3. 删除原素材的收藏记录
                await db.execute(
                    delete(MaterialFavorite).where(
                        MaterialFavorite.material_id == original.id
                    )
                )

                # 4. 删除原素材的附件（数据库外键无CASCADE，需手动删除）
                await db.execute(
                    delete(MaterialAttachment).where(
                        MaterialAttachment.material_id == original.id
                    )
                )

                # 5. 删除原素材
                await db.delete(original)

                created_material_ids.append(new_material.id)
                success_count += 1

            except Exception as e:
                logger.error(f"迁移素材 {material_id} 失败: {str(e)}")
                failed_ids.append(material_id)
                failed_count += 1
                # 继续处理下一个素材

        await db.commit()

        return {
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
            "created_material_ids": created_material_ids,
        }

    # ============================================
    # 素材附件管理
    # ============================================
    @staticmethod
    async def add_material_attachment(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: int,
        file_type: str,
        file_url: str,
        file_name: str,
        file_size: Optional[int] = None,
        sort_order: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[float] = None,
        thumbnail_url: Optional[str] = None,
    ) -> MaterialAttachment:
        """
        添加素材附件
        """
        logger.info(
            f"[MaterialService] Adding attachment: material_id={material_id}, "
            f"owner_operator_id={owner_operator_id}, file_type={file_type}, "
            f"file_url={file_url}, file_name={file_name}, file_size={file_size}, "
            f"thumbnail_url={thumbnail_url}"
        )

        # 验证素材所有权
        material = await MaterialService.get_material(
            db, material_id, owner_operator_id
        )
        if not material:
            logger.error(
                f"[MaterialService] Material not found: material_id={material_id}, owner_operator_id={owner_operator_id}"
            )
            raise MaterialNotFoundError()

        attachment = MaterialAttachment(
            material_id=material_id,
            file_type=file_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            sort_order=sort_order,
            width=width,
            height=height,
            duration=duration,
            thumbnail_url=thumbnail_url,
        )

        db.add(attachment)
        await db.flush()

        # 更新素材的图片/视频数量
        if file_type == "image":
            material.image_count += 1
        elif file_type == "video":
            material.video_count += 1

        await db.commit()
        await db.refresh(attachment)

        logger.info(
            f"[MaterialService] Attachment saved: id={attachment.id}, material_id={material_id}, "
            f"file_url={attachment.file_url}, thumbnail_url={attachment.thumbnail_url}"
        )
        return attachment

    @staticmethod
    async def list_material_attachments(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> List[MaterialAttachment]:
        """
        获取素材附件列表
        """
        logger.debug(
            f"[MaterialService] Querying attachments: material_id={material_id}, owner_operator_id={owner_operator_id}"
        )

        # 验证素材所有权
        if owner_operator_id:
            material = await MaterialService.get_material(
                db, material_id, owner_operator_id
            )
            if not material:
                logger.warning(
                    f"[MaterialService] Material not found for attachment query: "
                    f"material_id={material_id}, owner_operator_id={owner_operator_id}"
                )
                raise MaterialNotFoundError()

        query = select(MaterialAttachment).where(
            MaterialAttachment.material_id == material_id
        )
        query = query.order_by(
            MaterialAttachment.sort_order.asc(), MaterialAttachment.created_at.asc()
        )

        result = await db.execute(query)
        attachments = result.scalars().all()

        # 动态转换 URL（旧数据可能存的是本地路径）
        from app.services.storage_service import get_storage_service

        storage = get_storage_service()
        for attachment in attachments:
            attachment.file_url = storage.convert_url(attachment.file_url)
            if attachment.thumbnail_url:
                attachment.thumbnail_url = storage.convert_url(attachment.thumbnail_url)

        logger.debug(
            f"[MaterialService] Found attachments: material_id={material_id}, count={len(attachments)}, "
            f"urls={[a.file_url for a in attachments]}"
        )
        return attachments

    @staticmethod
    async def delete_material_attachment(
        db: AsyncSession,
        attachment_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        删除素材附件
        """
        logger.info(
            f"[MaterialService] Deleting attachment: attachment_id={attachment_id}, owner_operator_id={owner_operator_id}"
        )

        query = select(MaterialAttachment).where(MaterialAttachment.id == attachment_id)
        result = await db.execute(query)
        attachment = result.scalar_one_or_none()

        if not attachment:
            logger.warning(
                f"[MaterialService] Attachment not found: attachment_id={attachment_id}"
            )
            raise NotFoundError(message="附件不存在")

        # 验证素材所有权
        if owner_operator_id:
            material = await MaterialService.get_material(
                db, attachment.material_id, owner_operator_id
            )
            if not material:
                logger.warning(
                    f"[MaterialService] Material not found for attachment deletion: "
                    f"material_id={attachment.material_id}, owner_operator_id={owner_operator_id}"
                )
                raise MaterialNotFoundError()

        # 获取素材并更新计数
        material = await MaterialService.get_material(db, attachment.material_id, None)
        if material:
            if attachment.file_type == "image":
                material.image_count = max(0, material.image_count - 1)
            elif attachment.file_type == "video":
                material.video_count = max(0, material.video_count - 1)

        # 删除附件
        await db.delete(attachment)
        await db.commit()

        logger.info(
            f"[MaterialService] Attachment deleted: attachment_id={attachment_id}"
        )
        return True

    # ============================================
    # 素材收藏管理
    # ============================================
    @staticmethod
    async def get_favorite(
        db: AsyncSession,
        material_id: int,
        user_id: int,
    ) -> Optional[MaterialFavorite]:
        """
        获取收藏记录
        """
        result = await db.execute(
            select(MaterialFavorite).where(
                and_(
                    MaterialFavorite.material_id == material_id,
                    MaterialFavorite.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_material_tags(
        db: AsyncSession,
        material_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> List[MaterialTag]:
        """
        获取素材关联的标签列表
        """
        # 验证素材所有权
        if owner_operator_id:
            material = await MaterialService.get_material(
                db, material_id, owner_operator_id
            )
            if not material:
                raise MaterialNotFoundError()

        from sqlalchemy.orm import selectinload

        query = (
            select(MaterialTag)
            .options(
                selectinload(MaterialTag.category).selectinload(
                    MaterialCategory.platform
                )
            )
            .join(
                MaterialTagRel,
                and_(
                    MaterialTagRel.tag_id == MaterialTag.id,
                    MaterialTagRel.material_id == material_id,
                ),
            )
        )
        query = query.order_by(MaterialTag.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def toggle_favorite(
        db: AsyncSession,
        material_id: int,
        user_id: int,
        owner_operator_id: int,
    ) -> bool:
        """
        切换素材收藏状态
        """
        # 验证素材所有权
        material = await MaterialService.get_material(
            db, material_id, owner_operator_id
        )
        if not material:
            raise MaterialNotFoundError()

        # 检查是否已收藏
        favorite = await MaterialService.get_favorite(db, material_id, user_id)

        if favorite:
            # 取消收藏
            await db.delete(favorite)
            await db.commit()
            return False
        else:
            # 添加收藏
            new_favorite = MaterialFavorite(
                material_id=material_id,
                user_id=user_id,
            )
            db.add(new_favorite)
            await db.commit()
            return True
