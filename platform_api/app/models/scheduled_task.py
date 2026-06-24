"""
定时任务模型 (scheduled_task.py)

Author: Claude Code
Date: 2026-05-15
"""

from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Boolean, Column, DateTime, Enum,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScheduledTask(Base):
    """
    定时任务表

    支持创作管理者创建定时任务，按每日或每周定时执行内容生成。
    """

    __tablename__ = "scheduled_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(200), nullable=False, comment="定时任务名称")

    # ============================================
    # 调度配置
    # ============================================
    schedule_type = Column(
        Enum("daily", "weekly", "periodic", name="schedule_type_enum"),
        nullable=False,
        comment="调度类型：daily(每日) / weekly(每周) / periodic(周期)",
    )
    schedule_config_json = Column(
        JSON,
        nullable=False,
        comment="调度配置JSON。daily格式: {'times': ['09:00', '18:00']}; weekly格式: {'days': [1,3,5], 'times': ['09:00']}。days: 1=周一...7=周日",
    )

    # ============================================
    # 任务类型配置
    # ============================================
    task_type = Column(
        Enum("custom", "benchmark", name="scheduled_task_type_enum"),
        nullable=False,
        default="custom",
        comment="任务类型：custom(自定义文案) / benchmark(对标文案)",
    )

    # ============================================
    # 素材和模板配置
    # ============================================
    material_id = Column(
        BigInteger,
        ForeignKey("material.id"),
        nullable=True,
        comment="创作库素材ID（自定义文案时使用）",
    )
    benchmark_material_ids_json = Column(
        JSON,
        nullable=True,
        comment="对标素材ID列表JSON [1, 2, 3]（对标文案时使用，支持多选）",
    )
    template_ids_json = Column(
        JSON,
        nullable=True,
        comment="模板ID列表JSON [1, 2, 3]（支持多选，每次执行随机选一个）",
    )
    sub_user_ids_json = Column(
        JSON, nullable=False, comment="目标创作者ID列表JSON [1, 2, 3]"
    )

    # ============================================
    # 模型配置（复用 GenerationTask 的配置）
    # ============================================
    model_platform = Column(String(100), nullable=True, comment="选择的文本模型平台")
    model_id = Column(String(100), nullable=True, comment="选择的文本模型ID")
    image_model_platform = Column(
        String(100), nullable=True, comment="选择的图片模型平台"
    )
    image_model_id = Column(String(100), nullable=True, comment="选择的图片模型ID")
    model_selection_mode = Column(
        Enum("auto", "manual", name="scheduled_model_selection_mode_enum"),
        nullable=False,
        default="auto",
        comment="模型选择模式：auto（自动选择）/ manual（手动指定）",
    )
    max_concurrency = Column(
        Integer, nullable=False, default=5, comment="本次任务最大并发数"
    )
    image_count = Column(Integer, nullable=True, default=4, comment="生成图片数量")

    # ============================================
    # 变量值和去重配置
    # ============================================
    variable_values_json = Column(JSON, nullable=True, comment="变量值JSON")

    # 文案去重配置
    dedup_enabled = Column(
        Boolean, nullable=True, default=False, comment="文案去重检测开关"
    )
    dedup_threshold = Column(
        Integer, nullable=True, default=90, comment="文案去重阈值（0-100）"
    )
    dedup_retry_count = Column(
        Integer, nullable=True, default=3, comment="文案去重失败重试次数"
    )
    dedup_scope = Column(
        JSON,
        nullable=True,
        comment="文案去重范围配置：['subuser_history', 'current_task', 'all_history']",
    )

    # 图片去重配置
    image_dedup_enabled = Column(
        Boolean, nullable=True, default=False, comment="图片去重检测开关"
    )
    image_dedup_threshold = Column(
        Integer, nullable=True, default=90, comment="图片相似度阈值（0-100）"
    )
    image_dedup_retry_count = Column(
        Integer, nullable=True, default=3, comment="图片去重失败重试次数"
    )
    image_dedup_scope = Column(
        JSON,
        nullable=True,
        comment="图片去重范围：['subuser_image_history', 'current_task_images', 'all_image_history']",
    )

    # ============================================
    # 对标配置
    # ============================================
    benchmark_text_enabled = Column(
        Boolean, nullable=True, default=False, comment="文案对标开关"
    )
    benchmark_image_enabled = Column(
        Boolean, nullable=True, default=False, comment="图片对标开关"
    )
    benchmark_image_reference_options = Column(
        JSON, nullable=True, comment="图片参考选项：['composition', 'scene', 'style']"
    )
    benchmark_image_roles_json = Column(JSON, nullable=True, comment="对标图角色配置")
    template_product_mapping_json = Column(JSON, nullable=True, comment="模板产品映射")

    # ============================================
    # 任务状态
    # ============================================
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    status = Column(
        Enum("active", "paused", "disabled", name="scheduled_task_status_enum"),
        nullable=False,
        default="active",
        comment="任务状态：active(活跃) / paused(暂停) / disabled(禁用)",
    )

    # ============================================
    # 执行统计
    # ============================================
    total_executions = Column(Integer, nullable=False, default=0, comment="总执行次数")
    successful_executions = Column(
        Integer, nullable=False, default=0, comment="成功执行次数"
    )
    failed_executions = Column(
        Integer, nullable=False, default=0, comment="失败执行次数"
    )
    last_execution_at = Column(DateTime, nullable=True, comment="最后执行时间")
    last_execution_status = Column(
        String(50), nullable=True, comment="最后执行状态：success / failed / partial"
    )

    # ============================================
    # 下次执行时间（用于调度器快速查询）
    # ============================================
    next_execution_at = Column(
        DateTime, nullable=True, index=True, comment="下次执行时间"
    )

    # ============================================
    # 多租户隔离
    # ============================================
    owner_operator_id = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=False,
        index=True,
        comment="所属创作管理员ID（数据隔离用）",
    )
    created_by = Column(
        BigInteger,
        ForeignKey("operator.id"),
        nullable=True,
        comment="创建者创作管理员ID",
    )

    # ============================================
    # 时间戳
    # ============================================
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

    # ============================================
    # 关联关系
    # ============================================
    owner_operator = relationship(
        "Operator", foreign_keys=[owner_operator_id], back_populates="scheduled_tasks"
    )
    creator = relationship("Operator", foreign_keys=[created_by])
    material = relationship("Material", foreign_keys=[material_id])
    executions = relationship(
        "ScheduledTaskExecution",
        back_populates="scheduled_task",
        cascade="all, delete-orphan",
        order_by="ScheduledTaskExecution.execution_time.desc()",
    )

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, name={self.name}, status={self.status})>"
