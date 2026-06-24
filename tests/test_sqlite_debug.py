"""
SQLite调试测试 - 查看表创建SQL

Author: Claude Code
Date: 2025
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "platform_api"))

from sqlalchemy import create_engine, event, text, MetaData

# 显式导入所有模型
from app.models.user_base import UserBase
from app.models.operator import Operator
from app.models.sub_user import SubUser
from app.models.super_admin import SuperAdmin
from app.models.material import Material
from app.models.template import Template
from app.models.scheduled_task import ScheduledTask
from app.core.database import Base


def test_sqlite_table_creation():
    """测试SQLite表创建"""
    
    print(f"\n=== Registered Tables ===\n{list(Base.metadata.tables.keys())}\n")
    
    # 创建同步引擎（用于调试）
    engine = create_engine(
        "sqlite:///:memory:",
        echo=True,  # 显示SQL
    )
    
    # 创建所有表
    print("\n=== Creating Tables ===\n")
    Base.metadata.create_all(engine)
    
    # 检查表结构
    print("\n=== Checking Table Schemas ===\n")
    with engine.connect() as conn:
        # 列出所有表
        result = conn.execute(text("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"))
        rows = result.fetchall()
        print(f"Found {len(rows)} tables:")
        for name, sql in rows:
            print(f"\n=== {name} ===")
            if sql:
                print(sql[:500])  # 只显示前500字符
            else:
                print("(No SQL)")


if __name__ == "__main__":
    test_sqlite_table_creation()
