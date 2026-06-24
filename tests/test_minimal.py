"""
最小化测试 - 检查数据库和fixtures是否正常工作

Author: Claude Code
Date: 2025
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "platform_api"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operator import Operator
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_operator(async_session: AsyncSession):
    """测试创建创作管理员"""
    operator = Operator(
        userid="test_user",
        nickname="测试用户",
        hashed_password=get_password_hash("test123"),
        status="online",
    )
    
    async_session.add(operator)
    await async_session.commit()
    await async_session.refresh(operator)
    
    # 验证
    assert operator.id is not None
    assert operator.userid == "test_user"
    assert operator.nickname == "测试用户"
    assert operator.status == "online"
    
    print(f"✅ Operator created successfully: id={operator.id}, userid={operator.userid}")


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])