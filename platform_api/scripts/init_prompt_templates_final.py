#!/usr/bin/env python3
"""
初始化创作管理员的提示词模板（最终版本）

从 init_data.yaml 读取配置并初始化：
- 创建创作管理员（如果不存在）
- 初始化提示词模板，归属到指定创作管理员

使用方法：
  python scripts/init_prompt_templates_final.py
"""

import os
import sys
import yaml
from pathlib import Path

# 首先设置环境变量，覆盖默认配置
os.environ['DATABASE_URL'] = 'mysql+pymysql://aigc_user:aigc_password123@localhost:3306/aigc_platform'

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session

# 重新导入配置，确保使用我们设置的环境变量
from app.core.database import SyncSessionLocal
from app.models import Operator, PromptTemplate
from app.core.security import get_password_hash


def init_operator():
    """
    初始化创作管理员
    """
    operator_userid = "O_OvUQvegVpXAmJOTi"
    operator_password = "12345678"
    operator_nickname = "创作管理员"

    with SyncSessionLocal() as session:
        result = session.execute(
            select(Operator).where(Operator.userid == operator_userid)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"创作管理员已存在，跳过创建: {operator_userid}")
            return existing.id

        operator = Operator(
            userid=operator_userid,
            nickname=operator_nickname,
            hashed_password=get_password_hash(operator_password),
            status="active",
        )
        session.add(operator)
        session.commit()
        session.refresh(operator)
        print(f"创建创作管理员: {operator_userid} (ID: {operator.id})")
        return operator.id


def init_prompt_templates(config: dict, operator_id: int):
    """
    初始化提示词模板
    """
    items = config.get('prompt_templates', [])
    if not items:
        print("配置中没有找到 prompt_templates")
        return

    with SyncSessionLocal() as session:
        added_count = 0
        for item_data in items:
            result = session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.name == item_data['name'],
                    PromptTemplate.owner_operator_id == operator_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"提示词模板已存在，跳过: {item_data['name']}")
                continue

            # 更新配置中的 owner_operator_id
            item_data_for_create = dict(item_data)
            item_data_for_create['owner_operator_id'] = operator_id

            # 处理 applicable_platforms - 如果是字符串，尝试转换为列表
            applicable_platforms = item_data_for_create.get('applicable_platforms')
            if isinstance(applicable_platforms, str):
                # 如果是类似 "小红书" 的字符串，转换为单元素列表
                applicable_platforms = [applicable_platforms]

            item = PromptTemplate(
                name=item_data_for_create['name'],
                template_type=item_data_for_create['template_type'],
                content=item_data_for_create['content'],
                applicable_platforms=applicable_platforms,
                variables_hint=item_data_for_create.get('variables_hint'),
                description=item_data_for_create.get('description'),
                is_default=item_data_for_create.get('is_default', False),
                status=item_data_for_create.get('status', 'enabled'),
                owner_operator_id=operator_id,
            )
            session.add(item)
            print(f"添加提示词模板: {item_data_for_create['name']} (owner: {operator_id})")
            added_count += 1

        session.commit()

        if added_count > 0:
            print(f"\n成功添加 {added_count} 个提示词模板")
        else:
            print("没有添加新的提示词模板（都已存在）")

        # 统计该创作管理员的所有模板
        result = session.execute(
            select(PromptTemplate).where(PromptTemplate.owner_operator_id == operator_id)
        )
        all_templates = result.scalars().all()
        print(f"\n创作管理员 (ID: {operator_id}) 当前共有 {len(all_templates)} 个提示词模板:")
        for template in all_templates:
            print(f"  - {template.name} ({template.template_type})")


def init_all():
    """
    初始化所有数据
    """
    # 先尝试脚本所在项目的 config 目录，再尝试项目根目录
    config_path = Path(__file__).parent.parent / 'config' / 'init_data.yaml'

    if not config_path.exists():
        config_path = Path(__file__).parent.parent.parent / 'config' / 'init_data.yaml'

    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print("\n" + "=" * 60)
    print("1. 初始化创作管理员")
    print("=" * 60)
    operator_id = init_operator()

    print("\n" + "=" * 60)
    print(f"2. 初始化提示词模板 (归属创作管理员 ID: {operator_id})")
    print("=" * 60)
    init_prompt_templates(config, operator_id)

    print("\n" + "=" * 60)
    print("初始化完成！")
    print("=" * 60)
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("妙笔内容工场 - 创作管理员提示词模板初始化")
    print("=" * 60)
    print(f"数据库连接: {os.environ.get('DATABASE_URL')}")
    try:
        # 测试数据库连接
        print("\n测试数据库连接...")
        with SyncSessionLocal() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
        print("数据库连接成功！\n")

        success = init_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n提示：请确保数据库已启动并配置正确的连接信息")
        sys.exit(1)
