#!/usr/bin/env python3
"""初始化模型配置"""
import asyncio
import yaml
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal as async_session_factory
from app.models import ModelConfig


def substitute_env_vars(value):
    """替换字符串中的环境变量引用"""
    if not isinstance(value, str):
        return value

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


async def main():
    print("初始化模型配置...")

    config_path = Path("/config") / "init_data.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "init_data.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config" / "init_data.yaml"
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    async with async_session_factory() as session:
        for model_cfg in data.get("model_configs", []):
            existing = await session.execute(
                select(ModelConfig).where(
                    ModelConfig.platform == model_cfg["platform"],
                    ModelConfig.model_id == model_cfg["model_id"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            if 'config_json' in model_cfg:
                config_json = model_cfg['config_json']
                if isinstance(config_json, dict):
                    for key, value in config_json.items():
                        config_json[key] = substitute_env_vars(value)

            cfg = ModelConfig(
                platform=model_cfg["platform"],
                model_id=model_cfg["model_id"],
                model_name=model_cfg["model_name"],
                model_type=model_cfg["model_type"],
                base_url=model_cfg.get("base_url"),
                is_default=model_cfg.get("is_default", False),
                max_concurrency=model_cfg.get("max_concurrency", 5),
                config_json=model_cfg.get("config_json"),
                status=model_cfg.get("status", "active"),
                is_system=True,
            )
            session.add(cfg)

        await session.commit()
        print("✅ 模型配置初始化完成")


if __name__ == "__main__":
    asyncio.run(main())
