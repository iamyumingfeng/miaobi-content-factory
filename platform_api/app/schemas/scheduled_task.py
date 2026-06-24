"""
定时任务 Schema (scheduled_task.py)

包含定时任务相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .common import BaseSchema


# ============================================
# 调度配置 Schema
# ============================================

class DailyScheduleConfig(BaseModel):
    """
    每日调度配置
    """
    times: List[str] = Field(
        ...,
        description="执行时间列表，格式：HH:MM，如 ['09:00', '18:00']",
        min_length=1
    )
    
    @field_validator('times')
    @classmethod
    def validate_times(cls, v):
        """验证时间格式"""
        for time_str in v:
            try:
                hour, minute = time_str.split(':')
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    raise ValueError(f"时间格式错误：{time_str}")
            except ValueError:
                raise ValueError(f"时间格式错误：{time_str}，正确格式为 HH:MM")
        return v


class WeeklyScheduleConfig(BaseModel):
    """
    每周调度配置
    """
    days: List[int] = Field(
        ...,
        description="执行日期列表，1=周一...7=周日，如 [1, 3, 5]",
        min_length=1
    )
    times: List[str] = Field(
        ...,
        description="执行时间列表，格式：HH:MM，如 ['09:00', '18:00']",
        min_length=1
    )
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v):
        """验证日期范围"""
        if not all(1 <= day <= 7 for day in v):
            raise ValueError("日期必须在 1-7 之间（1=周一，7=周日）")
        return v
    
    @field_validator('times')
    @classmethod
    def validate_times(cls, v):
        """验证时间格式"""
        for time_str in v:
            try:
                hour, minute = time_str.split(':')
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    raise ValueError(f"时间格式错误：{time_str}")
            except ValueError:
                raise ValueError(f"时间格式错误：{time_str}，正确格式为 HH:MM")
        return v


class PeriodicScheduleConfig(BaseModel):
    """
    周期调度配置
    
    在指定的日期范围内，按照每日时间点执行。
    例如：2026-05-20 到 2026-06-20 期间，每天 09:00 和 18:00 执行。
    """
    start_date: str = Field(
        ...,
        description="周期开始日期，格式：YYYY-MM-DD，如 '2026-05-20'"
    )
    end_date: str = Field(
        ...,
        description="周期结束日期，格式：YYYY-MM-DD，如 '2026-06-20'"
    )
    times: List[str] = Field(
        ...,
        description="执行时间列表，格式：HH:MM，如 ['09:00', '18:00']",
        min_length=1
    )
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            from datetime import datetime
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"日期格式错误：{v}，正确格式为 YYYY-MM-DD")
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """验证日期范围"""
        if 'start_date' in info.data:
            from datetime import datetime
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError("结束日期不能早于开始日期")
        return v
    
    @field_validator('times')
    @classmethod
    def validate_times(cls, v):
        """验证时间格式"""
        for time_str in v:
            try:
                hour, minute = time_str.split(':')
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    raise ValueError(f"时间格式错误：{time_str}")
            except ValueError:
                raise ValueError(f"时间格式错误：{time_str}，正确格式为 HH:MM")
        return v


# ============================================
# 定时任务基础 Schema
# ============================================

class ScheduledTaskBase(BaseModel):
    """
    定时任务基础信息
    """
    name: str = Field(..., description="定时任务名称", max_length=200)
    task_type: str = Field(
        default="custom",
        description="任务类型：custom(自定义文案) / benchmark(对标文案)"
    )
    
    # 调度配置
    schedule_type: str = Field(
        ...,
        description="调度类型：daily(每日) / weekly(每周)"
    )
    schedule_config_json: Dict[str, Any] = Field(
        ...,
        description="调度配置JSON。daily格式: {'times': ['09:00', '18:00']}; weekly格式: {'days': [1,3,5], 'times': ['09:00']}"
    )
    
    # 素材和模板配置
    material_id: Optional[int] = Field(default=None, description="创作库素材ID（自定义文案时使用）")
    benchmark_material_ids_json: Optional[List[int]] = Field(default=None, description="对标素材ID列表（对标文案时使用，支持多选）")
    template_ids_json: Optional[List[int]] = Field(default=None, description="模板ID列表（支持多选，每次执行随机选一个）")
    sub_user_ids_json: List[int] = Field(..., description="目标创作者ID列表")
    
    # 模型配置
    model_platform: Optional[str] = Field(default=None, description="选择的文本模型平台", max_length=100)
    model_id: Optional[str] = Field(default=None, description="选择的文本模型ID", max_length=100)
    image_model_platform: Optional[str] = Field(default=None, description="选择的图片模型平台", max_length=100)
    image_model_id: Optional[str] = Field(default=None, description="选择的图片模型ID", max_length=100)
    model_selection_mode: str = Field(default="auto", description="模型选择模式：auto / manual")
    max_concurrency: int = Field(default=5, description="本次任务最大并发数", ge=1, le=100)
    image_count: int = Field(default=4, description="生成图片数量", ge=1, le=10)
    
    # 变量值配置
    variable_values_json: Optional[Dict[str, Any]] = Field(default=None, description="变量值JSON")
    
    # 文案去重配置
    dedup_enabled: Optional[bool] = Field(default=False, description="文案去重检测开关")
    dedup_threshold: Optional[int] = Field(default=90, description="文案去重阈值（0-100）", ge=0, le=100)
    dedup_retry_count: Optional[int] = Field(default=3, description="文案去重失败重试次数", ge=0, le=10)
    dedup_scope: Optional[List[str]] = Field(default=None, description="文案去重范围配置")
    
    # 图片去重配置
    image_dedup_enabled: Optional[bool] = Field(default=False, description="图片去重检测开关")
    image_dedup_threshold: Optional[int] = Field(default=90, description="图片相似度阈值（0-100）", ge=0, le=100)
    image_dedup_retry_count: Optional[int] = Field(default=3, description="图片去重失败重试次数", ge=0, le=10)
    image_dedup_scope: Optional[List[str]] = Field(default=None, description="图片去重范围")
    
    # 对标配置
    benchmark_text_enabled: Optional[bool] = Field(default=False, description="文案对标开关")
    benchmark_image_enabled: Optional[bool] = Field(default=False, description="图片对标开关")
    benchmark_image_reference_options: Optional[List[str]] = Field(default=None, description="图片参考选项")
    benchmark_image_roles_json: Optional[Dict[str, List[str]]] = Field(default=None, description="对标图角色配置")
    template_product_mapping_json: Optional[Dict[str, str]] = Field(default=None, description="模板产品映射")
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        """验证任务类型"""
        if v not in ['custom', 'benchmark']:
            raise ValueError("任务类型必须是 custom 或 benchmark")
        return v
    
    @field_validator('schedule_type')
    @classmethod
    def validate_schedule_type(cls, v):
        """验证调度类型"""
        if v not in ['daily', 'weekly', 'periodic']:
            raise ValueError("调度类型必须是 daily、weekly 或 periodic")
        return v
    
    @field_validator('schedule_config_json')
    @classmethod
    def validate_schedule_config(cls, v, info):
        """验证调度配置"""
        schedule_type = info.data.get('schedule_type')
        if schedule_type == 'daily':
            DailyScheduleConfig(**v)
        elif schedule_type == 'weekly':
            WeeklyScheduleConfig(**v)
        elif schedule_type == 'periodic':
            PeriodicScheduleConfig(**v)
        return v
    
    @field_validator('model_selection_mode')
    @classmethod
    def validate_model_selection_mode(cls, v):
        """验证模型选择模式"""
        if v not in ['auto', 'manual']:
            raise ValueError("模型选择模式必须是 auto 或 manual")
        return v


class ScheduledTaskCreate(ScheduledTaskBase):
    """
    创建定时任务请求
    """
    pass


class ScheduledTaskUpdate(BaseModel):
    """
    更新定时任务请求
    """
    name: Optional[str] = Field(default=None, description="定时任务名称", max_length=200)
    task_type: Optional[str] = Field(default=None, description="任务类型：custom / benchmark")
    
    # 调度配置
    schedule_type: Optional[str] = Field(default=None, description="调度类型：daily / weekly")
    schedule_config_json: Optional[Dict[str, Any]] = Field(default=None, description="调度配置JSON")
    
    # 素材和模板配置
    material_id: Optional[int] = Field(default=None, description="创作库素材ID")
    benchmark_material_ids_json: Optional[List[int]] = Field(default=None, description="对标素材ID列表")
    template_ids_json: Optional[List[int]] = Field(default=None, description="模板ID列表")
    sub_user_ids_json: Optional[List[int]] = Field(default=None, description="目标创作者ID列表")
    
    # 模型配置
    model_platform: Optional[str] = Field(default=None, description="文本模型平台")
    model_id: Optional[str] = Field(default=None, description="文本模型ID")
    image_model_platform: Optional[str] = Field(default=None, description="图片模型平台")
    image_model_id: Optional[str] = Field(default=None, description="图片模型ID")
    model_selection_mode: Optional[str] = Field(default=None, description="模型选择模式")
    max_concurrency: Optional[int] = Field(default=None, description="最大并发数", ge=1, le=100)
    image_count: Optional[int] = Field(default=None, description="生成图片数量", ge=1, le=10)
    
    # 变量值配置
    variable_values_json: Optional[Dict[str, Any]] = Field(default=None, description="变量值JSON")
    
    # 文案去重配置
    dedup_enabled: Optional[bool] = Field(default=None, description="文案去重检测开关")
    dedup_threshold: Optional[int] = Field(default=None, description="文案去重阈值", ge=0, le=100)
    dedup_retry_count: Optional[int] = Field(default=None, description="文案去重失败重试次数", ge=0, le=10)
    dedup_scope: Optional[List[str]] = Field(default=None, description="文案去重范围配置")
    
    # 图片去重配置
    image_dedup_enabled: Optional[bool] = Field(default=None, description="图片去重检测开关")
    image_dedup_threshold: Optional[int] = Field(default=None, description="图片相似度阈值", ge=0, le=100)
    image_dedup_retry_count: Optional[int] = Field(default=None, description="图片去重失败重试次数", ge=0, le=10)
    image_dedup_scope: Optional[List[str]] = Field(default=None, description="图片去重范围")
    
    # 对标配置
    benchmark_text_enabled: Optional[bool] = Field(default=None, description="文案对标开关")
    benchmark_image_enabled: Optional[bool] = Field(default=None, description="图片对标开关")
    benchmark_image_reference_options: Optional[List[str]] = Field(default=None, description="图片参考选项")
    benchmark_image_roles_json: Optional[Dict[str, List[str]]] = Field(default=None, description="对标图角色配置")
    template_product_mapping_json: Optional[Dict[str, str]] = Field(default=None, description="模板产品映射")
    
    # 状态管理
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    status: Optional[str] = Field(default=None, description="任务状态：active / paused / disabled")


class ScheduledTaskResponse(BaseSchema):
    """
    定时任务响应
    """
    id: int = Field(..., description="主键")
    name: str = Field(..., description="定时任务名称")
    task_type: str = Field(..., description="任务类型：custom / benchmark")
    
    # 调度配置
    schedule_type: str = Field(..., description="调度类型：daily / weekly")
    schedule_config_json: Dict[str, Any] = Field(..., description="调度配置JSON")
    
    # 素材和模板配置
    material_id: Optional[int] = Field(default=None, description="创作库素材ID")
    material_title: Optional[str] = Field(default=None, description="素材标题")
    benchmark_material_ids_json: Optional[List[int]] = Field(default=None, description="对标素材ID列表")
    benchmark_material_titles: Optional[List[str]] = Field(default=None, description="对标素材标题列表")
    template_ids_json: Optional[List[int]] = Field(default=None, description="模板ID列表")
    template_names: Optional[List[str]] = Field(default=None, description="模板名称列表")
    sub_user_ids_json: List[int] = Field(..., description="目标创作者ID列表")
    sub_user_names: Optional[List[str]] = Field(default=None, description="创作者名称列表")
    
    # 模型配置
    model_platform: Optional[str] = Field(default=None, description="文本模型平台")
    model_id: Optional[str] = Field(default=None, description="文本模型ID")
    image_model_platform: Optional[str] = Field(default=None, description="图片模型平台")
    image_model_id: Optional[str] = Field(default=None, description="图片模型ID")
    model_selection_mode: str = Field(..., description="模型选择模式")
    max_concurrency: int = Field(..., description="最大并发数")
    image_count: int = Field(..., description="生成图片数量")
    
    # 变量值配置
    variable_values_json: Optional[Dict[str, Any]] = Field(default=None, description="变量值JSON")
    
    # 文案去重配置
    dedup_enabled: Optional[bool] = Field(default=None, description="文案去重检测开关")
    dedup_threshold: Optional[int] = Field(default=None, description="文案去重阈值")
    dedup_retry_count: Optional[int] = Field(default=None, description="文案去重失败重试次数")
    dedup_scope: Optional[List[str]] = Field(default=None, description="文案去重范围配置")
    
    # 图片去重配置
    image_dedup_enabled: Optional[bool] = Field(default=None, description="图片去重检测开关")
    image_dedup_threshold: Optional[int] = Field(default=None, description="图片相似度阈值")
    image_dedup_retry_count: Optional[int] = Field(default=None, description="图片去重失败重试次数")
    image_dedup_scope: Optional[List[str]] = Field(default=None, description="图片去重范围")
    
    # 对标配置
    benchmark_text_enabled: Optional[bool] = Field(default=None, description="文案对标开关")
    benchmark_image_enabled: Optional[bool] = Field(default=None, description="图片对标开关")
    benchmark_image_reference_options: Optional[List[str]] = Field(default=None, description="图片参考选项")
    benchmark_image_roles_json: Optional[Dict[str, List[str]]] = Field(default=None, description="对标图角色配置")
    template_product_mapping_json: Optional[Dict[str, str]] = Field(default=None, description="模板产品映射")
    
    # 状态管理
    is_active: bool = Field(..., description="是否启用")
    status: str = Field(..., description="任务状态：active / paused / disabled")
    
    # 执行统计
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    last_execution_at: Optional[datetime] = Field(default=None, description="最后执行时间")
    last_execution_status: Optional[str] = Field(default=None, description="最后执行状态")
    
    # 下次执行时间
    next_execution_at: Optional[datetime] = Field(default=None, description="下次执行时间")
    
    # 多租户
    owner_operator_id: int = Field(..., description="所属创作管理员ID")
    owner_operator_name: Optional[str] = Field(default=None, description="所属创作管理员名称")
    created_by: Optional[int] = Field(default=None, description="创建者ID")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ScheduledTaskBrief(BaseSchema):
    """
    定时任务简要信息（用于列表展示）
    """
    id: int = Field(..., description="主键")
    name: str = Field(..., description="定时任务名称")
    task_type: str = Field(..., description="任务类型")
    schedule_type: str = Field(..., description="调度类型")
    schedule_config_json: Dict[str, Any] = Field(..., description="调度配置JSON")
    status: str = Field(..., description="任务状态")
    is_active: bool = Field(..., description="是否启用")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    next_execution_at: Optional[datetime] = Field(default=None, description="下次执行时间")
    last_execution_at: Optional[datetime] = Field(default=None, description="最后执行时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ScheduledTaskExecutionLog(BaseModel):
    """
    定时任务执行日志
    
    注意：执行历史记录只有 created_at，没有 updated_at（记录只读，不会更新）
    """
    model_config = {"from_attributes": True}
    
    id: int = Field(..., description="主键")
    scheduled_task_id: int = Field(..., description="定时任务ID")
    generation_task_id: Optional[int] = Field(default=None, description="生成的任务ID")
    execution_type: str = Field(..., description="执行类型：scheduled(定时) / manual(手动)")
    scheduled_at: datetime = Field(..., description="计划执行时间")
    started_at: Optional[datetime] = Field(default=None, description="实际开始执行时间")
    completed_at: Optional[datetime] = Field(default=None, description="执行完成时间")
    execution_time: datetime = Field(..., description="执行时间")
    status: str = Field(..., description="执行状态：pending(排队中) / running(执行中) / completed(完成) / failed(失败) / partial(部分成功) / cancelled(已取消)")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    total_items: Optional[int] = Field(default=None, description="总生成项数")
    success_items: Optional[int] = Field(default=None, description="成功项数")
    failed_items: Optional[int] = Field(default=None, description="失败项数")
    created_at: datetime = Field(..., description="创建时间")


class ScheduledTaskExecuteNow(BaseModel):
    """
    立即执行定时任务请求（测试用）
    """
    pass