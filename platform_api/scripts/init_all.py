#!/usr/bin/env python3
"""
统一初始化脚本 - 完整支持三层架构

从 init_data.yaml 读取配置并初始化数据库：
- 超级管理员（如果不存在）- 系统级配置
- 模型配置（系统级）
- 创作管理员及其业务数据（嵌套结构，支持三层架构）：
  - template_platform → template_category → template_tag
  - material_platform → material_category → material_tag
  - user_tags
  - prompt_templates

数据结构说明：
- 超级管理员：系统级配置，仅管理模型配置
- 创作管理员：业务数据所有者，每个创作管理员拥有独立的业务数据

使用方法：
  python scripts/init_all.py
"""

import os
import sys
import yaml
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal as async_session_factory, async_engine
from app.models import (
    SuperAdmin, Operator, ModelConfig,
    TemplatePlatform, TemplateCategory, TemplateTag,
    MaterialPlatform, MaterialCategory, MaterialTag,
    UserTag, CreativeSeed, ViralType
)
from app.core.security import get_password_hash


def substitute_env_vars(value):
    """
    替换字符串中的环境变量引用
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


async def init_super_admin(config: dict):
    """
    初始化超级管理员（系统级配置）
    """
    admin_config = config.get('super_admin', {})
    if not admin_config:
        print("跳过超级管理员初始化：配置不存在")
        return

    userid = substitute_env_vars(admin_config.get('userid', ''))
    password = substitute_env_vars(admin_config.get('password', ''))
    nickname = substitute_env_vars(admin_config.get('nickname', ''))
    display_name = substitute_env_vars(admin_config.get('display_name', '系统管理员'))

    if not userid or not password:
        print("跳过超级管理员初始化：缺少 userid 或 password")
        return

    async with async_session_factory() as session:
        result = await session.execute(
            select(SuperAdmin).where(SuperAdmin.userid == userid)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"超级管理员已存在，跳过：{userid}")
            return

        admin = SuperAdmin(
            userid=userid,
            nickname=nickname,
            display_name=display_name,
            hashed_password=get_password_hash(password),
        )
        session.add(admin)
        await session.commit()
        print(f"创建超级管理员：{userid}")


async def init_model_configs(config: dict):
    """
    初始化模型配置（系统级，仅超级管理员可管理）
    
    支持更新已存在的配置（仅更新非空字段）
    """
    model_configs = config.get('model_configs', [])
    if not model_configs:
        print("跳过模型配置初始化：配置不存在")
        return

    async with async_session_factory() as session:
        added_count = 0
        updated_count = 0
        
        for config_data in model_configs:
            # 替换环境变量
            config_data_processed = dict(config_data)
            if 'config_json' in config_data_processed:
                config_json = config_data_processed['config_json']
                if isinstance(config_json, dict):
                    config_json_processed = {}
                    for key, value in config_json.items():
                        config_json_processed[key] = substitute_env_vars(value)
                    config_data_processed['config_json'] = config_json_processed

            result = await session.execute(
                select(ModelConfig).where(
                    ModelConfig.platform == config_data_processed['platform'],
                    ModelConfig.model_id == config_data_processed['model_id']
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新已存在的配置（仅更新非空字段）
                updated = False
                
                # 更新 config_json（如果 YAML 中有值且不为空）
                if config_data_processed.get('config_json'):
                    new_config_json = config_data_processed['config_json']
                    # 检查是否有 api_key 需要更新
                    if new_config_json.get('api_key'):
                        if not existing.config_json or not existing.config_json.get('api_key'):
                            # 数据库中没有 api_key，更新整个 config_json
                            existing.config_json = new_config_json
                            updated = True
                            print(f"  更新模型配置 api_key：{config_data_processed['platform']} - {config_data_processed['model_id']}")
                
                # 更新其他字段（如果 YAML 中有值）
                if config_data_processed.get('model_name') and existing.model_name != config_data_processed['model_name']:
                    existing.model_name = config_data_processed['model_name']
                    updated = True
                if config_data_processed.get('base_url') and existing.base_url != config_data_processed['base_url']:
                    existing.base_url = config_data_processed['base_url']
                    updated = True
                if config_data_processed.get('max_concurrency') and existing.max_concurrency != config_data_processed['max_concurrency']:
                    existing.max_concurrency = config_data_processed['max_concurrency']
                    updated = True
                
                if updated:
                    updated_count += 1
                else:
                    print(f"  模型配置已存在且无需更新：{config_data_processed['platform']} - {config_data_processed['model_id']}")
                continue

            model_config = ModelConfig(
                platform=config_data_processed['platform'],
                model_id=config_data_processed['model_id'],
                model_name=config_data_processed['model_name'],
                model_type=config_data_processed['model_type'],
                base_url=config_data_processed.get('base_url'),
                api_endpoint=config_data_processed.get('api_endpoint'),
                is_default=config_data_processed.get('is_default', False),
                max_concurrency=config_data_processed.get('max_concurrency', 5),
                config_json=config_data_processed.get('config_json'),
                status=config_data_processed.get('status', 'active'),
                is_system=True,
            )
            session.add(model_config)
            added_count += 1
            print(f"  添加模型配置：{config_data_processed['platform']} - {config_data_processed['model_id']}")

        await session.commit()
        print(f"模型配置初始化完成，新增 {added_count} 条，更新 {updated_count} 条")


async def init_viral_types(config: dict):
    """
    初始化爆款类型配置（系统级，仅超级管理员可管理）
    """
    viral_types = config.get('viral_types', [])
    if not viral_types:
        print("跳过爆款类型配置初始化：配置不存在")
        return

    async with async_session_factory() as session:
        added_count = 0
        updated_count = 0

        for idx, type_data in enumerate(viral_types, 1):
            value = type_data.get('value')
            if not value:
                continue

            # 检查是否已存在
            result = await session.execute(
                select(ViralType).where(ViralType.value == value)
            )
            existing = result.scalar_one_or_none()

            # 处理 keywords - 转换为 JSON 字符串
            keywords = type_data.get('keywords', [])
            keywords_json = json.dumps(keywords) if keywords else None

            if existing:
                # 更新现有记录
                existing.label = type_data.get('label', existing.label)
                existing.description = type_data.get('description', existing.description)
                existing.keywords = keywords_json
                existing.sort_order = type_data.get('sort_order', idx)
                existing.is_system = type_data.get('is_system', True)
                updated_count += 1
                print(f"  更新爆款类型：{value} - {type_data.get('label')}")
            else:
                # 创建新记录
                viral_type = ViralType(
                    value=value,
                    label=type_data.get('label'),
                    description=type_data.get('description'),
                    keywords=keywords_json,
                    sort_order=type_data.get('sort_order', idx),
                    status='enabled',
                    is_system=type_data.get('is_system', True),
                )
                session.add(viral_type)
                added_count += 1
                print(f"  添加爆款类型：{value} - {type_data.get('label')}")

        await session.commit()
        print(f"爆款类型配置初始化完成，新增 {added_count} 条，更新 {updated_count} 条")


async def init_operator_with_data(operator_config: dict) -> int:
    """
    初始化创作管理员及其关联的业务数据（完整三层架构）

    Args:
        operator_config: 创作管理员配置（包含嵌套的业务数据）

    Returns:
        int: 创作管理员 ID
    """
    userid = substitute_env_vars(operator_config.get('userid', ''))
    password = substitute_env_vars(operator_config.get('password', ''))
    nickname = substitute_env_vars(operator_config.get('nickname', ''))
    display_name = substitute_env_vars(operator_config.get('display_name', '创作管理员'))

    if not userid or not password:
        print(f"  跳过创作管理员初始化：缺少 userid 或 password")
        return 0

    async with async_session_factory() as session:
        # 检查是否已存在创作管理员
        result = await session.execute(
            select(Operator).where(Operator.userid == userid)
        )
        existing = result.scalar_one_or_none()

        if existing:
            operator_id = existing.id
            print(f"  创作管理员已存在：{userid} (ID: {operator_id})")
        else:
            # 创建新的创作管理员
            operator = Operator(
                userid=userid,
                nickname=nickname,
                display_name=display_name,
                hashed_password=get_password_hash(password),
                status='offline',
            )
            session.add(operator)
            await session.commit()
            await session.refresh(operator)
            operator_id = operator.id
            print(f"  创建创作管理员：{userid} (ID: {operator_id})")

        # 初始化该创作管理员的业务数据
        await _init_operator_business_data(session, operator_config, operator_id)

        return operator_id


async def _init_operator_business_data(session, operator_config: dict, operator_id: int):
    """
    初始化创作管理员的业务数据（完整三层架构）

    Args:
        session: 数据库会话
        operator_config: 创作管理员配置
        operator_id: 创作管理员 ID
    """
    # ================================================================================
    # 1. 初始化模板平台 → 分类 → 标签（三层架构）
    # ================================================================================
    template_platform_ids: dict[str, int] = {}
    template_platform_configs = operator_config.get('template_platforms', [])

    for platform_config in template_platform_configs:
        # 检查平台是否存在
        result = await session.execute(
            select(TemplatePlatform).where(
                TemplatePlatform.name == platform_config['name'],
                TemplatePlatform.owner_operator_id == operator_id
            ).limit(1)
        )
        existing_platform = result.scalar()

        if not existing_platform:
            platform = TemplatePlatform(
                name=platform_config['name'],
                description=platform_config.get('description'),
                color=platform_config.get('color'),
                platform_code=platform_config.get('platform_code'),
                config_json=platform_config.get('config_json'),
                sort_order=platform_config.get('sort_order', 0),
                created_by=operator_id,
                owner_operator_id=operator_id,
            )
            session.add(platform)
            await session.flush()
            await session.refresh(platform)
            platform_id = platform.id
            template_platform_ids[platform_config['name']] = platform_id
            print(f"    添加模板平台：{platform_config['name']} (ID: {platform_id})")
        else:
            platform_id = existing_platform.id
            template_platform_ids[platform_config['name']] = platform_id
            print(f"    模板平台已存在：{platform_config['name']} (ID: {platform_id})")

        # 初始化该平台下的分类
        category_configs = platform_config.get('categories', [])
        template_category_ids: dict[str, int] = {}

        for category_config in category_configs:
            result = await session.execute(
                select(TemplateCategory).where(
                    TemplateCategory.name == category_config['name'],
                    TemplateCategory.owner_operator_id == operator_id
                ).limit(1)
            )
            existing_category = result.scalar()

            if not existing_category:
                category = TemplateCategory(
                    name=category_config['name'],
                    description=category_config.get('description'),
                    color=category_config.get('color'),
                    template_platform_id=platform_id,
                    sort_order=category_config.get('sort_order', 0),
                    created_by=operator_id,
                    owner_operator_id=operator_id,
                )
                session.add(category)
                await session.flush()
                await session.refresh(category)
                category_id = category.id
                template_category_ids[category_config['name']] = category_id
                print(f"      添加模板分类：{category_config['name']} (ID: {category_id})")
            else:
                category_id = existing_category.id
                template_category_ids[category_config['name']] = category_id
                print(f"      模板分类已存在：{category_config['name']} (ID: {category_id})")

            # 初始化该分类下的标签
            tag_configs = category_config.get('tags', [])

            for tag_config in tag_configs:
                result = await session.execute(
                    select(TemplateTag).where(
                        TemplateTag.name == tag_config['name'],
                        TemplateTag.category_id == category_id
                    ).limit(1)
                )
                existing_tag = result.scalar()

                if not existing_tag:
                    tag = TemplateTag(
                        name=tag_config['name'],
                        description=tag_config.get('description'),
                        color=tag_config.get('color'),
                        category_id=category_id,
                        is_system=tag_config.get('is_system', False),
                        created_by=operator_id,
                        owner_operator_id=operator_id,
                    )
                    session.add(tag)
                    print(f"        添加模板标签：{tag_config['name']}")
                else:
                    print(f"        模板标签已存在：{tag_config['name']}")

        await session.flush()

    # ================================================================================
    # 2. 初始化素材平台 → 分类 → 标签（三层架构）
    # ================================================================================
    material_platform_ids: dict[str, int] = {}
    material_platform_configs = operator_config.get('material_platforms', [])

    for platform_config in material_platform_configs:
        # 检查平台是否存在
        result = await session.execute(
            select(MaterialPlatform).where(
                MaterialPlatform.name == platform_config['name'],
                MaterialPlatform.owner_operator_id == operator_id
            ).limit(1)
        )
        existing_platform = result.scalar()

        if not existing_platform:
            platform = MaterialPlatform(
                name=platform_config['name'],
                description=platform_config.get('description'),
                color=platform_config.get('color'),
                platform_code=platform_config.get('platform_code'),
                config_json=platform_config.get('config_json'),
                sort_order=platform_config.get('sort_order', 0),
                created_by=operator_id,
                owner_operator_id=operator_id,
            )
            session.add(platform)
            await session.flush()
            await session.refresh(platform)
            platform_id = platform.id
            material_platform_ids[platform_config['name']] = platform_id
            print(f"    添加素材平台：{platform_config['name']} (ID: {platform_id})")
        else:
            platform_id = existing_platform.id
            material_platform_ids[platform_config['name']] = platform_id
            print(f"    素材平台已存在：{platform_config['name']} (ID: {platform_id})")

        # 初始化该平台下的分类
        category_configs = platform_config.get('categories', [])
        material_category_ids: dict[str, int] = {}

        for category_config in category_configs:
            result = await session.execute(
                select(MaterialCategory).where(
                    MaterialCategory.name == category_config['name'],
                    MaterialCategory.owner_operator_id == operator_id
                ).limit(1)
            )
            existing_category = result.scalar()

            if not existing_category:
                category = MaterialCategory(
                    name=category_config['name'],
                    description=category_config.get('description'),
                    color=category_config.get('color'),
                    material_platform_id=platform_id,
                    sort_order=category_config.get('sort_order', 0),
                    created_by=operator_id,
                    owner_operator_id=operator_id,
                )
                session.add(category)
                await session.flush()
                await session.refresh(category)
                category_id = category.id
                material_category_ids[category_config['name']] = category_id
                print(f"      添加素材分类：{category_config['name']} (ID: {category_id})")
            else:
                category_id = existing_category.id
                material_category_ids[category_config['name']] = category_id
                print(f"      素材分类已存在：{category_config['name']} (ID: {category_id})")

            # 初始化该分类下的标签
            tag_configs = category_config.get('tags', [])

            for tag_config in tag_configs:
                result = await session.execute(
                    select(MaterialTag).where(
                        MaterialTag.name == tag_config['name'],
                        MaterialTag.category_id == category_id,
                        MaterialTag.owner_operator_id == operator_id
                    ).limit(1)
                )
                existing_tag = result.scalar()

                if not existing_tag:
                    tag = MaterialTag(
                        name=tag_config['name'],
                        description=tag_config.get('description'),
                        color=tag_config.get('color'),
                        category_id=category_id,
                        is_system=tag_config.get('is_system', False),
                        created_by=operator_id,
                        owner_operator_id=operator_id,
                    )
                    session.add(tag)
                    print(f"        添加素材标签：{tag_config['name']}")
                else:
                    print(f"        素材标签已存在：{tag_config['name']}")

        await session.flush()

    # ================================================================================
    # 3. 初始化用户标签（简单列表）
    # ================================================================================
    user_tag_configs = operator_config.get('user_tags', [])
    for tag_config in user_tag_configs:
        result = await session.execute(
            select(UserTag).where(
                UserTag.name == tag_config['name'],
                UserTag.created_by == operator_id
            ).limit(1)
        )
        existing_tag = result.scalar()

        if not existing_tag:
            tag = UserTag(
                name=tag_config['name'],
                tag_type=tag_config.get('tag_type', 'subuser_tag'),
                description=tag_config.get('description'),
                color=tag_config.get('color'),
                created_by=operator_id,
            )
            session.add(tag)
            print(f"    添加用户标签：{tag_config['name']}")
        else:
            print(f"    用户标签已存在：{tag_config['name']}")

    # ================================================================================
    # 4. 初始化创意种子库（开头模式、情感基调、结尾模式）
    # ================================================================================
    creative_seed_configs = operator_config.get('creative_seeds', [])
    for seed_config in creative_seed_configs:
        result = await session.execute(
            select(CreativeSeed).where(
                CreativeSeed.name == seed_config['name'],
                CreativeSeed.seed_type == seed_config['seed_type'],
                CreativeSeed.owner_operator_id == operator_id
            ).limit(1)
        )
        existing_seed = result.scalar()

        if not existing_seed:
            # 处理数组字段 - 转换为 JSON 字符串
            template = seed_config.get('template', [])
            forbidden_patterns = seed_config.get('forbidden_patterns', [])
            example_phrases = seed_config.get('example_phrases', [])
            avoid_phrases = seed_config.get('avoid_phrases', [])

            seed = CreativeSeed(
                name=seed_config['name'],
                seed_type=seed_config['seed_type'],
                template=json.dumps(template) if template else None,
                description=seed_config.get('description'),
                forbidden_patterns=json.dumps(forbidden_patterns) if forbidden_patterns else None,
                example_phrases=json.dumps(example_phrases) if example_phrases else None,
                avoid_phrases=json.dumps(avoid_phrases) if avoid_phrases else None,
                category=seed_config.get('category', '通用'),
                status=seed_config.get('status', 'enabled'),
                is_system=seed_config.get('is_system', False),
                owner_operator_id=operator_id,
                use_count=seed_config.get('use_count', 0),
            )
            session.add(seed)
            print(f"    添加创意种子：{seed_config['name']} ({seed_config['seed_type']})")
        else:
            print(f"    创意种子已存在：{seed_config['name']} ({seed_config['seed_type']})")

    await session.commit()
    print(f"    业务数据初始化完成！")


async def init_all():
    """
    初始化所有数据
    """
    # 查找配置文件
    config_path = Path(__file__).parent.parent / 'config' / 'init_data.yaml'

    if not config_path.exists():
        config_path = Path(__file__).parent.parent.parent / 'config' / 'init_data.yaml'

    if not config_path.exists():
        print(f"配置文件不存在：{config_path}")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print("\n" + "=" * 60)
    print("1. 初始化超级管理员（系统级配置）")
    print("=" * 60)
    await init_super_admin(config)

    print("\n" + "=" * 60)
    print("2. 初始化模型配置（系统级）")
    print("=" * 60)
    await init_model_configs(config)

    print("\n" + "=" * 60)
    print("3. 初始化爆款类型配置（系统级）")
    print("=" * 60)
    await init_viral_types(config)

    # 初始化创作管理员及其业务数据（支持单个对象或数组）
    operator_admin_data = config.get('operator_admin', [])
    operator_admins = []
    if isinstance(operator_admin_data, dict):
        operator_admins = [operator_admin_data]
    elif isinstance(operator_admin_data, list):
        operator_admins = operator_admin_data

    if operator_admins:
        for idx, operator_config in enumerate(operator_admins, 1):
            print("\n" + "=" * 60)
            print(f"4.{idx}. 初始化创作管理员及其业务数据")
            print("=" * 60)
            operator_id = await init_operator_with_data(operator_config)

    print("\n" + "=" * 60)
    print("初始化完成！")
    print("=" * 60)
    print("\n数据结构说明：")
    print("  - 超级管理员：系统级配置，仅管理模型配置")
    print("  - 创作管理员：业务数据所有者")
    print("  - 模板架构：Platform → Category → Tag 三层")
    print("  - 素材架构：Platform → Category → Tag 三层")
    return True


async def main():
    """主函数，执行初始化并清理连接池"""
    success = await init_all()
    # 显式关闭连接池，防止垃圾回收时报错
    engine = async_engine()  # async_engine 是函数，需要调用获取 engine
    await engine.dispose()
    return success


if __name__ == '__main__':
    print("=" * 60)
    print("妙笔内容工场 - 统一初始化脚本（完整三层架构）")
    print("=" * 60)
    print("\n数据结构说明：")
    print("  - 超级管理员：系统级配置（仅管理模型配置）")
    print("  - 创作管理员：业务数据所有者")
    print("  - 支持三层架构：Platform → Category → Tag")
    print("=" * 60)
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
