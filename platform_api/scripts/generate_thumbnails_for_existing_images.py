"""
为已存在的生成图片生成缩略图

运行方式：
    python scripts/generate_thumbnails_for_existing_images.py

此脚本会：
1. 查询所有有图片但没有缩略图的 generation_item
2. 为每个图片生成缩略图并保存
3. 更新数据库中的 generated_image_thumbnails_json 字段

Author: Claude Code
Date: 2026-05-05
"""

import os
import sys
import asyncio
import io
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, and_, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import GenerationItem, GenerationTask
from app.core.config import get_settings

try:
    from PIL import Image
except ImportError:
    print("请安装 Pillow: pip install Pillow")
    sys.exit(1)

try:
    import aiohttp
except ImportError:
    print("请安装 aiohttp: pip install aiohttp")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_image(session: aiohttp.ClientSession, url: str, timeout: int = 60) -> Optional[bytes]:
    """
    从URL下载图片

    Args:
        session: aiohttp会话
        url: 图片URL
        timeout: 超时时间

    Returns:
        Optional[bytes]: 图片二进制数据
    """
    try:
        # 检查是否是本地路径
        settings = get_settings()
        cos_mount_path = Path(settings.cos_mount_path)

        if url.startswith('/cos/'):
            local_path = cos_mount_path / url[5:]
            if local_path.exists():
                return local_path.read_bytes()

        # 如果是本地文件路径
        if Path(url).exists():
            return Path(url).read_bytes()

        # 从URL下载
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            response.raise_for_status()
            return await response.read()

    except Exception as e:
        logger.error(f"下载图片失败: {url}, error={e}")
        return None


def generate_thumbnail(image_bytes: bytes, thumbnail_size: Tuple[int, int] = (300, 300), quality: int = 85) -> Optional[bytes]:
    """
    生成缩略图

    Args:
        image_bytes: 原图二进制数据
        thumbnail_size: 缩略图最大尺寸
        quality: JPEG质量

    Returns:
        Optional[bytes]: 缩略图二进制数据
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # 转换为 RGB
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            else:
                image = image.convert('RGB')

        # 等比例缩放
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # 保存到内存
        output = io.BytesIO()
        image.save(output, 'JPEG', quality=quality, optimize=True)
        return output.getvalue()

    except Exception as e:
        logger.error(f"生成缩略图失败: {e}")
        return None


def get_thumbnail_path(original_url: str, cos_mount_path: Path) -> Optional[Path]:
    """
    根据原图URL推导缩略图保存路径

    原图路径: Tasks/{owner}/{date}/{task_id}/{item_id}/images/img_xxx.jpg
    缩略图路径: Tasks/{owner}/{date}/{task_id}/{item_id}/images/thumbnails/thumb_img_xxx.jpg

    Args:
        original_url: 原图URL
        cos_mount_path: COS挂载路径

    Returns:
        Optional[Path]: 缩略图保存路径
    """
    try:
        settings = get_settings()
        cos_url_prefix = f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com"

        # 从URL提取相对路径
        if original_url.startswith(cos_url_prefix):
            relative_path = original_url[len(cos_url_prefix) + 1:]
        elif original_url.startswith('/cos/'):
            relative_path = original_url[5:]
        else:
            # 尝试直接作为路径
            if Path(original_url).exists():
                # 本地路径，需要转换
                return None
            return None

        # 构建原图本地路径
        original_local_path = cos_mount_path / relative_path

        # 提取文件名
        filename = original_local_path.name

        # 构建缩略图路径: 在 images 目录下创建 thumbnails 子目录
        parent_dir = original_local_path.parent
        thumbnail_dir = parent_dir / "thumbnails"
        thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"

        return thumbnail_dir / thumb_filename

    except Exception as e:
        logger.error(f"推导缩略图路径失败: {original_url}, error={e}")
        return None


def path_to_url(file_path: Path, cos_mount_path: Path) -> str:
    """
    将本地路径转换为COS URL

    Args:
        file_path: 本地文件路径
        cos_mount_path: COS挂载路径

    Returns:
        str: COS URL
    """
    settings = get_settings()
    relative_path = file_path.relative_to(cos_mount_path)
    return f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{relative_path}"


async def process_item(
    db: AsyncSession,
    item: GenerationItem,
    session: aiohttp.ClientSession,
    cos_mount_path: Path,
    thumbnail_size: Tuple[int, int] = (300, 300),
    quality: int = 85,
) -> bool:
    """
    处理单个生成项，为其图片生成缩略图

    Args:
        db: 数据库会话
        item: 生成项
        session: aiohttp会话
        cos_mount_path: COS挂载路径
        thumbnail_size: 缩略图尺寸
        quality: JPEG质量

    Returns:
        bool: 是否成功
    """
    try:
        original_urls = item.generated_image_urls_json or []
        if not original_urls:
            return True

        thumbnail_urls = []
        success_count = 0

        for original_url in original_urls:
            # 下载原图
            image_bytes = await download_image(session, original_url)
            if not image_bytes:
                logger.warning(f"无法下载图片: {original_url}")
                thumbnail_urls.append(original_url)  # 使用原图作为fallback
                continue

            # 生成缩略图
            thumb_bytes = generate_thumbnail(image_bytes, thumbnail_size, quality)
            if not thumb_bytes:
                logger.warning(f"无法生成缩略图: {original_url}")
                thumbnail_urls.append(original_url)
                continue

            # 获取缩略图保存路径
            thumb_path = get_thumbnail_path(original_url, cos_mount_path)
            if not thumb_path:
                logger.warning(f"无法推导缩略图路径: {original_url}")
                thumbnail_urls.append(original_url)
                continue

            # 确保目录存在
            thumb_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存缩略图
            thumb_path.write_bytes(thumb_bytes)

            # 获取缩略图URL
            thumb_url = path_to_url(thumb_path, cos_mount_path)
            thumbnail_urls.append(thumb_url)
            success_count += 1

            logger.info(f"生成缩略图: {original_url} -> {thumb_url}")

        # 更新数据库
        if thumbnail_urls:
            item.generated_image_thumbnails_json = thumbnail_urls
            await db.commit()
            logger.info(f"更新数据库: item_id={item.id}, thumbnails={len(thumbnail_urls)}")
            return True

        return False

    except Exception as e:
        logger.error(f"处理生成项失败: item_id={item.id}, error={e}")
        await db.rollback()
        return False


async def main():
    """
    主函数：为所有现有图片生成缩略图
    """
    settings = get_settings()
    cos_mount_path = Path(settings.cos_mount_path)

    if not cos_mount_path.exists():
        logger.error(f"COS挂载路径不存在: {cos_mount_path}")
        sys.exit(1)

    logger.info(f"COS挂载路径: {cos_mount_path}")
    logger.info(f"COS Bucket: {settings.cos_bucket}")
    logger.info(f"COS Region: {settings.cos_region}")

    async with aiohttp.ClientSession() as http_session:
        async with async_session_maker() as db:
            # 查询所有有图片但没有缩略图的生成项
            query = select(GenerationItem).where(
                and_(
                    GenerationItem.generated_image_urls_json.isnot(None),
                    GenerationItem.generated_image_thumbnails_json.is_(None),
                )
            )

            result = await db.execute(query)
            items = result.scalars().all()

            total_count = len(items)
            logger.info(f"找到 {total_count} 个需要处理的项目")

            if total_count == 0:
                logger.info("没有需要处理的项目，退出")
                return

            success_count = 0
            failed_count = 0

            for idx, item in enumerate(items, 1):
                logger.info(f"处理 [{idx}/{total_count}] item_id={item.id}")

                success = await process_item(
                    db, item, http_session, cos_mount_path,
                    thumbnail_size=(300, 300),
                    quality=85,
                )

                if success:
                    success_count += 1
                else:
                    failed_count += 1

            logger.info(f"处理完成: 成功={success_count}, 失败={failed_count}")


if __name__ == "__main__":
    asyncio.run(main())