"""
数据库连接管理模块 (database.py)

提供 SQLAlchemy 数据库连接和 Session 管理。

Dependencies:
    - sqlalchemy: ORM 框架
    - app.core.config: 配置管理

Author: Claude Code
Date: 2025
"""

from typing import Any, AsyncGenerator, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

# ============================================
# 异步数据库引擎
# 懒创建：在进程首次需要时创建，而非模块导入时。
# 配合 Celery worker_process_init 信号解决 prefork fork 后
# aiomysql 连接池事件循环冲突问题。
# ============================================

# 模块级标记：当前进程是否已初始化过 engine
_process_async_initialized: bool = False
_async_engine: Any = None  # Any = AsyncEngine，避免循环导入
_async_sessionmaker: Any = None


def _create_async_engine_for_current_process():
    """
    为当前进程创建异步 engine。
    每个进程（API 主进程 / Celery worker 子进程）调用一次，
    各自拥有独立的连接池，绑定到各自的事件循环。
    """
    return create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=settings.database_pool_pre_ping,
        pool_recycle=getattr(settings, "database_pool_recycle", 1800),  # 连接回收时间
        echo=settings.database_echo,
    )


def _get_async_engine():
    """获取当前进程的异步 engine（懒创建）。"""
    global _async_engine, _process_async_initialized
    if not _process_async_initialized:
        _async_engine = _create_async_engine_for_current_process()
        _process_async_initialized = True
    return _async_engine


def _get_async_sessionmaker():
    """获取当前进程的异步 sessionmaker（懒创建）。"""
    global _async_sessionmaker, _process_async_initialized
    if not _process_async_initialized:
        engine = _get_async_engine()
        _async_sessionmaker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_sessionmaker


def _invalidate_process_async_engine():
    """
    关闭并重置当前进程的 async engine。
    由 Celery worker_process_init 信号调用，
    确保 worker 子进程不继承父进程（Celery launcher）的 engine，
    而是创建属于自己事件循环的全新 engine。

    也可在每个 Celery 任务执行前/后调用，
    防止连接池绑定到已关闭的事件循环。
    """
    global _async_engine, _async_sessionmaker, _process_async_initialized
    if _async_engine is not None:
        try:
            import asyncio

            # 同步等待 dispose 完成，避免异步调度导致引擎被置为 None 但资源未释放
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_async_engine.dispose())
            finally:
                loop.close()
        except Exception:
            # 忽略关闭错误（进程正在退出或循环已关闭）
            pass
        _async_engine = None
        _async_sessionmaker = None
        _process_async_initialized = False


# ============================================
# async_session_maker 兼容层
# ============================================
class _AsyncSessionContext:
    """
    每次 `async with async_session_maker():` 创建一个新实例，
    彼此独立，避免并发冲突。
    """

    __slots__ = ("_maker", "_session")

    def __init__(self):
        self._maker = _get_async_sessionmaker()
        self._session = None

    def __call__(self):
        return self._maker()

    async def __aenter__(self) -> AsyncSession:
        # async_sessionmaker() 返回 AsyncSession 实例（不是 maker 本身）
        # AsyncSession 才有 __aenter__/__aexit__
        self._session = self._maker()
        await self._session.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None


def async_session_maker():
    return _AsyncSessionContext()


# 兼容旧代码：保持 AsyncSessionLocal 别名（脚本直接导入使用）
AsyncSessionLocal = _AsyncSessionContext


# 兼容直接 engine 引用（如 async_engine.dispose()）
# 每次调用返回当前进程的 engine（懒创建）
def async_engine():
    return _get_async_engine()


# ============================================
# 同步数据库引擎（Celery 和 Alembic 用）
# 同步 engine 不受 fork 事件循环影响，可以全局复用
# ============================================
sync_database_url = settings.database_url.replace("+aiomysql", "+pymysql")
sync_engine = create_engine(
    sync_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=settings.database_pool_pre_ping,
    pool_recycle=getattr(settings, "database_pool_recycle", 1800),  # 连接回收时间
    echo=settings.database_echo,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# ============================================
# 基类（用于模型定义）
# ============================================
Base = declarative_base()


# ============================================
# 依赖注入用的数据库会话获取
# ============================================
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_db() -> Generator[sessionmaker, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================
# 数据库健康检查
# ============================================
async def check_database_connection() -> bool:
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return True
    except Exception:
        return False


def check_sync_database_connection() -> bool:
    try:
        with SyncSessionLocal() as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
