"""
模板管理服务 (template_service.py)

提供模板管理相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (NotFoundError, TemplateNotFoundError)
from app.models import (Template, TemplateAttachment, TemplateCategory,
                        TemplatePlatform, TemplateTag, TemplateTagRel)

logger = logging.getLogger(__name__)


class TemplateService:
    """
    模板管理服务类
    """

    # ============================================
    # 模板分类管理（3级结构中间层）
    # ============================================
    @staticmethod
    async def create_template_category(
        db: AsyncSession,
        name: str,
        template_platform_id: int,
        owner_operator_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        sort_order: int = 0,
    ) -> TemplateCategory:
        """创建模板分类"""
        # 检查同一平台下是否已有同名分类
        existing = await db.execute(
            select(TemplateCategory).where(
                and_(
                    TemplateCategory.name == name,
                    TemplateCategory.template_platform_id == template_platform_id,
                    TemplateCategory.owner_operator_id == owner_operator_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"该平台下已存在名为'{name}'的分类")

        category = TemplateCategory(
            name=name,
            template_platform_id=template_platform_id,
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
    async def list_template_categories(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        platform_id: Optional[int] = None,
    ) -> List[TemplateCategory]:
        """获取模板分类列表"""
        query = select(TemplateCategory)

        if owner_operator_id is not None:
            query = query.where(TemplateCategory.owner_operator_id == owner_operator_id)

        if platform_id is not None:
            query = query.where(TemplateCategory.template_platform_id == platform_id)

        query = query.order_by(TemplateCategory.sort_order, TemplateCategory.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_template_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[TemplateCategory]:
        """获取模板分类详情"""
        query = select(TemplateCategory).where(TemplateCategory.id == category_id)

        if owner_operator_id is not None:
            query = query.where(TemplateCategory.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_template_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
        **kwargs,
    ) -> TemplateCategory:
        """更新模板分类"""
        category = await TemplateService.get_template_category(
            db, category_id, owner_operator_id
        )
        if not category:
            raise NotFoundError(message="分类不存在")

        # 如果更新名称，检查重复
        if "name" in kwargs and kwargs["name"] != category.name:
            existing = await db.execute(
                select(TemplateCategory).where(
                    and_(
                        TemplateCategory.name == kwargs["name"],
                        TemplateCategory.template_platform_id
                        == category.template_platform_id,
                        TemplateCategory.owner_operator_id
                        == category.owner_operator_id,
                        TemplateCategory.id != category_id,
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
    async def delete_template_category(
        db: AsyncSession,
        category_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """删除模板分类（级联删除标签）"""
        category = await TemplateService.get_template_category(
            db, category_id, owner_operator_id
        )
        if not category:
            raise NotFoundError(message="分类不存在")

        # 获取分类下标签关联的模板数量
        template_count = await db.scalar(
            select(func.count(func.distinct(TemplateTagRel.template_id)))
            .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
            .where(TemplateTag.category_id == category_id)
        )

        if template_count and template_count > 0:
            raise ValueError(
                f"该分类下有 {template_count} 个模板关联，请先迁移或删除标签"
            )

        await db.delete(category)
        await db.commit()
        return True

    @staticmethod
    async def count_tags_by_category(db: AsyncSession, category_id: int) -> int:
        """统计分类下的标签数量"""
        result = await db.scalar(
            select(func.count(TemplateTag.id)).where(
                TemplateTag.category_id == category_id
            )
        )
        return result or 0

    # ============================================
    # 模板平台查询（仅供关联数据加载使用）
    # ============================================
    @staticmethod
    async def get_template_platform(
        db: AsyncSession,
        platform_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[TemplatePlatform]:
        """获取模板平台详情"""
        query = select(TemplatePlatform).where(TemplatePlatform.id == platform_id)
        if owner_operator_id:
            query = query.where(TemplatePlatform.owner_operator_id == owner_operator_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    # ============================================
    # 模板管理
    # ============================================
    @staticmethod
    async def create_template(
        db: AsyncSession,
        name: str,
        content_type: str,
        owner_operator_id: int,
        created_by: int,
        product_name: str = None,  # 默认值，向后兼容
        description: Optional[str] = None,
        prompt_template: Optional[str] = None,
        variables_json: Optional[dict] = None,
        style_reference: Optional[str] = None,
        platform_rules_json: Optional[dict] = None,
        platform_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        image_size_ratio: Optional[str] = None,
        add_watermark: Optional[bool] = True,
        viral_type: Optional[str] = None,
        product_selling_points: Optional[str] = None,
        opening_seed_id: Optional[str] = None,
        emotion_seed_id: Optional[str] = None,
        ending_seed_id: Optional[str] = None,
    ) -> Template:
        """
        创建模板
        """
        # DEBUG: 记录创建模板参数
        logger.debug(
            f"[TemplateService.create_template] name={name}, content_type={content_type}, "
            f"platform_id={platform_id}, tag_ids={tag_ids}, owner_operator_id={owner_operator_id}"
        )

        template = Template(
            name=name,
            description=description,
            content_type=content_type,
            prompt_template=prompt_template,
            variables_json=variables_json,
            style_reference=style_reference,
            platform_rules_json=platform_rules_json,
            platform_id=platform_id,
            created_by=created_by,
            owner_operator_id=owner_operator_id,
            status="enabled",
            image_size_ratio=image_size_ratio,
            add_watermark=add_watermark,
            viral_type=viral_type,
            product_name=product_name,
            product_selling_points=product_selling_points,
            opening_seed_id=opening_seed_id,
            emotion_seed_id=emotion_seed_id,
            ending_seed_id=ending_seed_id,
        )

        db.add(template)
        await db.flush()

        # DEBUG: 记录 flush 后的 template.id
        logger.debug(
            f"[TemplateService.create_template] after flush: template.id={template.id}"
        )

        # 处理标签关联
        if tag_ids:
            logger.debug(
                f"[TemplateService.create_template] processing {len(tag_ids)} tag_ids"
            )
            for tag_id in tag_ids:
                logger.debug(
                    f"[TemplateService.create_template] creating tag_rel: template_id={template.id}, tag_id={tag_id}"
                )
                tag_rel = TemplateTagRel(
                    template_id=template.id,
                    tag_id=tag_id,
                )
                db.add(tag_rel)
        else:
            logger.debug("[TemplateService.create_template] no tag_ids provided")

        await db.commit()
        await db.refresh(template)

        # DEBUG: 记录最终创建的 template
        logger.debug(
            f"[TemplateService.create_template] final template: id={template.id}, platform_id={template.platform_id}"
        )

        return template

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        owner_operator_id: Optional[int],
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
        platform_id: Optional[int] = None,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        no_tag: bool = False,
        keyword: Optional[str] = None,
    ) -> tuple[List[Template], int]:
        """
        获取模板列表

        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
        """
        logger.info(
            f"[list_templates] called with: owner_operator_id={owner_operator_id}, platform_id={platform_id}, category_id={category_id}, tag_id={tag_id}"
        )

        query = select(Template)
        if owner_operator_id is not None:
            query = query.where(Template.owner_operator_id == owner_operator_id)

        if status:
            query = query.where(Template.status == status)

        if content_type:
            query = query.where(Template.content_type == content_type)

        if platform_id:
            # 间接关联：通过标签 -> 分类 -> 平台
            # 与左侧树的统计方式一致（只通过标签关联计算）
            indirect_subq = (
                select(TemplateTagRel.template_id)
                .join(TemplateTag, TemplateTagRel.tag_id == TemplateTag.id)
                .join(TemplateCategory, TemplateTag.category_id == TemplateCategory.id)
                .where(TemplateCategory.template_platform_id == platform_id)
            )
            query = query.where(Template.id.in_(indirect_subq))
            logger.info(
                f"[list_templates] platform_id={platform_id} filter applied: indirect via category"
            )

        if keyword:
            query = query.where(Template.name.contains(keyword))

        if tag_id:
            # 直接通过 tag_id 筛选（使用 alias 避免重复 join）
            query = query.join(
                TemplateTagRel,
                and_(
                    TemplateTagRel.template_id == Template.id,
                    TemplateTagRel.tag_id == tag_id,
                ),
            )
            # 如果同时指定了 category_id，验证该 tag 是否属于该 category
            if category_id:
                tag_category_subq = (
                    select(TemplateTag.category_id)
                    .where(TemplateTag.id == tag_id)
                    .scalar_subquery()
                )
                query = query.where(tag_category_subq == category_id)
        elif category_id:
            # 仅 category_id 筛选：通过标签关联的分类来筛选
            tag_ids_subq = select(TemplateTag.id).where(
                TemplateTag.category_id == category_id
            )
            query = query.join(
                TemplateTagRel,
                and_(
                    TemplateTagRel.template_id == Template.id,
                    TemplateTagRel.tag_id.in_(tag_ids_subq),
                ),
            )

        if no_tag:
            # 筛选无标签的模板：不在 TemplateTagRel 中的模板
            tagged_ids_subq = select(TemplateTagRel.template_id).distinct()
            query = query.where(Template.id.notin_(tagged_ids_subq))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(Template.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        logger.info(f"[list_templates] returning {len(items)} items, total={total}")
        return items, total

    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[Template]:
        """
        获取模板详情

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可查看所有模板）
        """
        query = select(Template).where(Template.id == template_id)

        if owner_operator_id is not None:
            query = query.where(Template.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: int,
        owner_operator_id: Optional[int],
        **kwargs,
    ) -> Optional[Template]:
        """
        更新模板

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可更新所有模板）
        """
        query = select(Template).where(Template.id == template_id)
        if owner_operator_id is not None:
            query = query.where(Template.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if not template:
            raise TemplateNotFoundError()

        # 更新字段
        allowed_fields = [
            "name",
            "description",
            "content_type",
            "prompt_template",
            "variables_json",
            "style_reference",
            "platform_rules_json",
            "platform_id",
            "status",
            "image_count",
            "video_count",
            "image_size_ratio",
            "add_watermark",
            "viral_type",
            "product_name",
            "product_selling_points",
            "opening_seed_id",
            "emotion_seed_id",
            "ending_seed_id",
        ]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(template, field, value)

        # 处理标签关联更新（差异更新）
        if "tag_ids" in kwargs:
            tag_ids = kwargs["tag_ids"]
            if tag_ids is not None:
                await TemplateService._update_template_tag_rels(
                    db, template_id, tag_ids
                )

        template.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: int,
        owner_operator_id: Optional[int],
    ) -> bool:
        """
        删除模板（级联清理关联数据）

        Args:
            owner_operator_id: 创作管理员ID，None表示超级管理员（可删除所有模板）
        """
        from app.models import GenerationItem, GenerationTaskTemplate

        query = select(Template).where(Template.id == template_id)
        if owner_operator_id is not None:
            query = query.where(Template.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if not template:
            raise TemplateNotFoundError()

        logger.info(
            f"[TemplateService] Deleting template: id={template_id}, owner_operator_id={owner_operator_id}"
        )

        # 1. 删除标签关联
        delete_tag_rels = delete(TemplateTagRel).where(
            TemplateTagRel.template_id == template_id
        )
        tag_rels_result = await db.execute(delete_tag_rels)
        logger.info(
            f"[TemplateService] Deleted tag relations: count={tag_rels_result.rowcount}"
        )

        # 2. 删除生成任务-模板关联
        delete_task_rels = delete(GenerationTaskTemplate).where(
            GenerationTaskTemplate.template_id == template_id
        )
        task_rels_result = await db.execute(delete_task_rels)
        logger.info(
            f"[TemplateService] Deleted generation_task_template rels: count={task_rels_result.rowcount}"
        )

        # 3. 清理 generation_item 中的 template_id 引用（置空，不删除子任务）
        update_items = (
            GenerationItem.__table__.update()
            .where(GenerationItem.template_id == template_id)
            .values(template_id=None)
        )
        await db.execute(update_items)
        logger.info("[TemplateService] Cleared template_id from generation_items")

        # 4. 清理自引用外键：将引用该模板的 original_template_id 置空
        update_clones = (
            Template.__table__.update()
            .where(Template.original_template_id == template_id)
            .values(original_template_id=None)
        )
        await db.execute(update_clones)
        logger.info("[TemplateService] Cleared original_template_id references")

        # 5. 删除模板附件（TemplateAttachment）记录
        delete_attachments = delete(TemplateAttachment).where(
            TemplateAttachment.template_id == template_id
        )
        attachments_result = await db.execute(delete_attachments)
        logger.info(
            f"[TemplateService] Deleted template attachments: count={attachments_result.rowcount}"
        )

        # 6. 删除模板
        await db.delete(template)
        await db.commit()
        logger.info(
            f"[TemplateService] Template deleted successfully: id={template_id}"
        )
        return True

    @staticmethod
    async def copy_template(
        db: AsyncSession,
        template_id: int,
        owner_operator_id: int,
        new_name: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        target_platform_id: Optional[int] = None,
        target_category_id: Optional[int] = None,
    ) -> Optional[Template]:
        """
        复制模板

        Args:
            tag_ids: 可选，指定新模板的标签；为None时复制原模板的标签
            target_platform_id: 可选，指定目标平台ID
            target_category_id: 可选，指定目标分类ID（用于验证标签归属）
        """
        original = await TemplateService.get_template(
            db, template_id, owner_operator_id=None
        )
        if not original:
            raise TemplateNotFoundError()

        # 确定使用的平台ID：如果指定了目标平台ID则使用，否则使用原模板的平台ID
        final_platform_id = (
            target_platform_id if target_platform_id else original.platform_id
        )

        template = Template(
            name=new_name or f"{original.name} (副本)",
            description=original.description,
            content_type=original.content_type,
            prompt_template=original.prompt_template,
            variables_json=original.variables_json,
            style_reference=original.style_reference,
            platform_rules_json=original.platform_rules_json,
            platform_id=final_platform_id,
            original_template_id=original.id,
            created_by=owner_operator_id,
            owner_operator_id=owner_operator_id,
            status="enabled",
            image_size_ratio=original.image_size_ratio,
            add_watermark=original.add_watermark,
        )

        db.add(template)
        await db.flush()

        # 处理标签
        if tag_ids is not None and len(tag_ids) > 0:
            # 使用指定的标签
            await TemplateService._update_template_tag_rels(db, template.id, tag_ids)
        else:
            # 复制原模板的标签
            original_tag_ids_result = await db.execute(
                select(TemplateTagRel.tag_id).where(
                    TemplateTagRel.template_id == original.id
                )
            )
            original_tag_ids = [row[0] for row in original_tag_ids_result.fetchall()]
            if original_tag_ids:
                for tid in original_tag_ids:
                    db.add(TemplateTagRel(template_id=template.id, tag_id=tid))

        # 复制原模板的附件
        original_attachments_result = await db.execute(
            select(TemplateAttachment).where(
                TemplateAttachment.template_id == original.id
            )
        )
        original_attachments = original_attachments_result.scalars().all()

        image_count = 0
        video_count = 0

        for attachment in original_attachments:
            new_attachment = TemplateAttachment(
                template_id=template.id,
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

            if attachment.file_type == "image":
                image_count += 1
            elif attachment.file_type == "video":
                video_count += 1

        # 更新模板的附件计数
        template.image_count = image_count
        template.video_count = video_count

        await db.commit()
        await db.refresh(template)
        return template

    # ============================================
    # 模板标签管理
    # ============================================
    @staticmethod
    async def create_template_tag(
        db: AsyncSession,
        name: str,
        created_by: int,
        description: Optional[str] = None,
        color: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> TemplateTag:
        """
        创建模板标签（3级结构）

        CategoryPlatform -> TemplateCategory -> TemplateTag
        """
        # 检查同一分类下是否已有同名标签
        if category_id is not None:
            existing = await db.execute(
                select(TemplateTag).where(
                    and_(
                        TemplateTag.name == name,
                        TemplateTag.category_id == category_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"该分类下已存在名为'{name}'的标签")

        tag = TemplateTag(
            name=name,
            description=description,
            color=color,
            created_by=created_by,
            category_id=category_id,
        )

        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def list_template_tags(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List["TemplateTag"]:
        """
        获取模板标签列表（3级结构）

        Args:
            owner_operator_id: 创作管理员ID，None表示查询所有（仅超级管理员可用）
            category_id: 分类ID，筛选特定分类的标签
        """
        from app.models import TemplateTag

        query = select(TemplateTag)

        if owner_operator_id is not None:
            # 通过 category -> platform -> owner_operator_id 筛选
            from app.models import TemplateCategory

            category_subquery = select(TemplateCategory.id).where(
                TemplateCategory.owner_operator_id == owner_operator_id
            )
            query = query.where(
                or_(
                    and_(
                        TemplateTag.category_id.is_not(None),
                        TemplateTag.category_id.in_(category_subquery),
                    ),
                    and_(
                        TemplateTag.category_id.is_(None),
                        TemplateTag.created_by == owner_operator_id,
                    ),
                )
            )

        if category_id is not None:
            query = query.where(TemplateTag.category_id == category_id)

        query = query.order_by(
            TemplateTag.is_system.desc(), TemplateTag.created_at.desc()
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_template_tag(
        db: AsyncSession,
        tag_id: int,
        created_by: Optional[int] = None,
        is_super_admin: bool = False,
    ) -> Optional["TemplateTag"]:
        """
        获取模板标签详情
        """
        from app.models import TemplateTag

        query = select(TemplateTag).where(TemplateTag.id == tag_id)

        if created_by and not is_super_admin:
            query = query.where(TemplateTag.created_by == created_by)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_template_tag(
        db: AsyncSession,
        tag_id: int,
        created_by: int,
        is_super_admin: bool = False,
        **kwargs,
    ) -> Optional["TemplateTag"]:
        """
        更新模板标签
        """
        from app.models import TemplateTag

        query = select(TemplateTag).where(TemplateTag.id == tag_id)

        if not is_super_admin:
            query = query.where(TemplateTag.created_by == created_by)

        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise NotFoundError("标签不存在")

        allowed_fields = ["name", "description", "color", "category_id"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(tag, field, value)

        tag.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def delete_template_tag(
        db: AsyncSession,
        tag_id: int,
        created_by: int,
        is_super_admin: bool = False,
    ) -> None:
        """
        删除模板标签（系统默认标签不可删除）
        """
        from app.models import TemplateTag

        query = select(TemplateTag).where(TemplateTag.id == tag_id)

        if not is_super_admin:
            query = query.where(TemplateTag.created_by == created_by)

        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise NotFoundError("标签不存在")

        # 检查是否为系统默认标签
        if tag.is_system:
            from app.core.exceptions import SystemResourceError

            raise SystemResourceError("系统默认标签不可删除")

        await db.delete(tag)
        await db.commit()

    @staticmethod
    async def get_template_tags_by_template_id(
        db: AsyncSession,
        template_id: int,
    ) -> List[TemplateTag]:
        """
        获取模板关联的标签列表
        """
        from sqlalchemy.orm import selectinload

        from app.models import TemplateCategory, TemplateTagRel

        # DEBUG: 记录查询开始
        logger.debug(
            f"[TemplateService.get_template_tags_by_template_id] template_id={template_id}"
        )

        # 预加载 category 和 category.platform
        query = (
            select(TemplateTag)
            .options(
                selectinload(TemplateTag.category).selectinload(
                    TemplateCategory.platform
                )
            )
            .join(
                TemplateTagRel,
                and_(
                    TemplateTagRel.tag_id == TemplateTag.id,
                    TemplateTagRel.template_id == template_id,
                ),
            )
        )
        query = query.order_by(TemplateTag.created_at.desc())

        result = await db.execute(query)
        tags = result.scalars().all()

        return tags

    # ============================================
    # 标签关联内部辅助
    # ============================================
    @staticmethod
    async def _update_template_tag_rels(
        db: AsyncSession,
        template_id: int,
        new_tag_ids: List[int],
    ):
        """差异更新模板标签关联（仅增删变化部分）"""
        existing_result = await db.execute(
            select(TemplateTagRel.tag_id).where(
                TemplateTagRel.template_id == template_id
            )
        )
        existing_tag_ids = set(row[0] for row in existing_result.fetchall())
        new_tag_ids_set = set(new_tag_ids)

        to_remove = existing_tag_ids - new_tag_ids_set
        to_add = new_tag_ids_set - existing_tag_ids

        if to_remove:
            await db.execute(
                delete(TemplateTagRel).where(
                    and_(
                        TemplateTagRel.template_id == template_id,
                        TemplateTagRel.tag_id.in_(to_remove),
                    )
                )
            )
        for tid in to_add:
            db.add(TemplateTagRel(template_id=template_id, tag_id=tid))

    # ============================================
    # 批量操作
    # ============================================
    @staticmethod
    async def batch_transfer_templates(
        db: AsyncSession,
        template_ids: List[int],
        target_operator_id: int,
        target_platform_id: Optional[int] = None,
        target_category_id: Optional[int] = None,
        target_tag_ids: Optional[List[int]] = None,
    ) -> dict:
        """
        批量转移模板所有权（超级管理员专用）

        将指定模板转移到目标创作管理员名下，可选择替换平台、分类和标签。
        """
        if target_tag_ids is None:
            target_tag_ids = []

        success_count = 0
        failed_ids = []

        for tid in template_ids:
            try:
                query = select(Template).where(Template.id == tid)
                result = await db.execute(query)
                template = result.scalar_one_or_none()
                if not template:
                    failed_ids.append(tid)
                    continue

                old_owner = template.owner_operator_id
                template.owner_operator_id = target_operator_id
                # 如果指定了目标平台和分类，更新模板的平台和分类
                if target_platform_id is not None:
                    template.platform_id = target_platform_id
                if target_category_id is not None:
                    template.category_id = target_category_id
                template.updated_at = datetime.utcnow()

                # 如果指定了目标标签，替换所有标签
                if target_tag_ids or target_tag_ids == []:
                    await db.execute(
                        delete(TemplateTagRel).where(TemplateTagRel.template_id == tid)
                    )
                    for tag_id in target_tag_ids:
                        db.add(TemplateTagRel(template_id=tid, tag_id=tag_id))

                success_count += 1
                logger.info(
                    f"[TemplateService] Transferred template {tid} from owner {old_owner} to {target_operator_id}"
                )
            except Exception as e:
                logger.error(
                    f"[TemplateService] Failed to transfer template {tid}: {e}"
                )
                failed_ids.append(tid)

        await db.commit()

        return {
            "success_count": success_count,
            "failed_ids": failed_ids,
            "target_operator_id": target_operator_id,
        }

    @staticmethod
    async def migrate_tag_templates(
        db: AsyncSession,
        source_tag_id: int,
        target_tag_id: int,
    ) -> dict:
        """
        将源标签下的所有模板迁移到目标标签

        对于已关联目标标签的模板，仅移除源标签关联。
        """
        # 查找源标签下关联的模板
        source_rels = await db.execute(
            select(TemplateTagRel.template_id).where(
                TemplateTagRel.tag_id == source_tag_id
            )
        )
        template_ids = [row[0] for row in source_rels.fetchall()]

        if not template_ids:
            return {"migrated_count": 0, "template_ids": []}

        # 找出已关联目标标签的模板
        existing_target = await db.execute(
            select(TemplateTagRel.template_id).where(
                and_(
                    TemplateTagRel.tag_id == target_tag_id,
                    TemplateTagRel.template_id.in_(template_ids),
                )
            )
        )
        already_linked = set(row[0] for row in existing_target.fetchall())

        # 删除所有源标签关联
        await db.execute(
            delete(TemplateTagRel).where(TemplateTagRel.tag_id == source_tag_id)
        )

        # 为未关联目标标签的模板添加目标标签
        to_add = set(template_ids) - already_linked
        for tid in to_add:
            db.add(TemplateTagRel(template_id=tid, tag_id=target_tag_id))

        await db.commit()

        return {
            "migrated_count": len(template_ids),
            "already_linked_count": len(already_linked),
            "template_ids": template_ids,
        }

    @staticmethod
    async def batch_migrate_templates(
        db: AsyncSession,
        template_ids: List[int],
        target_tag_id: int,
        source_tag_id: Optional[int] = None,
    ) -> dict:
        """
        批量将模板迁移到目标标签

        Args:
            source_tag_id: 可选，仅移除指定的源标签关联；为None则保留其他标签
        """
        migrated_count = 0

        for tid in template_ids:
            # 如果指定了源标签，移除源标签关联
            if source_tag_id:
                await db.execute(
                    delete(TemplateTagRel).where(
                        and_(
                            TemplateTagRel.template_id == tid,
                            TemplateTagRel.tag_id == source_tag_id,
                        )
                    )
                )

            # 检查是否已关联目标标签
            existing = await db.execute(
                select(TemplateTagRel).where(
                    and_(
                        TemplateTagRel.template_id == tid,
                        TemplateTagRel.tag_id == target_tag_id,
                    )
                )
            )
            if not existing.scalar_one_or_none():
                db.add(TemplateTagRel(template_id=tid, tag_id=target_tag_id))

            migrated_count += 1

        await db.commit()

        return {
            "migrated_count": migrated_count,
            "template_ids": template_ids,
        }

    @staticmethod
    async def get_tag_summary(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
    ) -> dict:
        """
        获取标签统计汇总

        返回各标签下的模板数量、无标签模板数等。
        """
        base_query = select(Template)
        if owner_operator_id is not None:
            base_query = base_query.where(
                Template.owner_operator_id == owner_operator_id
            )

        # 总模板数
        total_result = await db.scalar(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result or 0

        # 有标签的模板数
        tagged_subq = select(TemplateTagRel.template_id).distinct()
        tagged_base = select(Template)
        if owner_operator_id is not None:
            tagged_base = tagged_base.where(
                Template.owner_operator_id == owner_operator_id
            )
        tagged_count_result = await db.scalar(
            select(func.count()).select_from(
                tagged_base.where(Template.id.in_(tagged_subq)).subquery()
            )
        )
        tagged_count = tagged_count_result or 0

        no_tag_count = total - tagged_count

        # 各标签下的模板数量
        tag_counts_query = (
            select(
                TemplateTag.id,
                TemplateTag.name,
                TemplateTag.category_id,
                func.count(func.distinct(TemplateTagRel.template_id)).label(
                    "template_count"
                ),
            )
            .join(TemplateTagRel, TemplateTagRel.tag_id == TemplateTag.id)
            .join(Template, TemplateTagRel.template_id == Template.id)
        )
        if owner_operator_id is not None:
            tag_counts_query = tag_counts_query.where(
                Template.owner_operator_id == owner_operator_id
            )
        tag_counts_query = tag_counts_query.group_by(
            TemplateTag.id, TemplateTag.name, TemplateTag.category_id
        )

        tag_counts_result = await db.execute(tag_counts_query)
        tag_counts = []
        for row in tag_counts_result.fetchall():
            tag_counts.append(
                {
                    "tag_id": row[0],
                    "tag_name": row[1],
                    "category_id": row[2],
                    "template_count": row[3],
                }
            )

        return {
            "total": total,
            "no_tag_count": no_tag_count,
            "tagged_count": tagged_count,
            "tag_counts": tag_counts,
        }

    @staticmethod
    async def get_category_stats(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
    ) -> List[dict]:
        """获取分类级别统计"""
        query = select(
            TemplateCategory.id,
            TemplateCategory.name,
            func.count(func.distinct(TemplateTag.id)).label("tag_count"),
        ).outerjoin(TemplateTag, TemplateTag.category_id == TemplateCategory.id)
        if owner_operator_id is not None:
            query = query.where(TemplateCategory.owner_operator_id == owner_operator_id)
        query = query.group_by(TemplateCategory.id, TemplateCategory.name)

        result = await db.execute(query)
        return [
            {"category_id": row[0], "category_name": row[1], "tag_count": row[2]}
            for row in result.fetchall()
        ]

    # ============================================
    # 模板附件管理
    # ============================================
    @staticmethod
    async def add_template_attachment(
        db: AsyncSession,
        template_id: int,
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
    ):
        """
        添加模板附件
        """
        from app.models import TemplateAttachment

        logger.info(
            f"[TemplateService] Adding attachment: template_id={template_id}, "
            f"owner_operator_id={owner_operator_id}, file_type={file_type}, "
            f"file_url={file_url}, file_name={file_name}, file_size={file_size}, "
            f"thumbnail_url={thumbnail_url}"
        )

        # 验证模板所有权
        template = await TemplateService.get_template(
            db, template_id, owner_operator_id
        )
        if not template:
            logger.error(
                f"[TemplateService] Template not found: template_id={template_id}, owner_operator_id={owner_operator_id}"
            )
            raise TemplateNotFoundError()

        attachment = TemplateAttachment(
            template_id=template_id,
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

        # 更新模板的图片/视频数量
        if file_type == "image":
            template.image_count += 1
        elif file_type == "video":
            template.video_count += 1

        await db.commit()
        await db.refresh(attachment)

        logger.info(
            f"[TemplateService] Attachment saved: id={attachment.id}, template_id={template_id}, "
            f"file_url={attachment.file_url}, thumbnail_url={attachment.thumbnail_url}"
        )
        return attachment

    @staticmethod
    async def list_template_attachments(
        db: AsyncSession,
        template_id: int,
        owner_operator_id: Optional[int] = None,
    ):
        """
        获取模板附件列表
        """
        from app.models import TemplateAttachment
        from app.services.storage_service import get_storage_service

        logger.debug(
            f"[TemplateService] Querying attachments: template_id={template_id}, owner_operator_id={owner_operator_id}"
        )

        # 验证模板所有权
        if owner_operator_id:
            template = await TemplateService.get_template(
                db, template_id, owner_operator_id
            )
            if not template:
                logger.warning(
                    f"[TemplateService] Template not found for attachment query: "
                    f"template_id={template_id}, owner_operator_id={owner_operator_id}"
                )
                raise TemplateNotFoundError()

        query = select(TemplateAttachment).where(
            TemplateAttachment.template_id == template_id
        )
        query = query.order_by(
            TemplateAttachment.sort_order.asc(), TemplateAttachment.created_at.asc()
        )

        result = await db.execute(query)
        attachments = result.scalars().all()

        # 动态转换URL（旧数据可能存的是本地路径）
        storage = get_storage_service()
        for attachment in attachments:
            attachment.file_url = TemplateService._convert_url(
                attachment.file_url, storage
            )
            if attachment.thumbnail_url:
                attachment.thumbnail_url = TemplateService._convert_url(
                    attachment.thumbnail_url, storage
                )

        logger.debug(
            f"[TemplateService] Found attachments: template_id={template_id}, count={len(attachments)}, "
            f"urls={[a.file_url for a in attachments]}"
        )
        return attachments

    @staticmethod
    def _convert_url(url: str, storage) -> str:
        """
        动态转换URL：使用 StorageService 的统一转换逻辑
        """
        if not url:
            return url
        # 使用 StorageService 的统一转换逻辑
        return storage.convert_url(url)

    @staticmethod
    async def delete_template_attachment(
        db: AsyncSession,
        attachment_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> bool:
        """
        删除模板附件
        """
        from app.models import TemplateAttachment

        logger.info(
            f"[TemplateService] Deleting attachment: attachment_id={attachment_id}, owner_operator_id={owner_operator_id}"
        )

        query = select(TemplateAttachment).where(TemplateAttachment.id == attachment_id)
        result = await db.execute(query)
        attachment = result.scalar_one_or_none()

        if not attachment:
            logger.warning(
                f"[TemplateService] Attachment not found: attachment_id={attachment_id}"
            )
            raise NotFoundError(message="附件不存在")

        # 验证模板所有权
        if owner_operator_id:
            template = await TemplateService.get_template(
                db, attachment.template_id, owner_operator_id
            )
            if not template:
                logger.warning(
                    f"[TemplateService] Template not found for attachment deletion: "
                    f"template_id={attachment.template_id}, owner_operator_id={owner_operator_id}"
                )
                raise TemplateNotFoundError()

        # 获取模板并更新计数
        template = await TemplateService.get_template(db, attachment.template_id, None)
        if template:
            if attachment.file_type == "image":
                template.image_count = max(0, template.image_count - 1)
            elif attachment.file_type == "video":
                template.video_count = max(0, template.video_count - 1)

        # 删除附件
        await db.delete(attachment)
        await db.commit()

        logger.info(
            f"[TemplateService] Attachment deleted: attachment_id={attachment_id}, template_id={attachment.template_id}"
        )
        return True
