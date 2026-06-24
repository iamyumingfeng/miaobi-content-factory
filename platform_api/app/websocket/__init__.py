"""
WebSocket 模块

包含实时通信处理。
"""

from .manager import ConnectionManager, manager, get_manager

__all__ = [
    "ConnectionManager",
    "manager",
    "get_manager",
]
