#!/usr/bin/env python3
"""
初始化模板和标签数据 - 完整三层架构支持

支持：
- TemplatePlatform -> TemplateCategory -> TemplateTag
- MaterialPlatform -> MaterialCategory -> MaterialTag
- UserTag
- PromptTemplate

Author: Claude Code
Date: 2025
"""
import asyncio
import yaml
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal as async_session_factory
from app.core.security import get_password_hash
from app.models import (
    Operator,
    TemplatePlatform, TemplateCategory, TemplateTag,
    MaterialPlatform, MaterialCategory, MaterialTag,
    UserTag, PromptTemplate,
)


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


def substitute_env_vars_in_dict(data: dict) -> dict:
    """
    递归替换字典中的环境变量引用
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = substitute_env_vars_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                substitute_env_vars_in_dict(item) if isinstance(item, dict)
                else substitute_env_vars(item)
                for item in value
            ]
        else:
            result[key] = substitute_env_vars(value)
    return result


async def init_template_platform_with_categories_and_tags(
    session: AsyncSession,
    platform_config: dict,
    operator_id: int,
) -> TemplatePlatform:
    """
    初始化模板平台及其分类和标签（三层架构）
    """
    # 1. 检查或创建平台
    result = await session.execute(
        select(TemplatePlatform).where(
            TemplatePlatform.name == platform_config["name"],
            TemplatePlatform.owner_operator_id == operator_id,
        )
    )
    platform = result.scalar_one_or_none()

    if not platform:
        platform = TemplatePlatform(
            name=platform_config["name"],
            description=platform_config.get("description"),
            color=platform_config.get("color"),
            platform_code=platform_config.get("platform_code"),
            config_json=platform_config.get("config_json"),
            sort_order=platform_config.get("sort_order", 0),
            created_by=operator_id,
            owner_operator_id=operator_id,
        )
        session.add(platform)
        await session.flush()
        await session.refresh(platform)
        print(f"  ✅ 添加模板平台: {platform_config['name']}")
    else:
        print(f"  ⚠️ 模板平台已存在: {platform_config['name']}")

    # 2. 处理该平台下的分类
    category_configs = platform_config.get("categories", [])
    for category_config in category_configs:
        result = await session.execute(
            select(TemplateCategory).where(
                TemplateCategory.name == category_config["name"],
                TemplateCategory.owner_operator_id == operator_id,
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            category = TemplateCategory(
                name=category_config["name"],
                description=category_config.get("description"),
                color=category_config.get("color"),
                template_platform_id=platform.id,
                owner_operator_id=operator_id,
                created_by=operator_id,
                sort_order=category_config.get("sort_order", 0),
            )
            session.add(category)
            await session.flush()
            await session.refresh(category)
            print(f"    ✅ 添加模板分类: {category_config['name']}")
        else:
            print(f"    ⚠️ 模板分类已存在: {category_config['name']}")

        # 3. 处理该分类下的标签
        tag_configs = category_config.get("tags", [])
        for tag_config in tag_configs:
            result = await session.execute(
                select(TemplateTag).where(
                    TemplateTag.name == tag_config["name"],
                    TemplateTag.category_id == category.id,
                )
            )
            tag = result.scalar_one_or_none()

            if not tag:
                tag = TemplateTag(
                    name=tag_config["name"],
                    description=tag_config.get("description"),
                    color=tag_config.get("color"),
                    category_id=category.id,
                    is_system=tag_config.get("is_system", False),
                    created_by=operator_id,
                )
                session.add(tag)
                print(f"      ✅ 添加模板标签: {tag_config['name']}")
            else:
                print(f"      ⚠️ 模板标签已存在: {tag_config['name']}")

    await session.commit()
    return platform


async def init_material_platform_with_categories_and_tags(
    session: AsyncSession,
    platform_config: dict,
    operator_id: int,
) -> MaterialPlatform:
    """
    初始化素材平台及其分类和标签（三层架构）
    """
    # 1. 检查或创建平台
    result = await session.execute(
        select(MaterialPlatform).where(
            MaterialPlatform.name == platform_config["name"],
            MaterialPlatform.owner_operator_id == operator_id,
        )
    )
    platform = result.scalar_one_or_none()

    if not platform:
        platform = MaterialPlatform(
            name=platform_config["name"],
            description=platform_config.get("description"),
            color=platform_config.get("color"),
            platform_code=platform_config.get("platform_code"),
            config_json=platform_config.get("config_json"),
            sort_order=platform_config.get("sort_order", 0),
            created_by=operator_id,
            owner_operator_id=operator_id,
        )
        session.add(platform)
        await session.flush()
        await session.refresh(platform)
        print(f"  ✅ 添加素材平台: {platform_config['name']}")
    else:
        print(f"  ⚠️ 素材平台已存在: {platform_config['name']}")

    # 2. 处理该平台下的分类
    category_configs = platform_config.get("categories", [])
    for category_config in category_configs:
        result = await session.execute(
            select(MaterialCategory).where(
                MaterialCategory.name == category_config["name"],
                MaterialCategory.owner_operator_id == operator_id,
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            category = MaterialCategory(
                name=category_config["name"],
                description=category_config.get("description"),
                color=category_config.get("color"),
                material_platform_id=platform.id,
                owner_operator_id=operator_id,
                created_by=operator_id,
                sort_order=category_config.get("sort_order", 0),
            )
            session.add(category)
            await session.flush()
            await session.refresh(category)
            print(f"    ✅ 添加素材分类: {category_config['name']}")
        else:
            print(f"    ⚠️ 素材分类已存在: {category_config['name']}")

        # 3. 处理该分类下的标签
        tag_configs = category_config.get("tags", [])
        for tag_config in tag_configs:
            result = await session.execute(
                select(MaterialTag).where(
                    MaterialTag.name == tag_config["name"],
                    MaterialTag.category_id == category.id,
                )
            )
            tag = result.scalar_one_or_none()

            if not tag:
                tag = MaterialTag(
                    name=tag_config["name"],
                    description=tag_config.get("description"),
                    color=tag_config.get("color"),
                    category_id=category.id,
                    is_system=tag_config.get("is_system", False),
                    created_by=operator_id,
                    owner_operator_id=operator_id,
                )
                session.add(tag)
                print(f"      ✅ 添加素材标签: {tag_config['name']}")
            else:
                print(f"      ⚠️ 素材标签已存在: {tag_config['name']}")

    await session.commit()
    return platform


async def main():
    print("=" * 60)
    print("初始化模板和标签数据 - 完整三层架构支持")
    print("=" * 60)

    # 查找配置文件
    config_path = Path("/config") / "init_data.yaml"
    print(f"尝试路径1: {config_path} (exists: {config_path.exists()})")
    if not config_path.exists():
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "init_data.yaml"
        print(f"尝试路径2: {config_path} (exists: {config_path.exists()})")
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config" / "init_data.yaml"
        print(f"尝试路径3: {config_path} (exists: {config_path.exists()})")
    if not config_path.exists():
        config_path = Path(__file__).parent.parent.parent / "config" / "init_data.yaml"
        print(f"尝试路径4: {config_path} (exists: {config_path.exists()})")
    if not config_path.exists():
        raise FileNotFoundError(f"找不到 init_data.yaml，已尝试所有路径")
    print(f"使用配置文件: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 替换配置中的环境变量引用
    data = substitute_env_vars_in_dict(data)

    async with async_session_factory() as session:
        # ========================================
        # 1. 初始化创作管理员
        # ========================================
        operator_admin_config = data.get("operator_admin", {})
        operator_id = None

        if operator_admin_config:
            # 处理单对象或数组的情况
            if isinstance(operator_admin_config, list):
                operator_admin_config = operator_admin_config[0] if operator_admin_config else {}

            userid = operator_admin_config.get("userid", os.getenv("INITIAL_OPERATOR_ADMIN_USERID", "operator"))
            password = operator_admin_config.get("password", os.getenv("INITIAL_OPERATOR_ADMIN_PASSWORD", "operator123"))
            nickname = operator_admin_config.get("nickname", os.getenv("INITIAL_OPERATOR_ADMIN_NICKNAME", "默认创作管理员"))
            display_name = operator_admin_config.get("display_name", "创作管理员")

            existing = await session.execute(
                select(Operator).where(Operator.userid == userid)
            )
            operator = existing.scalar_one_or_none()
            if not operator:
                operator = Operator(
                    userid=userid,
                    hashed_password=get_password_hash(password),
                    nickname=nickname,
                    display_name=display_name,
                    status="offline",
                )
                session.add(operator)
                await session.flush()
                await session.refresh(operator)
                operator_id = operator.id
                print(f"✅ 创作管理员 {userid} 创建完成")
            else:
                operator_id = operator.id
                print(f"⚠️ 创作管理员 {userid} 已存在，跳过")

        # 如果没有创建或找到，使用默认值1
        if not operator_id:
            operator_id = 1
            print(f"ℹ️ 使用默认创作管理员ID: {operator_id}")

        # ========================================
        # 2. 处理模板平台三层架构
        # ========================================
        print("\n" + "=" * 60)
        print("2. 初始化模板平台（Platform -> Category -> Tag）")
        print("=" * 60)
        template_platforms_config = operator_admin_config.get("template_platforms", [])
        for platform_config in template_platforms_config:
            await init_template_platform_with_categories_and_tags(
                session, platform_config, operator_id
            )

        # ========================================
        # 3. 处理素材平台三层架构
        # ========================================
        print("\n" + "=" * 60)
        print("3. 初始化素材平台（Platform -> Category -> Tag）")
        print("=" * 60)
        material_platforms_config = operator_admin_config.get("material_platforms", [])
        for platform_config in material_platforms_config:
            await init_material_platform_with_categories_and_tags(
                session, platform_config, operator_id
            )

        # ========================================
        # 4. 处理用户标签
        # ========================================
        print("\n" + "=" * 60)
        print("4. 初始化用户标签")
        print("=" * 60)
        user_tags_config = operator_admin_config.get("user_tags", [])
        for item in user_tags_config:
            existing = await session.execute(
                select(UserTag).where(
                    UserTag.name == item["name"],
                    UserTag.created_by == operator_id,
                )
            )
            if not existing.scalars().first():
                session.add(UserTag(
                    name=item["name"],
                    tag_type=item.get("tag_type", "subuser_tag"),
                    description=item.get("description"),
                    color=item.get("color"),
                    created_by=operator_id,
                ))
                print(f"✅ 添加用户标签: {item['name']}")
            else:
                print(f"⚠️ 用户标签已存在: {item['name']}")

        await session.commit()

        # ========================================
        # 5. 处理提示词模板
        # ========================================
        print("\n" + "=" * 60)
        print("5. 初始化提示词模板")
        print("=" * 60)
        prompt_templates_config = operator_admin_config.get("prompt_templates", [])
        for item in prompt_templates_config:
            existing = await session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.name == item["name"],
                    PromptTemplate.owner_operator_id == operator_id,
                )
            )
            if not existing.scalars().first():
                session.add(PromptTemplate(
                    name=item["name"],
                    template_type=item["template_type"],
                    content=item["content"],
                    applicable_platforms=item.get("applicable_platforms"),
                    variables_hint=item.get("variables_hint"),
                    description=item.get("description"),
                    is_default=item.get("is_default", False),
                    status=item.get("status", "enabled"),
                    owner_operator_id=operator_id,
                ))
                print(f"✅ 添加提示词模板: {item['name']}")
            else:
                print(f"⚠️ 提示词模板已存在: {item['name']}")

        await session.commit()

        print("\n" + "=" * 60)
        print("✅ 所有数据初始化完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
