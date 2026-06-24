"""
WebSocket 连接管理器 (manager.py)

管理 WebSocket 连接和实时消息推送。

Author: Claude Code
Date: 2025
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    WebSocket 连接管理器

    管理所有活动的 WebSocket 连接，并提供消息广播功能。
    """

    def __init__(self):
        # 按创作管理员 ID 分组的连接
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # 按任务 ID 订阅的连接
        self.task_subscriptions: Dict[int, Set[WebSocket]] = {}
        # 连接锁
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, operator_id: int, db=None):
        """
        建立连接

        Args:
            websocket: WebSocket 对象
            operator_id: 创作管理员 ID
            db: 数据库会话（用于验证用户状态）
        """
        # 检查用户是否被禁用
        if db:
            user_status = await self._get_user_status(operator_id, db)
            if user_status == "disabled":
                # 用户已被禁用，拒绝连接并通知
                await websocket.accept()
                await websocket.send_json({
                    "type": "account_disabled",
                    "message": "账号已被禁用，请联系管理员",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await websocket.close(code=4001, reason="Account disabled")
                return False
        
        await websocket.accept()
        async with self._lock:
            if operator_id not in self.active_connections:
                self.active_connections[operator_id] = set()
            self.active_connections[operator_id].add(websocket)
        return True

    async def _get_user_status(self, operator_id: int, db) -> Optional[str]:
        """
        获取用户状态

        Args:
            operator_id: 创作管理员 ID
            db: 数据库会话

        Returns:
            用户状态或 None
        """
        from sqlalchemy import select
        from app.models.operator import Operator

        try:
            result = await db.execute(
                select(Operator.status).where(Operator.id == operator_id)
            )
            status = result.scalar_one_or_none()
            return status
        except Exception:
            return None

    async def disconnect(self, websocket: WebSocket, operator_id: int):
        """
        断开连接

        Args:
            websocket: WebSocket 对象
            operator_id: 创作管理员 ID
        """
        async with self._lock:
            if operator_id in self.active_connections:
                self.active_connections[operator_id].discard(websocket)
                if not self.active_connections[operator_id]:
                    del self.active_connections[operator_id]

            # 同时清理任务订阅
            for task_id in list(self.task_subscriptions.keys()):
                self.task_subscriptions[task_id].discard(websocket)
                if not self.task_subscriptions[task_id]:
                    del self.task_subscriptions[task_id]

    async def disconnect_operator(self, operator_id: int, reason: str = "账号已被禁用"):
        """
        断开指定创作管理员的所有连接并发送通知

        Args:
            operator_id: 创作管理员 ID
            reason: 断开原因
        """
        disconnected = []
        message = {
            "type": "force_logout",
            "message": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        async with self._lock:
            if operator_id not in self.active_connections:
                return

            for connection in list(self.active_connections[operator_id]):
                try:
                    await connection.send_json(message)
                    await connection.close(code=4001, reason=reason)
                    disconnected.append(connection)
                except Exception:
                    disconnected.append(connection)

            # 清理所有断开或已关闭的连接
            for connection in disconnected:
                self.active_connections[operator_id].discard(connection)
                # 清理所有任务订阅
                for task_id in list(self.task_subscriptions.keys()):
                    self.task_subscriptions[task_id].discard(connection)

            if not self.active_connections[operator_id]:
                del self.active_connections[operator_id]

    async def notify_account_disabled(self, operator_id: int):
        """
        向指定用户发送账号禁用通知

        Args:
            operator_id: 创作管理员 ID
        """
        await self.broadcast_to_operator(
            {
                "type": "account_disabled",
                "message": "账号已被禁用，请联系管理员",
                "timestamp": datetime.utcnow().isoformat(),
            },
            operator_id
        )

    async def subscribe_to_task(self, websocket: WebSocket, task_id: int):
        """
        订阅任务进度

        Args:
            websocket: WebSocket 对象
            task_id: 任务 ID
        """
        async with self._lock:
            if task_id not in self.task_subscriptions:
                self.task_subscriptions[task_id] = set()
            self.task_subscriptions[task_id].add(websocket)

    async def unsubscribe_from_task(self, websocket: WebSocket, task_id: int):
        """
        取消订阅任务进度

        Args:
            websocket: WebSocket 对象
            task_id: 任务 ID
        """
        async with self._lock:
            if task_id in self.task_subscriptions:
                self.task_subscriptions[task_id].discard(websocket)
                if not self.task_subscriptions[task_id]:
                    del self.task_subscriptions[task_id]

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket,
    ):
        """
        发送个人消息

        Args:
            message: 消息内容
            websocket: 目标 WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception:
            # 连接可能已断开
            pass

    async def broadcast_to_operator(
        self,
        message: Dict[str, Any],
        operator_id: int,
    ):
        """
        向指定创作管理员的所有连接广播消息

        Args:
            message: 消息内容
            operator_id: 创作管理员 ID
        """
        if operator_id not in self.active_connections:
            return

        # 创建要发送的消息副本
        message_copy = message.copy()
        message_copy["timestamp"] = datetime.utcnow().isoformat()

        disconnected = []
        async with self._lock:
            for connection in self.active_connections[operator_id]:
                try:
                    await connection.send_json(message_copy)
                except Exception:
                    disconnected.append(connection)

            # 清理断开的连接
            for connection in disconnected:
                self.active_connections[operator_id].discard(connection)

            if not self.active_connections[operator_id]:
                del self.active_connections[operator_id]

    async def broadcast_task_update(
        self,
        task_id: int,
        update_data: Dict[str, Any],
    ):
        """
        广播任务更新

        Args:
            task_id: 任务 ID
            update_data: 更新数据
        """
        if task_id not in self.task_subscriptions:
            return

        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        disconnected = []
        async with self._lock:
            for connection in self.task_subscriptions[task_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # 清理断开的连接
            for connection in disconnected:
                self.task_subscriptions[task_id].discard(connection)

            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]


# 全局连接管理器实例
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """
    获取全局连接管理器实例

    Returns:
        ConnectionManager: 连接管理器
    """
    return manager
