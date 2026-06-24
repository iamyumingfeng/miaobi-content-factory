"""
用户管理服务 (user_service.py)

提供用户管理相关的业务逻辑。

Author: Claude Code
Date: 2025
"""

from typing import List, Optional
from datetime import datetime, timezone
import secrets
from sqlalchemy import select, and_, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, generate_userid
from app.core.exceptions import (
    UserNotFoundError,
)
from app.models import (
    SuperAdmin,
    Operator,
    SubUser,
    UserTag,
    UserTagRel,
    CreativeSeed,
    MaterialPlatform,
    MaterialCategory,
    MaterialAttachment,
    MaterialTag,
    MaterialTagRel,
    MaterialFavorite,
    Material,
    TemplatePlatform,
    TemplateCategory,
    TemplateTag,
    TemplateTagRel,
    Template,
    ContentEmbedding,
    GenerationTask,
    GenerationItem,
    Distribution,
    OperationLog,
)


class UserService:
    """
    用户管理服务类
    """

    @staticmethod
    def _to_frontend_status(db_status: str) -> str:
        """
        将数据库状态转换为前端状态
        online/offline -> active
        disabled -> disabled
        """
        if db_status in ("online", "offline"):
            return "active"
        return db_status

    @staticmethod
    def _to_db_status(frontend_status: str, current_db_status: str = "offline") -> str:
        """
        将前端状态转换为数据库状态
        active -> online (保持当前状态如果是online/offline)
        disabled -> disabled
        """
        if frontend_status == "active":
            # 如果当前状态是online或offline，保持不变；否则设为offline
            if current_db_status in ("online", "offline"):
                return current_db_status
            return "offline"
        return frontend_status

    # ============================================
    # 超级创作管理员
    # ============================================
    @staticmethod
    async def create_super_admin(
        db: AsyncSession,
        userid: str,
        nickname: str,
        password: str,
        created_by: Optional[int] = None,
    ) -> SuperAdmin:
        """
        创建超级管理员
        """
        # 检查 userid 是否已存在
        existing = await db.execute(
            select(SuperAdmin).where(SuperAdmin.userid == userid)
        )
        if existing.scalar_one_or_none():
            raise ValueError("用户ID已存在")

        now = datetime.now(timezone.utc)
        super_admin = SuperAdmin(
            userid=userid,
            nickname=nickname,
            hashed_password=get_password_hash(password),
            status="offline",
            created_at=now,
            updated_at=now,
        )

        db.add(super_admin)
        await db.commit()
        await db.refresh(super_admin)
        return super_admin

    @staticmethod
    async def list_super_admins(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[SuperAdmin], int]:
        """
        获取超级管理员列表
        """
        query = select(SuperAdmin)

        if status:
            query = query.where(SuperAdmin.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(SuperAdmin.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    # ============================================
    # 创作创作管理员
    # ============================================
    @staticmethod
    async def create_operator(
        db: AsyncSession,
        nickname: str,
        password: str,
        created_by: int,
        display_name: Optional[str] = None,
        user_positioning: Optional[str] = None,
        user_category: Optional[str] = None,
    ) -> Operator:
        """
        创建创作管理员
        """
        # 生成唯一 userid - 使用 O 前缀表示创作管理员
        userid = generate_userid(prefix="O")
        now = datetime.now(timezone.utc)

        operator = Operator(
            userid=userid,
            nickname=nickname,
            display_name=display_name,
            hashed_password=get_password_hash(password),
            created_by=created_by,
            user_positioning=user_positioning,
            user_category=user_category,
            status="offline",
            created_at=now,
            updated_at=now,
        )

        db.add(operator)
        await db.commit()
        await db.refresh(operator)
        return operator

    @staticmethod
    async def list_operators(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        created_by: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[Operator], int]:
        """
        获取创作管理员列表

        Args:
            created_by: 如果指定，只返回该超级管理员创建的创作管理员；为 None 时返回所有
        """
        query = select(Operator)

        # created_by 为 None 时返回所有创作管理员（超级管理员场景）
        if created_by is not None:
            query = query.where(Operator.created_by == created_by)

        if status:
            if status == "online":
                query = query.where(Operator.status == "online")
            elif status == "offline":
                query = query.where(Operator.status == "offline")
            elif status == "disabled":
                query = query.where(Operator.status == "disabled")

        if keyword:
            query = query.where(Operator.nickname.contains(keyword))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(Operator.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    @staticmethod
    async def get_operator(
        db: AsyncSession,
        operator_id: int,
    ) -> Optional[Operator]:
        """
        获取创作管理员详情
        """
        result = await db.execute(select(Operator).where(Operator.id == operator_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_operator(
        db: AsyncSession,
        operator_id: int,
        **kwargs,
    ) -> Optional[Operator]:
        """
        更新创作管理员

        当禁用创作管理员时，会自动断开其所有 WebSocket 连接
        """
        result = await db.execute(select(Operator).where(Operator.id == operator_id))
        operator = result.scalar_one_or_none()
        if not operator:
            raise UserNotFoundError()

        # 检查是否正在禁用
        new_status = kwargs.get("status")
        is_disabling = (new_status == "disabled" and operator.status != "disabled")

        # 更新字段
        allowed_fields = [
            "nickname", "display_name", "status",
            "user_positioning", "user_category"
        ]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(operator, field, value)

        operator.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(operator)

        # 如果是禁用操作，主动关闭 WebSocket 连接
        if is_disabling:
            await UserService._force_disconnect_operator(operator_id)

        return operator

    @staticmethod
    async def _force_disconnect_operator(operator_id: int):
        """
        强制断开创作管理员的所有连接

        Args:
            operator_id: 创作管理员 ID
        """
        from app.websocket.manager import get_manager

        try:
            manager = get_manager()
            await manager.disconnect_operator(operator_id, "账号已被禁用")
        except Exception:
            # WebSocket 断开失败不影响主流程
            pass

    # ============================================
    # 创作员管理
    # ============================================
    @staticmethod
    async def create_sub_user(
        db: AsyncSession,
        owner_operator_id: int,
        nickname: str,
        password: Optional[str] = None,
        created_by: Optional[int] = None,
        display_name: Optional[str] = None,
        fan_profile: Optional[str] = None,
        user_positioning: Optional[str] = None,
        user_category: Optional[str] = None,
        content_style: Optional[str] = None,
        account_type: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
    ) -> SubUser:
        """
        创建创作者
        """
        # 生成唯一 userid - 使用 U 前缀表示创作者
        userid = generate_userid(prefix="U")
        now = datetime.now(timezone.utc)

        # 如果未提供密码，生成随机密码
        if not password:
            password = secrets.token_urlsafe(16)

        sub_user = SubUser(
            userid=userid,
            nickname=nickname,
            display_name=display_name,
            hashed_password=get_password_hash(password),
            owner_operator_id=owner_operator_id,
            created_by=created_by or owner_operator_id,
            managed_by=owner_operator_id,
            fan_profile=fan_profile,
            user_positioning=user_positioning,
            user_category=user_category,
            content_style=content_style,
            account_type=account_type,
            status="offline",
            created_at=now,
            updated_at=now,
        )

        db.add(sub_user)
        await db.flush()  # 获取 ID

        # 处理标签关联
        if tag_ids:
            for tag_id in tag_ids:
                tag_rel = UserTagRel(
                    user_id=sub_user.id,
                    tag_id=tag_id,
                )
                db.add(tag_rel)

        await db.commit()
        await db.refresh(sub_user)
        return sub_user

    @staticmethod
    async def list_sub_users(
        db: AsyncSession,
        owner_operator_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        tag_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[SubUser], int]:
        """
        获取创作者列表

        Args:
            owner_operator_id: 创作管理员ID，None 表示查看所有（超级管理员专用）
        """
        query = select(SubUser)
        if owner_operator_id:
            query = query.where(SubUser.owner_operator_id == owner_operator_id)

        if status:
            # 状态映射：前端 online/offline/disabled 对应数据库 online/offline/disabled
            if status == "online":
                query = query.where(SubUser.status == "online")
            elif status == "offline":
                query = query.where(SubUser.status == "offline")
            elif status == "disabled":
                query = query.where(SubUser.status == "disabled")

        if keyword:
            query = query.where(SubUser.nickname.contains(keyword))

        if tag_id:
            # 关联标签
            query = query.join(
                UserTagRel,
                and_(
                    UserTagRel.user_id == SubUser.id,
                    UserTagRel.tag_id == tag_id,
                )
            )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        query = query.order_by(SubUser.created_at.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        # 为每个创作者加载标签数据
        if items:
            user_ids = [user.id for user in items]
            # 查询所有标签关联
            tag_rel_query = select(UserTagRel).where(UserTagRel.user_id.in_(user_ids))
            tag_rel_result = await db.execute(tag_rel_query)
            tag_rels = tag_rel_result.scalars().all()

            # 查询所有标签
            tag_ids = list({rel.tag_id for rel in tag_rels})
            if tag_ids:
                tags_query = select(UserTag).where(UserTag.id.in_(tag_ids))
                tags_result = await db.execute(tags_query)
                tags = tags_result.scalars().all()
                tags_by_id = {tag.id: tag for tag in tags}

                # 按用户分组标签关联
                tag_rels_by_user: dict[int, list] = {}
                for rel in tag_rels:
                    if rel.user_id not in tag_rels_by_user:
                        tag_rels_by_user[rel.user_id] = []
                    tag_rels_by_user[rel.user_id].append(rel)

                # 为每个用户添加标签数据
                for user in items:
                    user_tags = []
                    if user.id in tag_rels_by_user:
                        for rel in tag_rels_by_user[user.id]:
                            if rel.tag_id in tags_by_id:
                                tag = tags_by_id[rel.tag_id]
                                user_tags.append({
                                    "id": tag.id,
                                    "name": tag.name,
                                    "tag_type": tag.tag_type,
                                    "description": tag.description,
                                    "color": tag.color,
                                    "created_by": tag.created_by,
                                    "created_at": tag.created_at,
                                    "updated_at": tag.updated_at,
                                })
                    # 动态添加 tags 属性
                    user.tags = user_tags

        return items, total

    @staticmethod
    async def get_sub_user(
        db: AsyncSession,
        sub_user_id: int,
        owner_operator_id: Optional[int] = None,
    ) -> Optional[SubUser]:
        """
        获取创作者详情
        """
        query = select(SubUser).where(SubUser.id == sub_user_id)

        if owner_operator_id:
            query = query.where(SubUser.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    # ============================================
    # 用户标签管理
    # ============================================
    @staticmethod
    async def create_user_tag(
        db: AsyncSession,
        name: str,
        tag_type: str,
        created_by: int,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> UserTag:
        """
        创建用户标签
        """
        tag = UserTag(
            name=name,
            tag_type=tag_type,
            description=description,
            color=color,
            created_by=created_by,
        )

        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def list_user_tags(
        db: AsyncSession,
        tag_type: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> List[UserTag]:
        """
        获取用户标签列表
        """
        query = select(UserTag)

        if tag_type:
            query = query.where(UserTag.tag_type == tag_type)

        if created_by:
            query = query.where(UserTag.created_by == created_by)

        query = query.order_by(UserTag.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count_sub_users_by_tag(
        db: AsyncSession,
        owner_operator_id: int,
    ) -> dict[int, int]:
        """
        统计每个标签下的创作者数量
        返回: {tag_id: count}
        """
        from sqlalchemy import func

        # 统计每个标签下的创作者数量
        query = (
            select(
                UserTagRel.tag_id,
                func.count(UserTagRel.user_id).label('count')
            )
            .select_from(UserTagRel)
            .join(SubUser, UserTagRel.user_id == SubUser.id)
            .where(SubUser.owner_operator_id == owner_operator_id)
            .group_by(UserTagRel.tag_id)
        )

        result = await db.execute(query)
        rows = result.all()

        return {row.tag_id: row.count for row in rows}

    @staticmethod
    async def get_super_admin(
        db: AsyncSession,
        super_admin_id: int,
    ) -> Optional[SuperAdmin]:
        """
        获取超级管理员详情
        """
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == super_admin_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_super_admin(
        db: AsyncSession,
        super_admin_id: int,
        **kwargs,
    ) -> Optional[SuperAdmin]:
        """
        更新超级管理员
        """
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == super_admin_id))
        super_admin = result.scalar_one_or_none()
        if not super_admin:
            raise UserNotFoundError()

        # 更新字段
        allowed_fields = ["nickname", "status", "user_positioning"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(super_admin, field, value)

        super_admin.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(super_admin)
        return super_admin

    @staticmethod
    async def delete_super_admin(
        db: AsyncSession,
        super_admin_id: int,
    ) -> None:
        """
        删除超级管理员
        """
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == super_admin_id))
        super_admin = result.scalar_one_or_none()
        if not super_admin:
            raise UserNotFoundError()

        await db.delete(super_admin)
        await db.commit()

    @staticmethod
    async def delete_operator(
        db: AsyncSession,
        operator_id: int,
    ) -> None:
        """
        删除创作管理员
        删除前检查是否有关联的创作者，如果有则抛出异常
        删除前处理所有外键约束：
        - 将 created_by/operator_id 等可空字段设为 NULL
        - 删除 owner_operator_id 非空字段关联的记录
        """
        result = await db.execute(select(Operator).where(Operator.id == operator_id))
        operator = result.scalar_one_or_none()
        if not operator:
            raise UserNotFoundError()

        # 检查是否有关联的创作者
        sub_user_count = await UserService.count_sub_users(db, operator_id)
        if sub_user_count > 0:
            raise ValueError(f"无法删除：该创作管理员下还有 {sub_user_count} 个创作者，请先转移或删除这些创作者")

        # ============================================
        # 第一步：将 created_by/operator_id 可空字段设为 NULL
        # ============================================

        # 素材相关表的 created_by
        await db.execute(
            update(MaterialPlatform)
            .where(MaterialPlatform.created_by == operator_id)
            .values(created_by=None)
        )
        await db.execute(
            update(MaterialCategory)
            .where(MaterialCategory.created_by == operator_id)
            .values(created_by=None)
        )
        await db.execute(
            update(MaterialTag)
            .where(MaterialTag.created_by == operator_id)
            .values(created_by=None)
        )
        await db.execute(
            update(Material)
            .where(Material.created_by == operator_id)
            .values(created_by=None)
        )

        # 模板相关表的 created_by（TemplateTag.created_by 是 nullable=False，需要删除）
        await db.execute(
            update(TemplateCategory)
            .where(TemplateCategory.created_by == operator_id)
            .values(created_by=None)
        )
        # 先删除 TemplateTagRel，再删除 TemplateTag（created_by 是 nullable=False）
        await db.execute(
            delete(TemplateTagRel).where(
                TemplateTagRel.tag_id.in_(
                    select(TemplateTag.id).where(TemplateTag.created_by == operator_id)
                )
            )
        )
        await db.execute(
            delete(TemplateTag).where(TemplateTag.created_by == operator_id)
        )
        await db.execute(
            update(Template)
            .where(Template.created_by == operator_id)
            .values(created_by=None)
        )
        await db.execute(
            update(TemplatePlatform)
            .where(TemplatePlatform.created_by == operator_id)
            .values(created_by=None)
        )

        # 生成任务相关表的 created_by
        await db.execute(
            update(GenerationTask)
            .where(GenerationTask.created_by == operator_id)
            .values(created_by=None)
        )

        # 操作日志的 operator_id
        await db.execute(
            update(OperationLog)
            .where(OperationLog.operator_id == operator_id)
            .values(operator_id=None)
        )

        # 创意种子的 owner_operator_id（可空，转为系统级种子）
        await db.execute(
            update(CreativeSeed)
            .where(CreativeSeed.owner_operator_id == operator_id)
            .values(owner_operator_id=None)
        )

        # ============================================
        # 第二步：删除 owner_operator_id 非空字段关联的记录
        # 注意：顺序很重要，先删除依赖表，再删除被依赖表
        # ============================================

        # 素材相关（先删除附件、标签关联、收藏，再删除素材本体，最后删除分类/平台/标签）
        # MaterialAttachment 通过 material_id 关联，需要子查询
        await db.execute(
            delete(MaterialAttachment).where(
                MaterialAttachment.material_id.in_(
                    select(Material.id).where(Material.owner_operator_id == operator_id)
                )
            )
        )
        # MaterialFavorite 通过 material_id 关联，需要子查询
        await db.execute(
            delete(MaterialFavorite).where(
                MaterialFavorite.material_id.in_(
                    select(Material.id).where(Material.owner_operator_id == operator_id)
                )
            )
        )
        await db.execute(
            delete(MaterialTagRel).where(
                MaterialTagRel.material_id.in_(
                    select(Material.id).where(Material.owner_operator_id == operator_id)
                )
            )
        )
        await db.execute(
            delete(Material).where(Material.owner_operator_id == operator_id)
        )
        await db.execute(
            delete(MaterialTag).where(MaterialTag.owner_operator_id == operator_id)
        )
        await db.execute(
            delete(MaterialCategory).where(MaterialCategory.owner_operator_id == operator_id)
        )
        await db.execute(
            delete(MaterialPlatform).where(MaterialPlatform.owner_operator_id == operator_id)
        )

        # 模板相关（先删除附件、标签关联，再删除模板本体）
        await db.execute(
            delete(Template).where(Template.owner_operator_id == operator_id)
        )
        # 先删除 TemplateTagRel，再删除 TemplateTag
        await db.execute(
            delete(TemplateTagRel).where(
                TemplateTagRel.tag_id.in_(
                    select(TemplateTag.id).where(TemplateTag.owner_operator_id == operator_id)
                )
            )
        )
        await db.execute(
            delete(TemplateTag).where(TemplateTag.owner_operator_id == operator_id)
        )
        await db.execute(
            delete(TemplateCategory).where(TemplateCategory.owner_operator_id == operator_id)
        )
        await db.execute(
            delete(TemplatePlatform).where(TemplatePlatform.owner_operator_id == operator_id)
        )

        # 内容嵌入
        await db.execute(
            delete(ContentEmbedding).where(ContentEmbedding.owner_operator_id == operator_id)
        )

        # 生成任务相关（先删除分发记录，再删除子任务，最后删除任务）
        # 先查询需要删除的 ID，避免子查询列名问题
        gen_item_ids_result = await db.execute(
            select(GenerationItem.id).where(GenerationItem.owner_operator_id == operator_id)
        )
        gen_item_ids = [row[0] for row in gen_item_ids_result.all()]
        
        if gen_item_ids:
            await db.execute(
                delete(Distribution).where(Distribution.generation_item_id.in_(gen_item_ids))
            )
        
        await db.execute(
            delete(GenerationItem).where(GenerationItem.owner_operator_id == operator_id)
        )
        
        gen_task_ids_result = await db.execute(
            select(GenerationTask.id).where(GenerationTask.owner_operator_id == operator_id)
        )
        gen_task_ids = [row[0] for row in gen_task_ids_result.all()]
        
        if gen_task_ids:
            await db.execute(
                delete(Distribution).where(Distribution.task_id.in_(gen_task_ids))
            )
        
        await db.execute(
            delete(GenerationTask).where(GenerationTask.owner_operator_id == operator_id)
        )

        # ============================================
        # 第三步：删除创作管理员
        # ============================================
        await db.delete(operator)
        await db.commit()

    @staticmethod
    async def update_sub_user(
        db: AsyncSession,
        sub_user_id: int,
        owner_operator_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[SubUser]:
        """
        更新创作者

        Args:
            owner_operator_id: 创作管理员ID，None 表示超级管理员（可以更新任何创作者）
        """
        query = select(SubUser).where(SubUser.id == sub_user_id)

        if owner_operator_id:
            query = query.where(SubUser.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        sub_user = result.scalar_one_or_none()
        if not sub_user:
            raise UserNotFoundError()

        # 提取 tag_ids 单独处理
        tag_ids = kwargs.pop('tag_ids', None)

        # 更新字段
        allowed_fields = [
            "nickname", "display_name", "status",
            "fan_profile", "user_positioning", "user_category",
            "content_style", "account_type", "managed_by"
        ]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(sub_user, field, value)

        # 处理标签关联更新
        if tag_ids is not None:
            # 删除旧的标签关联
            await db.execute(
                delete(UserTagRel).where(UserTagRel.user_id == sub_user_id)
            )
            # 添加新的标签关联
            for tag_id in tag_ids:
                tag_rel = UserTagRel(
                    user_id=sub_user_id,
                    tag_id=tag_id,
                )
                db.add(tag_rel)

        sub_user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(sub_user)
        return sub_user

    @staticmethod
    async def delete_sub_user(
        db: AsyncSession,
        sub_user_id: int,
        owner_operator_id: int,
    ) -> None:
        """
        删除创作者
        """
        query = select(SubUser).where(
            and_(
                SubUser.id == sub_user_id,
                SubUser.owner_operator_id == owner_operator_id
            )
        )
        result = await db.execute(query)
        sub_user = result.scalar_one_or_none()
        if not sub_user:
            raise UserNotFoundError()

        await db.delete(sub_user)
        await db.commit()

    @staticmethod
    async def update_user_tag(
        db: AsyncSession,
        tag_id: int,
        created_by: int,
        **kwargs,
    ) -> Optional[UserTag]:
        """
        更新用户标签
        """
        query = select(UserTag).where(
            and_(
                UserTag.id == tag_id,
                UserTag.created_by == created_by
            )
        )
        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise UserNotFoundError("标签不存在")

        allowed_fields = ["name", "description", "color"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(tag, field, value)

        tag.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(tag)
        return tag

    @staticmethod
    async def delete_user_tag(
        db: AsyncSession,
        tag_id: int,
        created_by: int,
    ) -> None:
        """
        删除用户标签
        """
        query = select(UserTag).where(
            and_(
                UserTag.id == tag_id,
                UserTag.created_by == created_by
            )
        )
        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            raise UserNotFoundError("标签不存在")

        await db.delete(tag)
        await db.commit()

    # ============================================
    # 用户转移和密码重置
    # ============================================
    @staticmethod
    async def reset_sub_user_password(
        db: AsyncSession,
        sub_user_id: int,
        new_password: str,
        owner_operator_id: Optional[int] = None,
    ) -> SubUser:
        """
        重置创作者密码
        """
        query = select(SubUser).where(SubUser.id == sub_user_id)
        if owner_operator_id:
            query = query.where(SubUser.owner_operator_id == owner_operator_id)

        result = await db.execute(query)
        sub_user = result.scalar_one_or_none()
        if not sub_user:
            raise UserNotFoundError("创作者不存在")

        sub_user.hashed_password = get_password_hash(new_password)
        sub_user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(sub_user)
        return sub_user

    @staticmethod
    async def reset_operator_password(
        db: AsyncSession,
        operator_id: int,
        new_password: str,
    ) -> Operator:
        """
        重置创作管理员密码（超级管理员）
        """
        result = await db.execute(select(Operator).where(Operator.id == operator_id))
        operator = result.scalar_one_or_none()
        if not operator:
            raise UserNotFoundError("创作管理员不存在")

        operator.hashed_password = get_password_hash(new_password)
        operator.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(operator)
        return operator

    @staticmethod
    async def reset_super_admin_password(
        db: AsyncSession,
        super_admin_id: int,
        new_password: str,
    ) -> SuperAdmin:
        """
        重置超级管理员密码
        """
        result = await db.execute(select(SuperAdmin).where(SuperAdmin.id == super_admin_id))
        super_admin = result.scalar_one_or_none()
        if not super_admin:
            raise UserNotFoundError("超级管理员不存在")

        super_admin.hashed_password = get_password_hash(new_password)
        super_admin.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(super_admin)
        return super_admin

    @staticmethod
    async def transfer_sub_users(
        db: AsyncSession,
        sub_user_ids: List[int],
        from_operator_id: int,
        to_operator_id: int,
    ) -> int:
        """
        批量转移创作者到其他创作管理员
        返回转移的用户数量

        处理逻辑：
        1. 获取源创作管理员的标签
        2. 获取要转移的用户及其标签
        3. 在目标创作管理员下创建同名标签（如果不存在）
        4. 更新用户的 owner_operator_id
        5. 重新建立用户与新标签的关联
        """
        from app.core.exceptions import UserNotFoundError

        count = 0

        # 验证目标创作管理员存在
        to_result = await db.execute(select(Operator).where(Operator.id == to_operator_id))
        if not to_result.scalar_one_or_none():
            raise UserNotFoundError("目标创作管理员不存在")

        # 验证源创作管理员存在
        from_result = await db.execute(select(Operator).where(Operator.id == from_operator_id))
        if not from_result.scalar_one_or_none():
            raise UserNotFoundError("源创作管理员不存在")

        # 第一步：获取所有要转移的用户
        query = select(SubUser).where(
            and_(
                SubUser.id.in_(sub_user_ids),
                SubUser.owner_operator_id == from_operator_id
            )
        )
        result = await db.execute(query)
        sub_users = result.scalars().all()

        if not sub_users:
            count = 0
        else:
            # 第二步：获取这些用户当前的标签关联
            user_tag_query = select(UserTagRel).where(
                UserTagRel.user_id.in_([u.id for u in sub_users])
            )
            tag_rel_result = await db.execute(user_tag_query)
            user_tag_rels = tag_rel_result.scalars().all()

            # 第三步：获取源标签的详细信息
            source_tag_ids = list({rel.tag_id for rel in user_tag_rels})
            source_tags_by_id = {}
            if source_tag_ids:
                source_tags_query = select(UserTag).where(
                    UserTag.id.in_(source_tag_ids)
                )
                source_tags_result = await db.execute(source_tags_query)
                source_tags = source_tags_result.scalars().all()
                source_tags_by_id = {tag.id: tag for tag in source_tags}

            # 第四步：获取目标创作管理员已有的标签
            target_tags_query = select(UserTag).where(
                and_(
                    UserTag.created_by == to_operator_id,
                    UserTag.tag_type == "subuser_tag"
                )
            )
            target_tags_result = await db.execute(target_tags_query)
            target_tags = target_tags_result.scalars().all()
            target_tags_by_name = {tag.name: tag for tag in target_tags}

            # 第五步：在目标创作管理员下创建缺失的标签
            new_tag_mapping: dict[int, int] = {}  # 源标签ID -> 新标签ID
            for source_tag_id, source_tag in source_tags_by_id.items():
                if source_tag.name in target_tags_by_name:
                    # 标签已存在，使用现有标签
                    new_tag_mapping[source_tag_id] = target_tags_by_name[source_tag.name].id
                else:
                    # 创建新标签
                    new_tag = UserTag(
                        name=source_tag.name,
                        tag_type=source_tag.tag_type,
                        description=source_tag.description,
                        color=source_tag.color,
                        created_by=to_operator_id,
                    )
                    db.add(new_tag)
                    await db.flush()
                    new_tag_mapping[source_tag_id] = new_tag.id
                    target_tags_by_name[source_tag.name] = new_tag

            # 第六步：删除旧的标签关联
            if user_tag_rels:
                await db.execute(
                    delete(UserTagRel).where(UserTagRel.id.in_([rel.id for rel in user_tag_rels]))
                )

            # 第七步：更新用户的 owner_operator_id 并创建新的标签关联
            count = 0
            for sub_user in sub_users:
                sub_user.owner_operator_id = to_operator_id
                sub_user.managed_by = to_operator_id
                sub_user.updated_at = datetime.utcnow()

                # 为该用户创建新的标签关联
                user_old_tag_rels = [rel for rel in user_tag_rels if rel.user_id == sub_user.id]
                for old_rel in user_old_tag_rels:
                    if old_rel.tag_id in new_tag_mapping:
                        new_rel = UserTagRel(
                            user_id=sub_user.id,
                            tag_id=new_tag_mapping[old_rel.tag_id],
                        )
                        db.add(new_rel)

                count += 1

        # 提交事务
        await db.commit()
        return count

    @staticmethod
    async def count_sub_users(
        db: AsyncSession,
        owner_operator_id: int,
    ) -> int:
        """
        统计创作管理员的创作者数量
        """
        query = select(func.count()).select_from(
            select(SubUser).where(SubUser.owner_operator_id == owner_operator_id).subquery()
        )
        result = await db.execute(query)
        return result.scalar() or 0
