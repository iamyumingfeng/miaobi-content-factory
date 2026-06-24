"""
操作日志服务 (operation_log_service.py)

提供操作日志的创建和查询功能。

Author: Claude Code
Date: 2026
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OperationLog, SuperAdmin, Operator, SubUser

# 操作日志模块常量
MODULE_USERS = "users"
MODULE_TEMPLATES = "templates"
MODULE_MATERIALS = "materials"
MODULE_GENERATION = "generation"
MODULE_DISTRIBUTION = "distribution"
MODULE_SYSTEM = "system"
MODULE_SCHEDULED_TASKS = "scheduled_tasks"

# 操作类型常量
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_DISTRIBUTE = "distribute"
ACTION_PUBLISH = "publish"
ACTION_LOGIN = "login"
ACTION_LOGOUT = "logout"
ACTION_CANCEL = "cancel"
ACTION_RETRY = "retry"
ACTION_COPY = "copy"
ACTION_DISABLE = "disable"
ACTION_ENABLE = "enable"
ACTION_TRANSFER = "transfer"
ACTION_IMPORT = "import"
ACTION_EXPORT = "export"
ACTION_TOGGLE = "toggle"


class OperationLogService:
    """
    操作日志服务类
    """

    # 数据截断阈值
    MAX_TEXT_LENGTH = 10000
    MAX_DESCRIPTION_LENGTH = 500
    MAX_EXTRA_LENGTH = 5000

    @staticmethod
    def _truncate_data(data: Any, max_length: int = 10000) -> Any:
        """
        截断数据以防止日志过大

        Args:
            data: 要截断的数据
            max_length: 最大长度

        Returns:
            截断后的数据
        """
        if data is None:
            return None
        if isinstance(data, str):
            if len(data) > max_length:
                half = max_length // 2
                return data[:half] + f"\n\n... [截断，原始长度 {len(data)} 字符] ...\n\n" + data[-half:]
            return data
        if isinstance(data, dict):
            return {k: OperationLogService._truncate_data(v, max_length) for k, v in data.items()}
        if isinstance(data, list):
            return [OperationLogService._truncate_data(v, max_length) for v in data]
        return data

    @staticmethod
    def _get_user_identity(
        db: AsyncSession,
        user_id: Optional[int] = None,
        user_type: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        根据用户类型获取用户身份

        Args:
            db: 数据库会话
            user_id: 用户ID
            user_type: 用户类型 (super_admin / operator / sub_user)

        Returns:
            Tuple[super_admin_id, operator_id, sub_user_id]
        """
        super_admin_id = None
        operator_id = None
        sub_user_id = None

        if user_type == "super_admin" and user_id:
            super_admin_id = user_id
        elif user_type == "operator" and user_id:
            operator_id = user_id
        elif user_type == "sub_user" and user_id:
            sub_user_id = user_id

        return super_admin_id, operator_id, sub_user_id

    @staticmethod
    async def create(
        db: AsyncSession,
        action: str,
        module: Optional[str] = None,
        description: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        user_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> OperationLog:
        """
        创建操作日志

        Args:
            db: 数据库会话
            action: 操作类型 (create/update/delete/distribute/publish/login/logout/cancel/retry/copy/disable/enable/transfer)
            module: 模块 (users/templates/materials/generation/distribution/system)
            description: 操作描述，如"创建素材：素材标题"
            table_name: 操作的数据表名
            record_id: 操作的记录ID
            old_value: 操作前的旧值
            new_value: 操作后的新值
            extra_data: 额外参数（如标签列表、操作条件等）
            user_id: 用户ID
            user_type: 用户类型 (super_admin/operator/sub_user)
            ip_address: IP地址
            user_agent: 浏览器/客户端信息

        Returns:
            创建的 OperationLog 对象
        """
        # 获取用户身份
        super_admin_id, operator_id, sub_user_id = OperationLogService._get_user_identity(
            db, user_id, user_type
        )

        # 截断数据
        description = OperationLogService._truncate_data(
            description, OperationLogService.MAX_DESCRIPTION_LENGTH
        )
        old_value = OperationLogService._truncate_data(old_value)
        new_value = OperationLogService._truncate_data(new_value)
        extra_data = OperationLogService._truncate_data(
            extra_data, OperationLogService.MAX_EXTRA_LENGTH
        )

        # 创建日志记录
        log = OperationLog(
            super_admin_id=super_admin_id,
            operator_id=operator_id,
            sub_user_id=sub_user_id,
            module=module,
            action=action,
            description=description,
            table_name=table_name,
            record_id=record_id,
            old_value_json=old_value,
            new_value_json=new_value,
            extra_data_json=extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        db.add(log)
        await db.flush()

        return log

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        module: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        user_type: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[OperationLog], int]:
        """
        查询操作日志列表（支持分页和条件筛选）

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            limit: 每页数量
            module: 模块筛选
            action: 操作类型筛选
            user_id: 用户ID筛选
            user_type: 用户类型筛选
            table_name: 数据表筛选
            record_id: 记录ID筛选
            start_date: 开始时间筛选
            end_date: 结束时间筛选

        Returns:
            Tuple[日志列表, 总数]
        """
        # 构建查询条件
        conditions = []

        if module:
            conditions.append(OperationLog.module == module)
        if action:
            conditions.append(OperationLog.action == action)
        if table_name:
            conditions.append(OperationLog.table_name == table_name)
        if record_id:
            conditions.append(OperationLog.record_id == record_id)
        if start_date:
            conditions.append(OperationLog.created_at >= start_date)
        if end_date:
            conditions.append(OperationLog.created_at <= end_date)

        # 用户身份筛选
        if user_id and user_type:
            if user_type == "super_admin":
                conditions.append(OperationLog.super_admin_id == user_id)
            elif user_type == "operator":
                conditions.append(OperationLog.operator_id == user_id)
            elif user_type == "sub_user":
                conditions.append(OperationLog.sub_user_id == user_id)

        # 构建查询
        query = select(OperationLog).where(and_(*conditions) if conditions else True)
        query = query.order_by(desc(OperationLog.created_at))

        # 获取总数
        from sqlalchemy import func
        count_query = select(func.count()).select_from(OperationLog)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    @staticmethod
    async def get_log_by_id(db: AsyncSession, log_id: int) -> Optional[OperationLog]:
        """
        根据ID获取操作日志

        Args:
            db: 数据库会话
            log_id: 日志ID

        Returns:
            OperationLog 对象或 None
        """
        result = await db.execute(
            select(OperationLog).where(OperationLog.id == log_id)
        )
        return result.scalar_one_or_none()
