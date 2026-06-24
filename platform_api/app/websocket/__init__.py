"""
WebSocket 模块

包含实时通信处理。
"""

from .manager import ConnectionManager, get_manager, manager

__all__ = [
    "ConnectionManager",
    "manager",
    "get_manager",
]
