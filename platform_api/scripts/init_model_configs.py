#!/usr/bin/env python3
"""
初始化模型配置脚本

从 init_data.yaml 读取配置并初始化数据库中的模型配置
支持环境变量替换，例如 ${BAILIAN_API_KEY:-}
"""

import os
import sys
import yaml
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal as async_session_factory
from app.models import ModelConfig
from app.core.security import get_password_hash


def substitute_env_vars(value):
    """
    替换字符串中的环境变量引用
    格式: ${VAR_NAME:-default_value}
    """
    if not isinstance(value, str):
        return value

    import re
    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_spec = match.group(1)
        if ':-' in var_spec:
            var_name, default = var_spec.split(':-', 1)
        else:
            var_name = var_spec
            default = ''
        return os.environ.get(var_name, default)

    return re.sub(pattern, replace_var, value)


async def init_model_configs():
    """
    初始化模型配置
    """
    config_path = Path(__file__).parent.parent.parent / 'config' / 'init_data.yaml'

    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    model_configs = config.get('model_configs', [])

    if not model_configs:
        print("没有找到模型配置")
        return True

    async with async_session_factory() as session:
        for config_data in model_configs:
            # 替换环境变量
            if 'config_json' in config_data:
                config_json = config_data['config_json']
                if isinstance(config_json, dict):
                    for key, value in config_json.items():
                        config_json[key] = substitute_env_vars(value)

            # 检查是否已存在
            result = await session.execute(
                select(ModelConfig).where(
                    ModelConfig.platform == config_data['platform'],
                    ModelConfig.model_id == config_data['model_id']
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"模型配置已存在，跳过: {config_data['platform']} - {config_data['model_id']}")
                continue

            # 创建新配置
            model_config = ModelConfig(
                platform=config_data['platform'],
                model_id=config_data['model_id'],
                model_name=config_data['model_name'],
                model_type=config_data['model_type'],
                base_url=config_data.get('base_url'),
                api_endpoint=config_data.get('api_endpoint'),
                is_default=config_data.get('is_default', False),
                max_concurrency=config_data.get('max_concurrency', 5),
                config_json=config_data.get('config_json'),
                status=config_data.get('status', 'active'),
                is_system=True,
            )
            session.add(model_config)
            print(f"添加模型配置: {config_data['platform']} - {config_data['model_id']}")

        await session.commit()

    print("\n模型配置初始化完成！")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("初始化模型配置")
    print("=" * 60)
    try:
        success = asyncio.run(init_model_configs())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
