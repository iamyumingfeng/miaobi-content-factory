"""
Alembic 环境配置文件
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 将项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入配置和 Base
from app.core.config import get_settings
from app.core.database import Base

# 导入所有模型以确保 Alembic 能检测所有表变更
from app.models.user_base import UserBase
from app.models.super_admin import SuperAdmin
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.models.user_tag import UserTag, UserTagRel
from app.models.material import (
    Material, MaterialPlatform, MaterialCategory, MaterialTag,
    MaterialTagRel, MaterialAttachment, MaterialFavorite
)
from app.models.template import Template, TemplateCategory, TemplateTag
from app.models.generation import GenerationTaskTemplate
from app.models.template_platform import TemplatePlatform
from app.models.generation import GenerationTask, GenerationItem, GenerationTaskProgressLog
from app.models.system import OperationLog, ModelConfig

settings = get_settings()

# Alembic Config 对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 配置数据库 URL（从环境变量获取）
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("+aiomysql", "+pymysql")
)

# 模型的 MetaData
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    只需要 URL，不需要创建 Engine。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    需要创建 Engine 和关联 Connection。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 比较字段类型变化
            compare_server_default=True,  # 比较服务器默认值
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
