"""
妙笔内容工场 - FastAPI 主应用入口

Author: Claude Code
Date: 2025
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import (auth, creative_seeds, dashboard, distribution,
                        generation, materials, operation_logs, scheduled_tasks)
from app.api.v1 import settings as settings_api
from app.api.v1 import task_queue, templates, trend_analysis, users
from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.exceptions import AppException
from app.core.init_db import initialize_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 为素材上传调试启用 DEBUG 级别日志
logging.getLogger("app.services.storage_service").setLevel(logging.DEBUG)
logging.getLogger("app.api.v1.materials").setLevel(logging.DEBUG)
logging.getLogger("app.services.material_service").setLevel(logging.DEBUG)

# 为模板调试启用 DEBUG 级别日志
logging.getLogger("app.api.v1.templates").setLevel(logging.DEBUG)
logging.getLogger("app.services.template_service").setLevel(logging.DEBUG)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时
    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")

    # 检查数据库连接
    db_ok = await check_database_connection()
    if db_ok:
        logger.info("Database connected")
        # 初始化数据库和超级管理员
        await initialize_database()
    else:
        logger.warning("Database connection failed")

    yield

    # 关闭时
    logger.info(f"Shutting down {settings.app_name}...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="AIGC 内容创作平台 API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None,  # 关闭 Swagger UI 文档
    redoc_url=None,  # 关闭 ReDoc 文档
    openapi_url=None,  # 关闭 OpenAPI schema
    redirect_slashes=False,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# 挂载静态文件服务（用于本地开发时访问存储文件）
# 存储路径下的文件可以通过 /cos/ 前缀访问
from app.services.storage_service import get_storage_service

storage_service = get_storage_service()
storage_path = storage_service.local_storage_path

# 确保存储目录存在
storage_path.mkdir(parents=True, exist_ok=True)

app.mount("/cos", StaticFiles(directory=str(storage_path)), name="cos")
logger.info(f"Mounted static files: /cos -> {storage_path}")


# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    处理应用自定义异常
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    """
    import traceback

    error_detail = traceback.format_exc()
    logger.error(f"未捕获的异常: {exc}\n{error_detail}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "detail": error_detail},
    )


# 根路径
@app.get("/")
async def root():
    """
    根路径 - 健康检查
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }


@app.get("/api/version")
async def get_version():
    """
    获取版本信息端点

    返回后端版本号，每次请求都动态读取 VERSION 文件
    """

    def get_dynamic_version(version_file_path):
        """动态读取 VERSION 文件"""
        try:
            if version_file_path.exists():
                version = version_file_path.read_text().strip()
                if version:
                    return version
        except Exception:
            pass
        return "1.0.0"

    # 后端版本 - 支持多个可能的路径
    backend_version_files = [
        Path(__file__).parent / "VERSION",  # 本地开发: app/VERSION
        Path(__file__).parent.parent / "VERSION",  # Docker: /app/VERSION (从项目根目录)
        Path("/app/VERSION"),  # Docker 直接路径
    ]
    backend_version = "1.0.0"
    for vf in backend_version_files:
        if vf.exists():
            backend_version = get_dynamic_version(vf)
            break

    return {
        "backend_version": backend_version,
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    db_ok = await check_database_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


# 注册 API 路由
api_prefix = settings.api_prefix

app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["用户管理"])
# 平台分类已拆分到 materials/platforms 和 templates/platforms
app.include_router(
    templates.router, prefix=f"{api_prefix}/templates", tags=["模板管理"]
)
app.include_router(
    materials.router, prefix=f"{api_prefix}/materials", tags=["素材管理"]
)
app.include_router(
    generation.router, prefix=f"{api_prefix}/generation", tags=["内容生成"]
)
app.include_router(
    distribution.router, prefix=f"{api_prefix}/distribution", tags=["内容分发"]
)
app.include_router(
    settings_api.router, prefix=f"{api_prefix}/settings", tags=["系统设置"]
)
app.include_router(dashboard.router, prefix=f"{api_prefix}/dashboard", tags=["仪表盘"])
app.include_router(
    operation_logs.router, prefix=f"{api_prefix}/operation-logs", tags=["操作日志"]
)
app.include_router(
    trend_analysis.router, prefix=f"{api_prefix}/trend-analysis", tags=["趋势分析"]
)
app.include_router(
    creative_seeds.router, prefix=f"{api_prefix}/creative-seeds", tags=["创意种子库"]
)
app.include_router(
    scheduled_tasks.router, prefix=f"{api_prefix}/scheduled-tasks", tags=["定时任务"]
)
app.include_router(
    task_queue.router, prefix=f"{api_prefix}/task-queue", tags=["任务队列管理"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
