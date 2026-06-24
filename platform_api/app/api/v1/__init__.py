"""
API v1 路由模块

包含版本 1 的所有 API 端点。
"""

from fastapi import APIRouter

from . import auth
from . import users
from . import templates
from . import materials
from . import generation
from . import distribution
from . import settings
from . import dashboard
from . import operation_logs
from . import trend_analysis
from . import creative_seeds
from . import platform_config
from . import scheduled_tasks
from . import task_queue

# 主路由（禁用自动斜杠重定向，避免 POST body 丢失）
router = APIRouter(redirect_slashes=False)

# 包含所有子路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(users.router, prefix="/users", tags=["用户管理"])
# 平台分类已拆分到 materials/platforms 和 templates/platforms
router.include_router(templates.router, prefix="/templates", tags=["模板管理"])
router.include_router(materials.router, prefix="/materials", tags=["素材管理"])
router.include_router(generation.router, prefix="/generation", tags=["内容生成"])
router.include_router(distribution.router, prefix="/distribution", tags=["内容分发"])
router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
router.include_router(operation_logs.router, prefix="/operation-logs", tags=["操作日志"])
router.include_router(trend_analysis.router, prefix="/trend-analysis", tags=["趋势分析"])
router.include_router(creative_seeds.router, prefix="/creative-seeds", tags=["创意种子库"])
router.include_router(platform_config.router, prefix="/config", tags=["平台配置"])
router.include_router(scheduled_tasks.router, prefix="/scheduled-tasks", tags=["定时任务"])
router.include_router(task_queue.router, prefix="/task-queue", tags=["任务队列管理"])

__all__ = ["router"]
