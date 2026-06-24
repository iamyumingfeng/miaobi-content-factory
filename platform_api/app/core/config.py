"""
配置管理模块 (config.py)

使用 Pydantic Settings 管理应用配置，支持环境变量加载。

Dependencies:
    - pydantic-settings: 配置管理
    - python-dotenv: .env 文件加载

Author: Claude Code
Date: 2025
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


def get_version() -> str:
    """
    从 VERSION 文件中读取版本号

    Returns:
        str: 版本号，读取失败时返回 "1.0.0"
    """
    # VERSION 文件在 platform_api 目录下
    version_file = Path(__file__).parent.parent / "VERSION"
    try:
        if version_file.exists():
            version = version_file.read_text().strip()
            if version:
                return version
    except Exception:
        pass
    return "1.0.0"


class Settings(BaseSettings):
    """
    应用配置类

    所有配置项都可以通过环境变量覆盖，环境变量名为大写形式。
    例如：DATABASE_URL 对应 database_url 字段。
    """

    # ============================================
    # 应用基础配置
    # ============================================
    app_name: str = "Miaobi Content Factory"
    app_version: str = get_version()
    debug: bool = False
    api_prefix: str = "/api/v1"

    # ============================================
    # 数据库配置
    # ============================================
    # 连接池配置说明：
    # - pool_size: 核心连接数，常驻连接
    # - max_overflow: 溢出连接数，高峰时额外创建的连接
    # - 总最大连接数 = pool_size + max_overflow = 80
    # 注意：MySQL max_connections 需要设置为 >= 100
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/aigc_platform"
    database_pool_size: int = 50  # 增加核心连接数（原 20）
    database_max_overflow: int = 30  # 增加溢出连接数（原 10）
    database_pool_pre_ping: bool = True
    database_echo: bool = False
    # 连接回收时间（秒），防止连接长时间闲置被 MySQL 断开
    database_pool_recycle: int = 1800  # 30 分钟

    # ============================================
    # JWT 认证配置
    # ============================================
    # ⚠️  安全警告：必须通过环境变量 SECRET_KEY 设置密钥
    # 不要在代码中硬编码密钥！
    secret_key: str = ""  # 必须从环境变量读取
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # ============================================
    # Redis 配置
    # ============================================
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 256
    redis_socket_connect_timeout: float = 5.0
    redis_socket_timeout: float = 5.0

    # ============================================
    # 腾讯云 COS 配置
    # ============================================
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_bucket: str = ""
    cos_region: str = "ap-guangzhou"
    cos_mount_path: str = "/app/cos"
    cos_url_prefix: str = ""
    cos_path_prefix: str = ""

    # ============================================
    # 图片处理配置
    # ============================================
    # 参考图传输方式：True=公网URL，False=Base64（本地开发推荐）
    # 本地环境用 Base64 避免公网访问问题；公网部署用 URL 减少数据传输
    image_prefer_url: bool = False

    # ============================================
    # 存储 URL 类型配置
    # ============================================
    # 文件访问 URL 类型：
    # - "auto": 自动检测（默认），有 COS 配置时返回 COS URL，否则返回 IP 路径
    # - "local": 强制返回本地路径 (/cos/...)
    # - "cos": 强制返回 COS 公网 URL（需要配置 COS）
    # - "ip": 强制返回服务器 IP + 路径格式 (http://your-ip/cos/...)
    storage_url_type: str = "auto"
    storage_url_prefix: str = "http://127.0.0.1:8000"

    # ============================================
    # 服务器公网地址配置
    # ============================================
    # 用于生成 "ip" 类型的访问 URL，例如：http://your-server-ip
    server_domain: str = ""

    # ============================================
    # Celery 配置
    # ============================================
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_task_soft_time_limit: int = 300
    celery_task_time_limit: int = 600
    celery_concurrency: int = 32  # Celery Worker 并发数
    task_queue_max_concurrent: int = (
        64  # 任务队列最大并发数（建议为 Worker 并发数的 2 倍）
    )

    # ============================================
    # 日志配置
    # ============================================
    log_level: str = "INFO"
    log_file_path: str = "./logs/app.log"
    log_json_format: bool = False

    # ============================================
    # CORS 配置
    # ============================================
    cors_origins: str = (
        "http://localhost,http://localhost:80,http://localhost:3000,http://localhost:5173"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS origins 列表"""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # ============================================
    # 安全配置
    # ============================================
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15
    password_min_length: int = 12

    # ============================================
    # 初始超级管理员配置
    # ============================================
    initial_super_admin_userid: str = "admin"
    initial_super_admin_password: str = "admin123"
    initial_super_admin_nickname: str = "超级管理员"

    # ============================================
    # 初始创作管理员配置
    # ============================================
    initial_operator_admin_userid: str = "operator"
    initial_operator_admin_password: str = "operator123"
    initial_operator_admin_nickname: str = "默认创作管理员"

    # ============================================
    # 平台模型类型配置
    # ============================================
    # 格式: platform_id -> model_types (逗号分隔，可选值: llm, image, video)
    # 示例: bailian -> llm,image
    platform_bailian_types: str = "llm,image,embedding"
    platform_volcano_types: str = "llm,image"
    platform_jimeng_types: str = "image,video"
    platform_kling_types: str = "image,video"
    platform_zhipu_types: str = "llm,image"
    platform_moonshot_types: str = "llm"
    platform_deepseek_types: str = "llm"
    platform_lingyaai_types: str = "llm,image"
    platform_4sapi_types: str = "llm,image"

    # ============================================
    # 优化版生成器配置
    # ============================================
    # 是否启用优化版生成器（减少 LLM 调用次数）
    # True: 使用优化版（推荐，1-5 次调用/item）
    # False: 使用原版（7-9+ 次调用/item）
    use_optimized_generator: bool = True

    # ============================================
    # 三阶段事务架构配置（推荐）
    # ============================================
    # 是否启用三阶段事务架构（解决长时间持有数据库连接问题）
    # True: 使用三阶段架构（推荐）
    #   - 阶段1: 读取数据（<1秒）
    #   - 阶段2: AI生成（30-90秒，无数据库连接）
    #   - 阶段3: 保存结果（<1秒）
    # False: 使用原有单阶段架构
    # 连接持有时间：100秒 → <2秒，利用率提升50倍
    use_phased_transaction: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

    @property
    def effective_celery_broker_url(self) -> str:
        """获取有效的 Celery Broker URL"""
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_result_backend(self) -> str:
        """获取有效的 Celery Result Backend URL"""
        return self.celery_result_backend or self.redis_url

    def get_platform_model_types(self, platform_id: str) -> List[str]:
        """
        获取指定平台的模型类型配置

        Args:
            platform_id: 平台ID（如 bailian, volcano, jimeng 等）

        Returns:
            该平台启用的模型类型列表（如 ['llm', 'image']）
        """
        env_var = f"platform_{platform_id}_types"
        types_str = getattr(self, env_var, "")
        if not types_str:
            return []
        return [t.strip() for t in types_str.split(",") if t.strip()]

    def get_all_platform_model_types(self) -> dict:
        """
        获取所有平台的模型类型配置

        Returns:
            dict: { platform_id: [model_types] }
        """
        platforms = [
            "bailian",
            "volcano",
            "jimeng",
            "kling",
            "zhipu",
            "moonshot",
            "deepseek",
            "lingyaai",
            "4sapi",
        ]
        result = {}
        for platform in platforms:
            types = self.get_platform_model_types(platform)
            if types:
                result[platform] = types
        return result


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保只加载一次配置。

    Returns:
        Settings: 应用配置对象
    """
    return Settings()
