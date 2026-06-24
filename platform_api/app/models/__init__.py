"""
数据模型模块

包含所有 SQLAlchemy 模型定义。

用户相关模型（按角色分表，物理隔离）：
- SuperAdmin: 超级管理员
- Operator: 创作管理员
- SubUser: 创作者
- UserTag: 用户标签
- UserTagRel: 用户标签关联

分类标签管理相关模型（3层结构：平台→分类→标签）：
- MaterialPlatform: 素材库平台表
- MaterialCategory: 素材分类表
- MaterialTag: 素材标签表
- TemplatePlatform: 模板库平台表
- TemplateCategory: 模板分类表
- TemplateTag: 模板标签表

模板管理相关模型：
- TemplateTag: 模板标签
- TemplateTagRel: 模板标签关联
- TemplateFavorite: 模板收藏
- TemplateAttachment: 模板附件
- Template: 模板

素材管理相关模型：
- MaterialCategory: 素材分类
- MaterialTag: 素材标签
- MaterialTagRel: 素材标签关联
- MaterialFavorite: 素材收藏
- MaterialAttachment: 素材附件
- Material: 素材

内容生成相关模型（核心模块）：
- GenerationTaskTemplate: 任务-模板关联
- GenerationTaskSubuser: 任务-创作者关联
- GenerationTaskProgressLog: 任务进度快照
- GenerationTask: 生成任务（主表）
- GenerationItem: 生成子任务/明细
- ScheduledTask: 定时任务（自动调度生成任务）

内容分发相关模型：
- Distribution: 分发记录
- PublishAccount: 发布账号

系统管理相关模型：
- OperationLog: 操作日志
- CleanupRule: 清理规则
- ModelConfig: 模型配置
"""

# 用户相关
from .user_base import UserBase
from .super_admin import SuperAdmin
from .operator import Operator
from .sub_user import SubUser
from .user_tag import UserTag, UserTagRel

# 素材库平台（独立3层分类标签体系顶层）
from .material import (
    Material,
    MaterialPlatform,
    MaterialCategory,
    MaterialTag,
    MaterialTagRel,
    MaterialFavorite,
    MaterialAttachment,
)

# 模板库平台（独立3层分类标签体系顶层）
from .template_platform import TemplatePlatform
from .template import Template, TemplateCategory, TemplateTag, TemplateTagRel, TemplateAttachment

# 内容生成相关
from .generation import (
    GenerationTask,
    GenerationTaskTemplate,
    GenerationTaskSubuser,
    GenerationTaskProgressLog,
    GenerationItem,
    GenerationItemExecutionLog,
    ContentEmbedding,
)
from .scheduled_task import ScheduledTask
from .scheduled_task_execution import ScheduledTaskExecution

# 内容分发相关
from .distribution import Distribution, PublishAccount

# 系统管理相关
from .system import (
    OperationLog,
    CleanupRule,
    ModelConfig,
)
from .user_default_model import UserDefaultModel

# 创意种子库
from .creative_seed import CreativeSeed

# 爆款类型配置
from .viral_type import ViralType

# 仪表盘相关
from .dashboard import DashboardAlertDismissal

# Token 相关
from .refresh_token import RefreshToken

__all__ = [
    # 用户相关
    "UserBase",
    "SuperAdmin",
    "Operator",
    "SubUser",
    "UserTag",
    "UserTagRel",
    # 素材库平台（独立）
    "MaterialPlatform",
    "Material",
    "MaterialCategory",
    "MaterialTag",
    "MaterialTagRel",
    "MaterialFavorite",
    "MaterialAttachment",
    # 模板库平台（独立）
    "TemplatePlatform",
    "Template",
    "TemplateCategory",
    "TemplateTag",
    "TemplateTagRel",
    "TemplateAttachment",
    # 内容生成相关
    "GenerationTask",
    "GenerationTaskTemplate",
    "GenerationTaskSubuser",
    "GenerationTaskProgressLog",
    "GenerationItem",
    "GenerationItemExecutionLog",
    "ContentEmbedding",
    "ScheduledTask",
    "ScheduledTaskExecution",
    # 内容分发相关
    "Distribution",
    "PublishAccount",
    # 系统管理相关
    "OperationLog",
    "CleanupRule",
    "ModelConfig",
    "UserDefaultModel",
    # 创意种子库
    "CreativeSeed",
    # 爆款类型配置
    "ViralType",
    # 仪表盘相关
    "DashboardAlertDismissal",
    # Token 相关
    "RefreshToken",
]
