"""
存储服务 (storage_service.py)

提供文件存储功能，包括：
- 任务生成内容的存储（图片、视频、文案）
- 系统上传资源的存储（素材、模板附件）

目录结构设计：
```
data/cos/
├── Tasks/                              # 任务生成内容
│   └── {owner_admin_id}/              # 创作管理员ID
│       └── {YYYY-MM-DD}/              # 日期（按天归档）
│           └── {task_id}/             # 任务ID
│               └── {item_id}/         # 子任务ID
│                   ├── images/        # 生成的图片
│                   ├── videos/        # 生成的视频
│                   └── text/          # 生成的文案
│
└── Materials/                          # 素材对标库上传资源
│   └── {owner_admin_id}/              # 创作管理员ID
│       ├── images/                     # 图片素材
│       │   └── {material_id}/
│       │       ├── original/           # 原始文件
│       │       └── thumbnails/         # 缩略图
│       ├── videos/                     # 视频素材
│       │   └── {material_id}/
│       │       └── original/
└── Templates/                          # 模板创作库上传资源
    └── {owner_admin_id}/              # 创作管理员ID
        ├── images/                     # 图片素材
        │   └── {material_id}/
        │       ├── original/           # 原始文件
        │       └── thumbnails/         # 缩略图
        ├── videos/                     # 视频创作素材
            └── {material_id}/
                └── original/
```

Author: Claude Code
Date: 2025
"""

import hashlib
import io
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse

import aiohttp

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """内容类型枚举"""

    IMAGE = "images"
    VIDEO = "videos"
    TEXT = "text"


class ResourceType(str, Enum):
    """资源类型枚举"""

    IMAGE = "images"
    VIDEO = "videos"
    TEMPLATE = "templates"


def _is_safe_url(url: str) -> bool:
    """
    验证URL是否安全

    Args:
        url: 待验证的URL

    Returns:
        bool: 是否安全
    """
    try:
        parsed = urlparse(url)
        # 如果已经是本地路径或 data URL，直接通过
        if not parsed.scheme or parsed.scheme in ("data", "file"):
            return True
        # 只允许 http/https 协议
        if parsed.scheme not in ("http", "https"):
            return False
        # 允许 localhost 地址（我们会在之后规范化为本地路径）
        hostname = parsed.hostname or ""
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            return True
        # 不允许访问其他内网地址
        if hostname.startswith("192.168.") or hostname.startswith("10."):
            return False
        if hostname.startswith("172.") and 16 <= int(hostname.split(".")[1]) <= 31:
            return False
        return True
    except Exception:
        return False


def _validate_id(param_id: Optional[int], param_name: str) -> None:
    """
    验证ID参数是否有效

    Args:
        param_id: 待验证的ID
        param_name: 参数名称

    Raises:
        ValueError: 当ID无效时
    """
    if param_id is not None:
        if not isinstance(param_id, int):
            raise ValueError(f"{param_name} must be an integer")
        if param_id <= 0:
            raise ValueError(f"{param_name} must be positive")


def _get_file_extension(url: str, default: str = "bin") -> str:
    """
    从URL或内容类型获取文件扩展名

    Args:
        url: 文件URL
        default: 默认扩展名

    Returns:
        str: 文件扩展名（不含点号）
    """
    try:
        # 从URL路径提取扩展名
        path = unquote(urlparse(url).path)
        if "." in path:
            ext = path.rsplit(".", 1)[-1].lower()
            # 常见图片/视频扩展名白名单
            if ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"):
                return ext
            if ext in ("mp4", "mov", "avi", "mkv", "webm", "flv"):
                return ext
    except Exception:
        pass
    return default


class StorageService:
    """
    存储服务类

    负责文件存储管理：
    - 任务生成内容：图片、视频、文案
    - 系统上传资源：素材、模板附件

    URL 访问策略：
    - 本地访问：返回本地文件路径（用于服务器内部处理）
    - 外部访问：返回 COS 公网 URL（格式：{bucket}.cos.{region}.myqcloud.com）
    """

    # 存储根目录名称
    TASKS_DIR = "Tasks"
    MATERIALS_DIR = "Materials"
    TEMPLATES_DIR = "Templates"

    def __init__(self):
        self.settings = get_settings()
        self.cos_mount_path = Path(self.settings.cos_mount_path)
        self.cos_bucket = self.settings.cos_bucket
        self.cos_region = self.settings.cos_region
        self.cos_path_prefix = (
            self.settings.cos_path_prefix.strip("/")
            if self.settings.cos_path_prefix
            else None
        )
        # 兼容旧配置：如果设置了 cos_url_prefix 则使用，否则自动构建
        self._cos_url_prefix = (
            self.settings.cos_url_prefix.rstrip("/")
            if self.settings.cos_url_prefix
            else None
        )
        # 存储 URL 类型配置："auto"、"local"、"cos"、"ip"
        self.storage_url_type = (
            self.settings.storage_url_type.lower()
            if self.settings.storage_url_type
            else "auto"
        )
        # 服务器公网地址{storage_url_prefix}
        self.storage_url_prefix = (
            self.settings.storage_url_prefix.rstrip("/")
            if self.settings.storage_url_prefix
            else "http://127.0.0.1"
        )

        # 使用COS挂载路径作为唯一存储路径
        self.local_storage_path = self.cos_mount_path

        # 缓存 COS 配置检查结果
        self._cos_configured_cache = None

        # 确保存储目录存在且可写
        try:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            # 测试写入权限
            test_file = self.local_storage_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            logger.error(
                f"[StorageService] Storage path not writable: {self.local_storage_path}, error: {e}"
            )

    def _ensure_cos_mount(self) -> bool:
        """
        确保存储目录可用

        Returns:
            bool: 存储目录是否可用
        """
        try:
            if not self.local_storage_path.exists():
                logger.error(
                    f"[StorageService] Storage path does not exist: {self.local_storage_path}"
                )
                return False

            if not os.access(self.local_storage_path, os.W_OK):
                logger.error(
                    f"[StorageService] Storage path is not writable: {self.local_storage_path}"
                )
                return False

            return True
        except Exception as e:
            logger.error(
                f"[StorageService] Failed to check storage: {e}", exc_info=True
            )
            return False

    @staticmethod
    def normalize_localhost_url(url: str) -> str:
        """
        规范化 localhost URL，将其转换为本地路径

        Args:
            url: 原始 URL

        Returns:
            规范化后的 URL 或本地路径
        """
        if not url or not isinstance(url, str):
            return url

        # 如果已经是本地路径或 data URL，直接返回
        if url.startswith("/") or url.startswith("data:"):
            return url

        try:
            parsed = urlparse(url)
            # 检查是否是 localhost URL
            if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
                # 提取路径部分
                path = unquote(parsed.path)
                # 保持 /cos/ 开头的格式，这样 _download_image 能正确处理
                if path.startswith("/cos/"):
                    return path
                elif path.startswith("/"):
                    return path
        except Exception:
            pass

        return url

    # ==================== 任务生成内容路径管理 ====================

    def _get_task_storage_path(
        self,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        content_type: ContentType,
        date: Optional[str] = None,
    ) -> Path:
        """
        获取任务生成内容的存储路径

        路径结构：Tasks/{owner_admin_id}/{YYYY-MM-DD}/{task_id}/{item_id}/{content_type}/

        Args:
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            content_type: 内容类型（images/videos/text）
            date: 日期字符串（可选，默认今天）

        Returns:
            Path: 存储目录路径
        """
        _validate_id(owner_admin_id, "owner_admin_id")
        _validate_id(task_id, "task_id")
        _validate_id(item_id, "item_id")

        date_str = date or datetime.utcnow().strftime("%Y-%m-%d")

        path = (
            self.cos_mount_path
            / self.TASKS_DIR
            / str(owner_admin_id)
            / date_str
            / str(task_id)
            / str(item_id)
            / content_type.value
        )

        return path

    # ==================== 系统上传资源路径管理 ====================

    def _get_material_storage_path(
        self,
        owner_admin_id: int,
        resource_type: ResourceType,
        resource_id: int,
        sub_dir: str = "original",
        allow_temp: bool = False,
    ) -> Path:
        """
        获取素材对标库（Materials）的存储路径

        路径结构：
        - 图片素材：Materials/{owner_admin_id}/images/{material_id}/original/
        - 视频素材：Materials/{owner_admin_id}/videos/{material_id}/original/

        Args:
            owner_admin_id: 创作管理员ID
            resource_type: 资源类型（IMAGE/VIDEO）
            resource_id: 素材ID，可为0表示临时上传（需设置 allow_temp=True）
            sub_dir: 子目录（original/thumbnails）
            allow_temp: 是否允许临时ID（resource_id=0），临时上传会保存到 images|temp/

        Returns:
            Path: 存储目录路径
        """
        _validate_id(owner_admin_id, "owner_admin_id")
        if not allow_temp:
            _validate_id(resource_id, "resource_id")

        path = (
            self.cos_mount_path
            / self.MATERIALS_DIR
            / str(owner_admin_id)
            / resource_type.value
            / str(resource_id)
        )

        if resource_type != ResourceType.TEMPLATE:
            path = path / sub_dir

        logger.debug(
            f"[StorageService] Material storage path: owner_admin_id={owner_admin_id}, "
            f"resource_type={resource_type.value}, resource_id={resource_id}, "
            f"sub_dir={sub_dir}, path={path}"
        )

        return path

    # ==================== 通用工具方法 ====================

    def _generate_filename(
        self,
        prefix: str = "generated",
        extension: str = "jpg",
        include_timestamp: bool = True,
    ) -> str:
        """
        生成唯一文件名

        Args:
            prefix: 文件名前缀
            extension: 文件扩展名
            include_timestamp: 是否包含时间戳

        Returns:
            str: 唯一文件名
        """
        if include_timestamp:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            random_suffix = hashlib.md5(
                f"{timestamp}_{os.urandom(8)}".encode()
            ).hexdigest()[:8]
            return f"{prefix}_{timestamp}_{random_suffix}.{extension}"
        else:
            random_suffix = hashlib.md5(f"{os.urandom(16)}".encode()).hexdigest()[:12]
            return f"{prefix}_{random_suffix}.{extension}"

    def _is_cos_configured(self) -> bool:
        """
        检查 COS 是否已真正配置（非占位符）

        Returns:
            bool: COS 是否可用
        """
        if self._cos_configured_cache is not None:
            return self._cos_configured_cache

        if self._cos_url_prefix:
            # 检查是否是有效的 URL 前缀（不能以 https://. 开头）
            if self._cos_url_prefix.startswith(
                "https://."
            ) or self._cos_url_prefix.startswith("http://."):
                self._cos_configured_cache = False
                return False
            self._cos_configured_cache = True
            return True

        if not self.cos_bucket or self.cos_bucket.startswith("your-"):
            self._cos_configured_cache = False
            return False

        if not self.cos_region:
            self._cos_configured_cache = False
            return False

        self._cos_configured_cache = True
        return True

    def _get_cos_url_prefix(self) -> str:
        """
        获取 COS 公网 URL 前缀

        格式：https://{bucket}.cos.{region}.myqcloud.com/{path_prefix}

        Returns:
            str: COS URL 前缀
        """
        if self._cos_url_prefix:
            return self._cos_url_prefix

        if not self.cos_bucket or not self.cos_region:
            logger.warning(
                "COS bucket or region not configured, returning empty prefix"
            )
            return ""

        url = f"https://{self.cos_bucket}.cos.{self.cos_region}.myqcloud.com"
        # 注意：path_prefix 不在 URL 构建时添加，避免与文件路径中的前缀重复
        return url

    def _build_full_cos_url(self, relative_path: str) -> str:
        """
        构建完整的 COS URL，避免 path_prefix 重复拼接，并修复已存在的重复

        Args:
            relative_path: 相对存储路径的文件路径

        Returns:
            str: 完整的 COS URL
        """
        base_url = self._get_cos_url_prefix().rstrip("/")
        clean_path = str(relative_path).lstrip("/")

        if not self.cos_path_prefix:
            # 没有配置前缀，直接拼接
            return f"{base_url}/{clean_path}"

        prefix = self.cos_path_prefix.strip("/")
        expected_prefix = prefix + "/"

        # 检查并修复重复的前缀
        final_path = clean_path
        double_prefix = expected_prefix + prefix + "/"
        if final_path.startswith(double_prefix):
            # 发现重复前缀，移除重复部分
            logger.info(
                f"[StorageService] Found duplicate prefix, fixing: {relative_path}"
            )
            final_path = final_path[len(expected_prefix) :]
        elif final_path.startswith(expected_prefix):
            # 只有一个前缀，保持不变
            logger.info(
                f"[StorageService] Path already contains prefix: {relative_path}"
            )
        else:
            # 路径不包含前缀，正常添加
            final_path = f"{prefix}/{final_path}"

        return f"{base_url}/{final_path}"

    def _path_to_url(self, file_path: Path, external: bool = True) -> str:
        """
        将本地文件路径转换为 URL

        Args:
            file_path: 本地文件路径
            external: 是否返回外部访问 URL
                - True（默认）：根据 storage_url_type 配置返回对应类型的 URL
                - False：返回本地路径，供服务器内部使用

        Returns:
            str: 访问 URL
        """
        try:
            relative_path = file_path.relative_to(self.local_storage_path)
        except ValueError as e:
            logger.error(
                f"[StorageService] Cannot compute relative path: file_path={file_path}, "
                f"storage_path={self.local_storage_path}, error={e}"
            )
            return str(file_path)

        if not external:
            return str(file_path)

        # 根据配置返回对应类型的 URL
        if self.storage_url_type == "local":
            return f"/cos/{relative_path}"
        elif self.storage_url_type == "cos":
            if self._is_cos_configured():
                return self._build_full_cos_url(str(relative_path))
            else:
                if self.storage_url_prefix:
                    return f"{self.storage_url_prefix}/cos/{relative_path}"
                else:
                    return f"/cos/{relative_path}"
        elif self.storage_url_type == "ip":
            if self.storage_url_prefix:
                return f"{self.storage_url_prefix}/cos/{relative_path}"
            else:
                return f"/cos/{relative_path}"
        else:  # "auto" or other values
            if self._is_cos_configured():
                return self._build_full_cos_url(str(relative_path))
            elif self.storage_url_prefix:
                return f"{self.storage_url_prefix}/cos/{relative_path}"
            else:
                return f"/cos/{relative_path}"

    def convert_url(self, url: str) -> str:
        """
        将本地路径转换为对应类型的 URL（根据 storage_url_type 配置）

        Args:
            url: 原始 URL，可能是本地路径或 COS URL

        Returns:
            str: 转换后的 URL
        """
        if not url:
            return url

        # 安全检查：如果 URL 包含 localhost/127.0.0.1，强行替换
        if (
            url.startswith("http://localhost")
            or url.startswith("https://localhost")
            or url.startswith("http://127.0.0.1")
            or url.startswith("https://127.0.0.1")
        ):
            parsed = urlparse(url)
            path = parsed.path
            if path.startswith("/cos/"):
                relative_path = path[5:]
                # 优先尝试 COS
                if self._is_cos_configured() and self.storage_url_type in [
                    "auto",
                    "cos",
                ]:
                    return self._build_full_cos_url(relative_path)
                # 否则使用配置的 storage_url_prefix
                if self.storage_url_prefix:
                    return f"{self.storage_url_prefix}/cos/{relative_path}"

        # 检查是否是旧的 IP URL（需要重新处理）
        if url.startswith("http://") or url.startswith("https://"):
            # 检查是否是我们自己生成的 IP URL（包含 /cos/ 路径）
            parsed = urlparse(url)
            path = parsed.path

            # 如果路径以 /cos/ 开头，说明这是我们之前生成的 IP URL
            if path.startswith("/cos/"):
                # 提取相对路径，重新处理
                relative_path = path[5:]  # 去掉 /cos/

                # 先修复相对路径中的重复前缀
                if self.cos_path_prefix:
                    prefix = self.cos_path_prefix.strip("/")
                    expected_prefix = prefix + "/"
                    double_prefix = expected_prefix + prefix + "/"
                    if relative_path.startswith(double_prefix):
                        relative_path = relative_path[len(expected_prefix) :]

                # 按照新的配置重新生成 URL
                if self.storage_url_type == "local":
                    return f"/cos/{relative_path}"
                elif self.storage_url_type == "cos":
                    if self._is_cos_configured():
                        return self._build_full_cos_url(relative_path)
                elif self.storage_url_type == "ip":
                    if self.storage_url_prefix:
                        return f"{self.storage_url_prefix}/cos/{relative_path}"
                else:  # "auto"
                    if self._is_cos_configured():
                        return self._build_full_cos_url(relative_path)
                    elif self.storage_url_prefix:
                        return f"{self.storage_url_prefix}/cos/{relative_path}"

            # 如果配置为强制使用 local，但不是我们的 IP URL 格式，尝试正常转换
            if self.storage_url_type == "local":
                # 检查是否是 COS URL
                if self._is_cos_configured():
                    cos_prefix = self._get_cos_url_prefix()
                    if url.startswith(cos_prefix):
                        # 转换 COS URL 回本地路径
                        relative_path = url[len(cos_prefix) :].lstrip("/")
                        local_url = f"/cos/{relative_path}"
                        logger.info(
                            f"[StorageService] Converting COS URL to local: {url} -> {local_url}"
                        )
                        return local_url
                # 检查是否是 IP URL
                if self.storage_url_prefix and url.startswith(self.storage_url_prefix):
                    relative_path = url[len(self.storage_url_prefix) :].lstrip("/")
                    if relative_path.startswith("cos/"):
                        relative_path = relative_path[4:]  # 去掉 cos/
                        local_url = f"/cos/{relative_path}"
                        logger.info(
                            f"[StorageService] Converting IP URL to local: {url} -> {local_url}"
                        )
                        return local_url

            # 其他情况，检查是否是 COS URL 且配置了新的 URL 类型
            if self._is_cos_configured():
                cos_prefix = self._get_cos_url_prefix()
                # 如果已经是 COS URL 且配置没有变，直接返回
                if url.startswith(cos_prefix):
                    return url
                # 如果配置要求使用 COS URL，但当前是 IP URL，需要转换
                if self.storage_url_type in ["cos", "auto"]:
                    # 尝试提取相对路径
                    if path.startswith("/cos/"):
                        relative_path = path[5:]
                        return self._build_full_cos_url(relative_path)

            # 其他情况直接返回
            return url

        # 如果是本地 /cos/... 路径
        if url.startswith("/cos/"):
            # 提取相对路径
            relative_path = url[5:]  # 去掉 /cos/

            # 先修复相对路径中的重复前缀
            if self.cos_path_prefix:
                prefix = self.cos_path_prefix.strip("/")
                expected_prefix = prefix + "/"
                double_prefix = expected_prefix + prefix + "/"
                if relative_path.startswith(double_prefix):
                    relative_path = relative_path[len(expected_prefix) :]

            # 根据配置决定是否转换
            if self.storage_url_type == "local":
                return f"/cos/{relative_path}"
            elif self.storage_url_type == "cos":
                if self._is_cos_configured():
                    return self._build_full_cos_url(relative_path)
            elif self.storage_url_type == "ip":
                if self.storage_url_prefix:
                    return f"{self.storage_url_prefix}/cos/{relative_path}"
            else:  # "auto"
                if self._is_cos_configured():
                    return self._build_full_cos_url(relative_path)
                elif self.storage_url_prefix:
                    return f"{self.storage_url_prefix}/cos/{relative_path}"

        return url

    def _path_to_external_url(self, file_path: Path) -> str:
        """
        将本地文件路径转换为外部访问 URL（COS 公网 URL）

        这是 _path_to_url(file_path, external=True) 的快捷方法

        Args:
            file_path: 本地文件路径

        Returns:
            str: COS 公网 URL
        """
        return self._path_to_url(file_path, external=True)

    # ==================== 任务生成内容存储 ====================

    async def save_generated_image(
        self,
        image_url: str,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> Optional[str]:
        """
        从URL下载图片并保存到COS（任务生成）

        Args:
            image_url: 源图片URL
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串（可选）

        Returns:
            Optional[str]: 保存后的公网URL，失败返回None
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None

        if not _is_safe_url(image_url):
            logger.error(f"Unsafe URL rejected: {image_url}")
            return None

        try:
            # 获取存储目录
            storage_path = self._get_task_storage_path(
                owner_admin_id, task_id, item_id, ContentType.IMAGE, date
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            extension = _get_file_extension(image_url, "jpg")
            filename = self._generate_filename(prefix="img", extension=extension)
            file_path = storage_path / filename

            # 下载/复制图片（支持 HTTP URL 和本地文件路径）
            parsed = urlparse(image_url)
            if not parsed.scheme or parsed.scheme == "file":
                # 本地文件路径：直接读取文件内容
                local_path = (
                    Path(image_url) if not parsed.scheme else Path(unquote(parsed.path))
                )
                if not local_path.exists():
                    raise FileNotFoundError(f"Local file not found: {local_path}")
                content = local_path.read_bytes()
                logger.info(f"Read local file: {local_path} ({len(content)} bytes)")
            else:
                # HTTP(S) URL：下载
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url, timeout=60) as response:
                        response.raise_for_status()
                        content = await response.read()

            # 保存文件到 COS
            file_path.write_bytes(content)

            # 返回公网URL
            public_url = self._path_to_url(file_path)
            logger.info(f"Saved generated image: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save image from {image_url}: {e}")
            return None

    async def save_generated_images(
        self,
        image_urls: List[str],
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> List[str]:
        """
        批量保存生成的图片

        Args:
            image_urls: 源图片URL列表
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串

        Returns:
            List[str]: 保存后的公网URL列表（保存失败使用原URL）
        """
        results = []
        for url in image_urls:
            saved_url = await self.save_generated_image(
                url, owner_admin_id, task_id, item_id, date
            )
            results.append(saved_url or url)
        return results

    async def save_generated_image_with_thumbnail(
        self,
        image_url: str,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
        thumbnail_size: Tuple[int, int] = (300, 300),
        thumbnail_quality: int = 85,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        从URL下载图片并保存到COS，同时生成缩略图

        Args:
            image_url: 源图片URL
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串（可选）
            thumbnail_size: 缩略图最大尺寸 (width, height)
            thumbnail_quality: 缩略图质量（1-100）

        Returns:
            Tuple[Optional[str], Optional[str]]: (原图URL, 缩略图URL)
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None, None

        if not _is_safe_url(image_url):
            logger.error(f"Unsafe URL rejected: {image_url}")
            return None, None

        try:
            from PIL import Image

            # 获取存储目录
            storage_path = self._get_task_storage_path(
                owner_admin_id, task_id, item_id, ContentType.IMAGE, date
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            extension = _get_file_extension(image_url, "jpg")
            filename = self._generate_filename(prefix="img", extension=extension)
            file_path = storage_path / filename

            # 下载图片（支持 HTTP URL 和本地文件路径）
            parsed = urlparse(image_url)
            if not parsed.scheme or parsed.scheme == "file":
                # 本地文件路径：直接读取文件内容
                local_path = (
                    Path(image_url) if not parsed.scheme else Path(unquote(parsed.path))
                )
                if not local_path.exists():
                    raise FileNotFoundError(f"Local file not found: {local_path}")
                content = local_path.read_bytes()
                logger.info(f"Read local file: {local_path} ({len(content)} bytes)")
            else:
                # HTTP(S) URL：下载
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url, timeout=60) as response:
                        response.raise_for_status()
                        content = await response.read()

            # 保存原图
            file_path.write_bytes(content)
            public_url = self._path_to_url(file_path)
            logger.info(f"Saved generated image: {public_url}")

            # 生成缩略图
            thumbnail_url = None
            try:
                image = Image.open(io.BytesIO(content))

                # 转换为 RGB（处理 RGBA 等模式）
                if image.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    if image.mode in ("RGBA", "LA"):
                        background.paste(
                            image,
                            mask=(
                                image.split()[-1]
                                if image.mode in ("RGBA", "LA")
                                else None
                            ),
                        )
                        image = background
                    else:
                        image = image.convert("RGB")

                # 等比例缩放
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"

                # 缩略图保存到 thumbnails 子目录
                thumbnail_path = storage_path / "thumbnails"
                thumbnail_path.mkdir(parents=True, exist_ok=True)
                thumbnail_file_path = thumbnail_path / thumb_filename

                # 保存为 JPEG
                image.save(
                    thumbnail_file_path,
                    "JPEG",
                    quality=thumbnail_quality,
                    optimize=True,
                )
                thumbnail_url = self._path_to_url(thumbnail_file_path)

                logger.info(
                    f"[StorageService] Generated thumbnail: {thumbnail_file_path} -> {thumbnail_url}"
                )

            except Exception as e:
                logger.warning(
                    f"[StorageService] Failed to generate thumbnail: {e}", exc_info=True
                )
                # 缩略图生成失败不影响原图保存

            return public_url, thumbnail_url

        except Exception as e:
            logger.error(f"Failed to save image from {image_url}: {e}")
            return None, None

    async def save_generated_images_with_thumbnails(
        self,
        image_urls: List[str],
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        批量保存生成的图片并生成缩略图

        Args:
            image_urls: 源图片URL列表
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串

        Returns:
            Tuple[List[str], List[str]]: (原图URL列表, 缩略图URL列表)
        """
        original_urls = []
        thumbnail_urls = []

        for url in image_urls:
            original_url, thumbnail_url = (
                await self.save_generated_image_with_thumbnail(
                    url, owner_admin_id, task_id, item_id, date
                )
            )
            original_urls.append(original_url or url)
            thumbnail_urls.append(thumbnail_url or url)  # 缩略图失败时使用原图

        return original_urls, thumbnail_urls

    async def save_base64_image_with_thumbnail(
        self,
        base64_data: str,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
        thumbnail_size: Tuple[int, int] = (300, 300),
        thumbnail_quality: int = 85,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        从 Base64 数据保存图片到COS，同时生成缩略图

        Args:
            base64_data: Base64 编码的图片数据（可带或不带 data:image/xxx;base64, 前缀）
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串（可选）
            thumbnail_size: 缩略图最大尺寸 (width, height)
            thumbnail_quality: 缩略图质量（1-100）

        Returns:
            Tuple[Optional[str], Optional[str]]: (原图URL, 缩略图URL)
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None, None

        try:
            import base64

            from PIL import Image

            # 去除 data:image/xxx;base64, 前缀（如果存在）
            if ";base64," in base64_data:
                pure_base64 = base64_data.split(";base64,")[1]
            else:
                pure_base64 = base64_data

            # 解码 Base64
            img_bytes = base64.b64decode(pure_base64)
            logger.info(
                f"[StorageService] Base64 解码完成 | size={len(img_bytes)} bytes"
            )

            # 获取存储目录
            storage_path = self._get_task_storage_path(
                owner_admin_id, task_id, item_id, ContentType.IMAGE, date
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            filename = self._generate_filename(prefix="img", extension="png")
            file_path = storage_path / filename

            # 保存原图
            file_path.write_bytes(img_bytes)
            public_url = self._path_to_url(file_path)
            logger.info(f"[StorageService] Saved base64 image: {public_url}")

            # 生成缩略图
            thumbnail_url = None
            try:
                image = Image.open(io.BytesIO(img_bytes))

                # 转换为 RGB（处理 RGBA 等模式）
                if image.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    if image.mode in ("RGBA", "LA"):
                        background.paste(
                            image,
                            mask=(
                                image.split()[-1]
                                if image.mode in ("RGBA", "LA")
                                else None
                            ),
                        )
                        image = background
                    else:
                        image = image.convert("RGB")

                # 等比例缩放
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"

                # 缩略图保存到 thumbnails 子目录
                thumbnail_path = storage_path / "thumbnails"
                thumbnail_path.mkdir(parents=True, exist_ok=True)
                thumbnail_file_path = thumbnail_path / thumb_filename

                # 保存为 JPEG
                image.save(
                    thumbnail_file_path,
                    "JPEG",
                    quality=thumbnail_quality,
                    optimize=True,
                )
                thumbnail_url = self._path_to_url(thumbnail_file_path)

                logger.info(
                    f"[StorageService] Generated thumbnail: {thumbnail_file_path} -> {thumbnail_url}"
                )

            except Exception as e:
                logger.warning(
                    f"[StorageService] Failed to generate thumbnail: {e}", exc_info=True
                )
                # 缩略图生成失败不影响原图保存

            return public_url, thumbnail_url

        except Exception as e:
            logger.error(f"Failed to save base64 image: {e}")
            return None, None

    async def save_base64_images_with_thumbnails(
        self,
        base64_list: List[str],
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        批量保存 Base64 编码的图片并生成缩略图

        Args:
            base64_list: Base64 编码的图片列表
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串

        Returns:
            Tuple[List[str], List[str]]: (原图URL列表, 缩略图URL列表)
        """
        original_urls = []
        thumbnail_urls = []

        for base64_data in base64_list:
            original_url, thumbnail_url = await self.save_base64_image_with_thumbnail(
                base64_data, owner_admin_id, task_id, item_id, date
            )
            if original_url:
                original_urls.append(original_url)
                thumbnail_urls.append(
                    thumbnail_url or original_url
                )  # 缩略图失败时使用原图

        return original_urls, thumbnail_urls

    async def save_generated_video(
        self,
        video_url: str,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> Optional[str]:
        """
        从URL下载视频并保存到COS（任务生成）

        Args:
            video_url: 源视频URL
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串

        Returns:
            Optional[str]: 保存后的公网URL，失败返回None
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None

        if not _is_safe_url(video_url):
            logger.error(f"Unsafe URL rejected: {video_url}")
            return None

        try:
            # 获取存储目录
            storage_path = self._get_task_storage_path(
                owner_admin_id, task_id, item_id, ContentType.VIDEO, date
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            extension = _get_file_extension(video_url, "mp4")
            filename = self._generate_filename(prefix="video", extension=extension)
            file_path = storage_path / filename

            # 下载视频
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, timeout=300) as response:
                    response.raise_for_status()
                    content = await response.read()

            # 保存文件
            file_path.write_bytes(content)

            # 返回公网URL
            public_url = self._path_to_url(file_path)
            logger.info(f"Saved generated video: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save video from {video_url}: {e}")
            return None

    async def save_generated_text(
        self,
        content: str,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        filename: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Optional[str]:
        """
        保存生成的文案到COS

        Args:
            content: 文案内容
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            filename: 自定义文件名（可选）
            date: 日期字符串

        Returns:
            Optional[str]: 保存后的公网URL，失败返回None
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None

        try:
            # 获取存储目录
            storage_path = self._get_task_storage_path(
                owner_admin_id, task_id, item_id, ContentType.TEXT, date
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if not filename:
                filename = self._generate_filename(prefix="content", extension="txt")
            elif not filename.endswith(".txt"):
                filename = f"{filename}.txt"

            file_path = storage_path / filename

            # 保存文案
            file_path.write_text(content, encoding="utf-8")

            # 返回公网URL
            public_url = self._path_to_url(file_path)
            logger.info(f"Saved generated text: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save text: {e}")
            return None

    # ==================== 系统上传资源存储 ====================

    async def save_material_image(
        self,
        file_content: bytes,
        owner_admin_id: int,
        material_id: int,
        filename: Optional[str] = None,
        extension: str = "jpg",
    ) -> Optional[str]:
        """
        保存图片素材

        Args:
            file_content: 文件内容
            owner_admin_id: 创作管理员ID
            material_id: 素材ID
            filename: 自定义文件名
            extension: 文件扩展名

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            logger.error("COS mount is not available")
            return None

        try:
            # 获取存储目录
            storage_path = self._get_material_storage_path(
                owner_admin_id, ResourceType.IMAGE, material_id, "original"
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            if not filename:
                filename = self._generate_filename(
                    prefix="material", extension=extension
                )

            file_path = storage_path / filename

            # 保存文件
            file_path.write_bytes(file_content)

            public_url = self._path_to_url(file_path)
            logger.info(f"Saved material image: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save material image: {e}")
            return None

    async def save_material_thumbnail(
        self,
        file_content: bytes,
        owner_admin_id: int,
        material_id: int,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        保存素材缩略图

        Args:
            file_content: 文件内容
            owner_admin_id: 创作管理员ID
            material_id: 素材ID
            filename: 自定义文件名

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            return None

        try:
            storage_path = self._get_material_storage_path(
                owner_admin_id, ResourceType.IMAGE, material_id, "thumbnails"
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            if not filename:
                filename = self._generate_filename(prefix="thumb", extension="jpg")

            file_path = storage_path / filename
            file_path.write_bytes(file_content)

            return self._path_to_url(file_path)

        except Exception as e:
            logger.error(f"Failed to save thumbnail: {e}")
            return None

    async def save_material_image_with_thumbnail(
        self,
        file_content: bytes,
        owner_admin_id: int,
        material_id: int,
        filename: Optional[str] = None,
        extension: str = "jpg",
        max_size: int = 20 * 1024 * 1024,  # 20MB
        thumbnail_size: Tuple[int, int] = (300, 300),
        thumbnail_quality: int = 85,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        保存图片素材并生成缩略图

        Args:
            file_content: 文件内容（图片二进制数据）
            owner_admin_id: 创作管理员ID
            material_id: 素材ID
            filename: 自定义文件名（不含扩展名）
            extension: 文件扩展名
            max_size: 最大文件大小（字节）
            thumbnail_size: 缩略图最大尺寸 (width, height)
            thumbnail_quality: 缩略图质量（1-100）

        Returns:
            Tuple[Optional[str], Optional[str]]: (原图URL, 缩略图URL)
        """
        logger.info(
            f"[StorageService] Starting save_material_image_with_thumbnail: "
            f"owner_admin_id={owner_admin_id}, material_id={material_id}, "
            f"file_content_size={len(file_content)}, filename={filename}, extension={extension}"
        )

        if not self._ensure_cos_mount():
            logger.error(
                f"[StorageService] COS mount check failed, cannot save image for material_id={material_id}"
            )
            return None, None

        # 检查文件大小
        if len(file_content) > max_size:
            logger.error(
                f"[StorageService] File size exceeds limit: {len(file_content)} > {max_size}"
            )
            return None, None

        try:
            from PIL import Image

            # 生成文件名
            if not filename:
                filename = self._generate_filename(
                    prefix="material", extension=extension
                )
                logger.debug(f"[StorageService] Generated filename: {filename}")
            else:
                # 确保扩展名正确
                if not filename.lower().endswith(
                    (".", "jpg", "jpeg", "png", "gif", "webp")
                ):
                    filename = f"{filename}.{extension}"
                logger.debug(f"[StorageService] Using provided filename: {filename}")

            # 保存原图
            original_path = self._get_material_storage_path(
                owner_admin_id, ResourceType.IMAGE, material_id, "original"
            )
            logger.debug(f"[StorageService] Original path: {original_path}")

            original_path.mkdir(parents=True, exist_ok=True)
            logger.debug(
                f"[StorageService] Created directory (if needed): {original_path}"
            )

            original_file_path = original_path / filename
            original_file_path.write_bytes(file_content)
            logger.info(
                f"[StorageService] Saved original file: {original_file_path}, size={len(file_content)}"
            )

            original_url = self._path_to_url(original_file_path)
            logger.info(f"[StorageService] Generated original URL: {original_url}")

            # 验证文件是否真正写入
            if original_file_path.exists():
                actual_size = original_file_path.stat().st_size
                logger.info(
                    f"[StorageService] Verified file exists: {original_file_path}, actual_size={actual_size}"
                )
            else:
                logger.error(
                    f"[StorageService] File was not created: {original_file_path}"
                )

            # 生成缩略图
            thumbnail_url = None
            try:
                image = Image.open(io.BytesIO(file_content))
                logger.debug(
                    f"[StorageService] Opened image for thumbnail: mode={image.mode}, size={image.size}"
                )

                # 转换为 RGB（处理 RGBA 等模式）
                if image.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    if image.mode in ("RGBA", "LA"):
                        background.paste(
                            image,
                            mask=(
                                image.split()[-1]
                                if image.mode in ("RGBA", "LA")
                                else None
                            ),
                        )
                        image = background
                    else:
                        image = image.convert("RGB")

                # 等比例缩放
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"

                # 保存缩略图
                thumbnail_path = self._get_material_storage_path(
                    owner_admin_id, ResourceType.IMAGE, material_id, "thumbnails"
                )
                thumbnail_path.mkdir(parents=True, exist_ok=True)
                thumbnail_file_path = thumbnail_path / thumb_filename

                # 保存为 JPEG
                image.save(
                    thumbnail_file_path,
                    "JPEG",
                    quality=thumbnail_quality,
                    optimize=True,
                )
                thumbnail_url = self._path_to_url(thumbnail_file_path)

                logger.info(
                    f"[StorageService] Generated thumbnail: {thumbnail_file_path} -> {thumbnail_url}"
                )

            except Exception as e:
                logger.warning(
                    f"[StorageService] Failed to generate thumbnail: {e}", exc_info=True
                )
                # 缩略图生成失败不影响原图保存

            logger.info(
                f"[StorageService] Completed save_material_image_with_thumbnail: "
                f"original_url={original_url}, thumbnail_url={thumbnail_url}"
            )
            return original_url, thumbnail_url

        except Exception as e:
            logger.error(
                f"[StorageService] Failed to save material image: {e}", exc_info=True
            )
            return None, None

    async def save_template_image_with_thumbnail(
        self,
        file_content: bytes,
        owner_admin_id: int,
        template_id: int,
        filename: Optional[str] = None,
        extension: str = "jpg",
        max_size: int = 20 * 1024 * 1024,  # 20MB
        thumbnail_size: Tuple[int, int] = (300, 300),
        thumbnail_quality: int = 85,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        保存模板图片并生成缩略图（参考素材对标库实现）

        Args:
            file_content: 文件内容（图片二进制数据）
            owner_admin_id: 创作管理员ID
            template_id: 模板ID
            filename: 自定义文件名（不含扩展名）
            extension: 文件扩展名
            max_size: 最大文件大小（字节）
            thumbnail_size: 缩略图最大尺寸 (width, height)
            thumbnail_quality: 缩略图质量（1-100）

        Returns:
            Tuple[Optional[str], Optional[str]]: (原图URL, 缩略图URL)
        """
        logger.info(
            f"[StorageService] Starting save_template_image_with_thumbnail: "
            f"owner_admin_id={owner_admin_id}, template_id={template_id}, "
            f"file_content_size={len(file_content)}, filename={filename}, extension={extension}"
        )

        if not self._ensure_cos_mount():
            logger.error(
                f"[StorageService] COS mount check failed, cannot save image for template_id={template_id}"
            )
            return None, None

        # 检查文件大小
        if len(file_content) > max_size:
            logger.error(
                f"[StorageService] File size exceeds limit: {len(file_content)} > {max_size}"
            )
            return None, None

        try:
            from PIL import Image

            # 生成文件名
            if not filename:
                filename = self._generate_filename(
                    prefix="template", extension=extension
                )
                logger.debug(f"[StorageService] Generated filename: {filename}")
            else:
                # 确保扩展名正确
                if not filename.lower().endswith(
                    (".", "jpg", "jpeg", "png", "gif", "webp")
                ):
                    filename = f"{filename}.{extension}"
                logger.debug(f"[StorageService] Using provided filename: {filename}")

            # 保存原图：Templates/{owner_admin_id}/images/{template_id}/original/
            storage_path = (
                self.local_storage_path
                / self.TEMPLATES_DIR
                / str(owner_admin_id)
                / ResourceType.IMAGE.value
                / str(template_id)
                / "original"
            )
            logger.debug(f"[StorageService] Original storage path: {storage_path}")

            storage_path.mkdir(parents=True, exist_ok=True)
            original_file_path = storage_path / filename
            original_file_path.write_bytes(file_content)
            logger.info(
                f"[StorageService] Saved original file: {original_file_path}, size={len(file_content)}"
            )

            original_url = self._path_to_url(original_file_path)
            logger.info(f"[StorageService] Generated original URL: {original_url}")

            # 生成缩略图
            thumbnail_url = None
            try:
                image = Image.open(io.BytesIO(file_content))
                logger.debug(
                    f"[StorageService] Opened image for thumbnail: mode={image.mode}, size={image.size}"
                )

                # 转换为 RGB（处理 RGBA 等模式）
                if image.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    if image.mode in ("RGBA", "LA"):
                        background.paste(
                            image,
                            mask=(
                                image.split()[-1]
                                if image.mode in ("RGBA", "LA")
                                else None
                            ),
                        )
                        image = background
                    else:
                        image = image.convert("RGB")

                # 等比例缩放
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # 生成缩略图文件名
                thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"

                # 保存缩略图：Templates/{owner_admin_id}/images/{template_id}/thumbnails/
                thumbnail_path = (
                    self.local_storage_path
                    / self.TEMPLATES_DIR
                    / str(owner_admin_id)
                    / ResourceType.IMAGE.value
                    / str(template_id)
                    / "thumbnails"
                )
                thumbnail_path.mkdir(parents=True, exist_ok=True)
                thumbnail_file_path = thumbnail_path / thumb_filename

                # 保存为 JPEG
                image.save(
                    thumbnail_file_path,
                    "JPEG",
                    quality=thumbnail_quality,
                    optimize=True,
                )
                thumbnail_url = self._path_to_url(thumbnail_file_path)

                logger.info(
                    f"[StorageService] Generated thumbnail: {thumbnail_file_path} -> {thumbnail_url}"
                )

            except Exception as e:
                logger.warning(
                    f"[StorageService] Failed to generate thumbnail: {e}", exc_info=True
                )
                # 缩略图生成失败不影响原图保存

            logger.info(
                f"[StorageService] Completed save_template_image_with_thumbnail: "
                f"original_url={original_url}, thumbnail_url={thumbnail_url}"
            )
            return original_url, thumbnail_url

        except Exception as e:
            logger.error(
                f"[StorageService] Failed to save template image: {e}", exc_info=True
            )
            return None, None

    async def save_template_video(
        self,
        file_content: bytes,
        owner_admin_id: int,
        template_id: int,
        filename: Optional[str] = None,
        extension: str = "mp4",
    ) -> Optional[str]:
        """
        保存模板视频（参考素材对标库实现）

        Args:
            file_content: 文件内容
            owner_admin_id: 创作管理员ID
            template_id: 模板ID
            filename: 自定义文件名
            extension: 文件扩展名

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            return None

        try:
            # 保存路径：Templates/{owner_admin_id}/videos/{template_id}/original/
            storage_path = (
                self.local_storage_path
                / self.TEMPLATES_DIR
                / str(owner_admin_id)
                / ResourceType.VIDEO.value
                / str(template_id)
                / "original"
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            if not filename:
                filename = self._generate_filename(prefix="video", extension=extension)

            file_path = storage_path / filename
            file_path.write_bytes(file_content)

            public_url = self._path_to_url(file_path)
            logger.info(f"Saved template video: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save template video: {e}")
            return None

    async def save_material_video(
        self,
        file_content: bytes,
        owner_admin_id: int,
        material_id: int,
        filename: Optional[str] = None,
        extension: str = "mp4",
    ) -> Optional[str]:
        """
        保存视频素材

        Args:
            file_content: 文件内容
            owner_admin_id: 创作管理员ID
            material_id: 素材ID
            filename: 自定义文件名
            extension: 文件扩展名

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            return None

        try:
            storage_path = self._get_material_storage_path(
                owner_admin_id, ResourceType.VIDEO, material_id, "original"
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            if not filename:
                filename = self._generate_filename(prefix="video", extension=extension)

            file_path = storage_path / filename
            file_path.write_bytes(file_content)

            public_url = self._path_to_url(file_path)
            logger.info(f"Saved material video: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save material video: {e}")
            return None

    async def save_template_attachment(
        self,
        file_content: bytes,
        owner_admin_id: int,
        template_id: int,
        filename: str,
        content_type: ContentType = ContentType.IMAGE,
        sub_dir: str = "original",
    ) -> Optional[str]:
        """
        保存模板创作库文件（图片/视频），包括original、thumbnails等

        路径结构（参考素材对标库）：
        - 图片：Templates/{owner_admin_id}/images/{template_id}/original/
        - 视频：Templates/{owner_admin_id}/videos/{template_id}/original/

        Args:
            file_content: 文件内容
            owner_admin_id: 创作管理员ID
            template_id: 模板ID
            filename: 文件名
            content_type: 内容类型（IMAGE/VIDEO），用于区分目录
            sub_dir: 子目录（original/thumbnails）

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            return None

        try:
            # 正式保存：Templates/{owner_admin_id}/{images|videos}/{template_id}/original/
            _validate_id(template_id, "template_id")
            storage_path = (
                self.local_storage_path
                / self.TEMPLATES_DIR
                / str(owner_admin_id)
                / content_type.value
                / str(template_id)
                / sub_dir
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            file_path = storage_path / filename
            file_path.write_bytes(file_content)

            public_url = self._path_to_url(file_path)
            logger.info(f"Saved template material: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to save template material: {e}")
            return None

    def delete_template_attachments(
        self,
        owner_admin_id: int,
        template_id: int,
    ) -> bool:
        """
        删除模板的所有物理文件（包含 original、thumbnails 等子目录）

        Args:
            owner_admin_id: 创作管理员ID
            template_id: 模板ID

        Returns:
            bool: 是否删除成功
        """
        try:
            # 删除图片目录
            image_path = (
                self.local_storage_path
                / self.TEMPLATES_DIR
                / str(owner_admin_id)
                / ResourceType.IMAGE.value
                / str(template_id)
            )

            # 删除视频目录
            video_path = (
                self.local_storage_path
                / self.TEMPLATES_DIR
                / str(owner_admin_id)
                / ResourceType.VIDEO.value
                / str(template_id)
            )

            success = True
            for path in [image_path, video_path]:
                if path.exists():
                    import shutil

                    shutil.rmtree(path)
                    logger.info(f"[StorageService] Deleted template directory: {path}")
                else:
                    logger.warning(
                        f"[StorageService] Template directory does not exist: {path}"
                    )

            return success

        except Exception as e:
            logger.error(
                f"[StorageService] Failed to delete template directory: {e}",
                exc_info=True,
            )
            return False

    async def download_and_save_material(
        self,
        source_url: str,
        owner_admin_id: int,
        resource_type: ResourceType,
        resource_id: int,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        从URL下载并保存为系统资源

        Args:
            source_url: 源URL
            owner_admin_id: 创作管理员ID
            resource_type: 资源类型
            resource_id: 资源ID
            filename: 自定义文件名

        Returns:
            Optional[str]: 保存后的公网URL
        """
        if not self._ensure_cos_mount():
            return None

        if not _is_safe_url(source_url):
            logger.error(f"Unsafe URL rejected: {source_url}")
            return None

        try:
            # 确定存储子目录
            sub_dir = "original" if resource_type != ResourceType.TEMPLATE else ""

            # 获取存储目录
            storage_path = self._get_material_storage_path(
                owner_admin_id, resource_type, resource_id, sub_dir
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            # 确定文件名和扩展名
            extension = _get_file_extension(source_url, "bin")
            if resource_type == ResourceType.VIDEO:
                extension = _get_file_extension(source_url, "mp4")
            elif resource_type == ResourceType.IMAGE:
                extension = _get_file_extension(source_url, "jpg")

            if not filename:
                filename = self._generate_filename(
                    prefix="resource", extension=extension
                )

            file_path = storage_path / filename

            # 下载文件
            timeout = 300 if resource_type == ResourceType.VIDEO else 60
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=timeout) as response:
                    response.raise_for_status()
                    content = await response.read()

            # 保存文件
            file_path.write_bytes(content)

            public_url = self._path_to_url(file_path)
            logger.info(f"Downloaded and saved resource: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to download and save from {source_url}: {e}")
            return None

    # ==================== 图片处理 ====================

    async def process_reference_image(
        self,
        image_url: str,
        max_dimension: int = 2048,
        max_size_bytes: int = 15 * 1024 * 1024,  # 15MB
        prefer_url: bool = False,
        no_compression: bool = False,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        处理参考图片：下载、缩放、确保文件大小限制

        Args:
            image_url: 图片URL（可以是相对路径或公网URL）
            max_dimension: 最大边长（宽或高超过此值则等比例缩放）
            max_size_bytes: 最大文件大小（字节）
            prefer_url: 是否优先返回URL，否则返回Base64
            no_compression: 是否跳过压缩处理（直接返回原图），用于 embedding 场景

        Returns:
            Tuple[Optional[str], Optional[str]]: (处理后的URL, 处理后的Base64字符串)
            - 如果 prefer_url=True 且成功：返回 (url, None)
            - 如果 prefer_url=False 且成功：返回 (None, base64_str)
            - 如果失败：返回 (None, None)
        """
        try:

            # 始终使用原始路径进行下载（支持本地路径和URL）
            download_path = image_url

            logger.info(
                f"[StorageService] Processing reference image: {download_path}, no_compression={no_compression}"
            )

            # 下载/读取图片
            image_bytes = await self._download_image(download_path)
            if not image_bytes:
                logger.error(
                    f"[StorageService] Failed to download/read image: {download_path}"
                )
                return None, None

            # 处理图片（如果 no_compression=True，跳过压缩）
            if no_compression:
                processed_bytes = image_bytes
                logger.info(
                    f"[StorageService] Using original image (no compression), size={len(processed_bytes)} bytes"
                )
            else:
                processed_bytes = self._resize_and_compress_image(
                    image_bytes,
                    max_dimension=max_dimension,
                    max_size_bytes=max_size_bytes,
                )

            if not processed_bytes:
                logger.error(
                    f"[StorageService] Failed to process image: {download_path}"
                )
                return None, None

            # 返回结果
            if prefer_url:
                # 保存到临时位置并返回URL（强制使用COS公网URL）
                temp_url = await self._save_temp_image(
                    processed_bytes, image_url, force_cos_url=True
                )
                if temp_url:
                    return temp_url, None
                # 如果保存失败，降级为Base64
                base64_str = self._image_to_base64(processed_bytes, image_url)
                return None, base64_str
            else:
                # 强制返回Base64（不返回任何URL，避免容器内访问问题）
                base64_str = self._image_to_base64(processed_bytes, image_url)
                logger.info(
                    f"[StorageService] Converted image to Base64, length={len(base64_str)}"
                )
                return None, base64_str

        except Exception as e:
            logger.error(
                f"[StorageService] Error processing reference image {image_url}: {e}",
                exc_info=True,
            )
            return None, None

    def _ensure_full_url(self, url: str) -> Optional[str]:
        """
        确保URL是完整的公网URL

        Args:
            url: 可能是相对路径或完整URL

        Returns:
            Optional[str]: 完整的公网URL，或None如果无法构建
        """
        if not url:
            return None

        # 如果已经是完整URL
        if url.startswith(("http://", "https://")):
            return url

        # 如果是Base64字符串，直接返回
        if url.startswith("data:"):
            return url

        # 如果是相对路径（如 /cos/...）
        if url.startswith("/cos/"):
            # 构建完整URL
            cos_prefix = self._get_cos_url_prefix()
            if cos_prefix and not cos_prefix.startswith("https://your-bucket"):
                relative_path = url[5:]  # 去掉 /cos/
                return f"{cos_prefix}/{relative_path}"
            # 如果没有配置COS，返回None表示使用本地路径
            return None

        # 其他情况，尝试直接使用
        return url

    async def _download_image(self, url: str) -> Optional[bytes]:
        """
        从URL下载图片或读取本地文件

        Args:
            url: 图片URL或本地文件路径

        Returns:
            Optional[bytes]: 图片二进制数据
        """
        try:
            # 适配三种部署场景的图片 URL → 本地路径转换：
            # 1. 本地 Docker: http://127.0.0.1:8000/cos/...
            # 2. 局域网服务器: http://192.168.x.x:8000/cos/...
            # 3. 云服务器: https://xxx/cos/...（公有云 URL 无法走本地路径，走 HTTP 下载）
            # 共性：所有 /cos/ 路径的 URL，优先尝试本地 COS 挂载目录读取
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https") and parsed.path.startswith("/cos/"):
                url = parsed.path
                logger.info(
                    f"[StorageService] Converted URL to local path: {url} (host={parsed.hostname})"
                )

            # 检查是否是本地路径
            if url.startswith("/cos/"):
                # 将 /cos/ 开头的路径转换为本地文件路径
                local_path = self.cos_mount_path / url[5:]
                if local_path.exists():
                    content = local_path.read_bytes()
                    logger.info(
                        f"[StorageService] Read local image: {local_path}, size={len(content)}"
                    )
                    return content
                else:
                    logger.warning(
                        f"[StorageService] Local file not found: {local_path}, trying HTTP..."
                    )

            # 检查是否是完整的本地文件路径
            if Path(url).exists():
                content = Path(url).read_bytes()
                logger.info(
                    f"[StorageService] Read local image: {url}, size={len(content)}"
                )
                return content

            # 尝试从URL下载
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as response:
                    response.raise_for_status()
                    content = await response.read()
                    logger.info(
                        f"[StorageService] Downloaded image: {url}, size={len(content)}"
                    )
                    return content
        except Exception as e:
            logger.error(f"[StorageService] Failed to download/read image {url}: {e}")
            return None

    def _resize_and_compress_image(
        self,
        image_bytes: bytes,
        max_dimension: int = 2048,
        max_size_bytes: int = 20 * 1024 * 1024,
    ) -> Optional[bytes]:
        """
        缩放和压缩图片

        Args:
            image_bytes: 原始图片二进制数据
            max_dimension: 最大边长
            max_size_bytes: 最大文件大小

        Returns:
            Optional[bytes]: 处理后的图片二进制数据
        """
        try:
            from PIL import Image

            # 打开图片
            image = Image.open(io.BytesIO(image_bytes))
            original_mode = image.mode
            original_size = image.size

            logger.debug(
                f"[StorageService] Original image: mode={original_mode}, size={original_size}, bytes={len(image_bytes)}"
            )

            # 处理RGBA等模式
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                if image.mode in ("RGBA", "LA"):
                    background.paste(
                        image,
                        mask=(
                            image.split()[-1] if image.mode in ("RGBA", "LA") else None
                        ),
                    )
                    image = background
                else:
                    image = image.convert("RGB")
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # 1. 缩放到最大边长
            width, height = image.size
            if width > max_dimension or height > max_dimension:
                # 计算缩放比例
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(
                    f"[StorageService] Resized image: {original_size} -> {(new_width, new_height)}"
                )

            # 2. 压缩到文件大小限制
            output_bytes = self._compress_to_size(image, max_size_bytes)

            logger.debug(f"[StorageService] Processed image: bytes={len(output_bytes)}")
            return output_bytes

        except Exception as e:
            logger.error(
                f"[StorageService] Failed to resize/compress image: {e}", exc_info=True
            )
            return None

    def _compress_to_size(
        self,
        image,
        max_size_bytes: int,
        initial_quality: int = 95,
        min_quality: int = 10,
    ) -> bytes:
        """
        压缩图片到指定大小

        Args:
            image: PIL图片对象
            max_size_bytes: 最大文件大小
            initial_quality: 初始质量
            min_quality: 最小质量

        Returns:
            bytes: 压缩后的图片二进制数据
        """
        from PIL import Image

        quality = initial_quality

        while quality >= min_quality:
            output_buffer = io.BytesIO()
            image.save(output_buffer, format="JPEG", quality=quality, optimize=True)
            output_bytes = output_buffer.getvalue()

            if len(output_bytes) <= max_size_bytes:
                logger.debug(
                    f"[StorageService] Compressed image to {len(output_bytes)} bytes at quality={quality}"
                )
                return output_bytes

            # 降低质量
            quality -= 10

        # 如果即使最低质量也超过限制，尝试进一步缩小图片
        logger.warning(
            f"[StorageService] Even min quality {min_quality} exceeds size limit, further resizing"
        )

        # 渐进式缩小
        scale_factor = 0.9
        while scale_factor > 0.3:
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output_buffer = io.BytesIO()
            resized.save(
                output_buffer, format="JPEG", quality=min_quality, optimize=True
            )
            output_bytes = output_buffer.getvalue()

            if len(output_bytes) <= max_size_bytes:
                logger.debug(
                    f"[StorageService] Compressed image to {len(output_bytes)} bytes by resizing to {new_width}x{new_height}"
                )
                return output_bytes

            scale_factor -= 0.1

        # 最后尝试：返回最小尺寸
        logger.warning(
            "[StorageService] Could not reach target size, returning smallest possible"
        )
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=min_quality, optimize=True)
        return output_buffer.getvalue()

    def _image_to_base64(self, image_bytes: bytes, original_url: str) -> str:
        """
        将图片二进制数据转换为Base64字符串

        Args:
            image_bytes: 图片二进制数据
            original_url: 原始URL（用于确定MIME类型）

        Returns:
            str: Base64编码字符串（带data:前缀）
        """
        import base64

        # 确定MIME类型
        ext = _get_file_extension(original_url, "jpg").lower()
        mime_type = "image/jpeg"  # 默认
        if ext == "png":
            mime_type = "image/png"
        elif ext == "gif":
            mime_type = "image/gif"
        elif ext == "webp":
            mime_type = "image/webp"

        # 编码
        base64_data = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"

    async def _save_temp_image(
        self, image_bytes: bytes, original_url: str, force_cos_url: bool = False
    ) -> Optional[str]:
        """
        保存处理后的图片到临时位置并返回URL

        Args:
            image_bytes: 图片二进制数据
            original_url: 原始URL（用于确定扩展名）
            force_cos_url: 是否强制返回COS公网URL（用于需要外部访问的场景）

        Returns:
            Optional[str]: 访问URL
        """
        if not self._ensure_cos_mount():
            return None

        try:
            # 生成临时路径
            import uuid

            temp_id = str(uuid.uuid4())[:8]

            # 保存到临时目录
            temp_path = self.cos_mount_path / "temp" / "processed_images"
            temp_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            ext = _get_file_extension(original_url, "jpg")
            filename = f"processed_{temp_id}.{ext}"
            file_path = temp_path / filename

            # 保存文件
            file_path.write_bytes(image_bytes)

            # 返回URL
            if force_cos_url:
                # 强制返回COS公网URL（用于AI模型访问）
                try:
                    relative_path = file_path.relative_to(self.local_storage_path)
                    # 构建完整的COS路径（带前缀）
                    cos_path = str(relative_path)
                    if self.cos_path_prefix:
                        prefix = self.cos_path_prefix.strip("/")
                        if not cos_path.startswith(prefix + "/"):
                            cos_path = f"{prefix}/{cos_path}"
                    # 构建完整的公网URL
                    if self._cos_url_prefix:
                        url = (
                            f"{self._cos_url_prefix.rstrip('/')}/{cos_path.lstrip('/')}"
                        )
                        logger.info(
                            f"[StorageService] Built COS URL from prefix: {url}"
                        )
                        return url
                    elif self.cos_bucket and self.cos_region:
                        url = f"https://{self.cos_bucket}.cos.{self.cos_region}.myqcloud.com/{cos_path.lstrip('/')}"
                        logger.info(
                            f"[StorageService] Built COS URL from bucket/region: {url}"
                        )
                        return url
                    else:
                        logger.warning(
                            "[StorageService] COS not configured, falling back to normal URL"
                        )
                        return self._path_to_url(file_path)
                except Exception as e:
                    logger.warning(
                        f"[StorageService] Failed to build COS URL, falling back: {e}"
                    )
                    return self._path_to_url(file_path)
            else:
                return self._path_to_url(file_path)

        except Exception as e:
            logger.error(f"[StorageService] Failed to save temp image: {e}")
            return None

    async def process_reference_images(
        self,
        image_urls: List[str],
        max_dimension: int = 2048,
        max_size_bytes: int = 20 * 1024 * 1024,
        prefer_url: bool = False,
    ) -> List[str]:
        """
        批量处理参考图片

        Args:
            image_urls: 图片URL列表
            max_dimension: 最大边长
            max_size_bytes: 最大文件大小
            prefer_url: 是否优先返回URL

        Returns:
            List[str]: 处理后的图片列表（URL或Base64）
        """
        results = []

        for url in image_urls:
            processed_url, processed_base64 = await self.process_reference_image(
                url,
                max_dimension=max_dimension,
                max_size_bytes=max_size_bytes,
                prefer_url=prefer_url,
            )

            if processed_url:
                results.append(processed_url)
            elif processed_base64:
                results.append(processed_base64)
            else:
                # 处理失败，保留原URL（尝试补全）
                full_url = self._ensure_full_url(url)
                if full_url:
                    results.append(full_url)
                else:
                    results.append(url)

        return results

    # ==================== 文件删除 ====================

    def delete_task_content(
        self,
        owner_admin_id: int,
        task_id: int,
        item_id: int,
        date: Optional[str] = None,
    ) -> bool:
        """
        删除任务生成的所有内容

        Args:
            owner_admin_id: 创作管理员ID
            task_id: 任务ID
            item_id: 子任务ID
            date: 日期字符串

        Returns:
            bool: 是否删除成功
        """
        try:
            date_str = date or datetime.utcnow().strftime("%Y-%m-%d")
            base_path = (
                self.local_storage_path
                / self.TASKS_DIR
                / str(owner_admin_id)
                / date_str
                / str(task_id)
                / str(item_id)
            )

            if base_path.exists():
                import shutil

                shutil.rmtree(base_path)
                logger.info(f"Deleted task content: {base_path}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete task content: {e}")
            return False

    def delete_material(
        self,
        owner_admin_id: int,
        resource_type: ResourceType,
        resource_id: int,
    ) -> bool:
        """
        删除素材/模板资源的所有物理文件（包含 original、thumbnails 等子目录）

        Args:
            owner_admin_id: 创作管理员ID
            resource_type: 资源类型
            resource_id: 资源ID

        Returns:
            bool: 是否删除成功
        """
        try:
            # 不传 sub_dir，获取素材根目录（如 Materials/{id}/images/{id}/）
            # 通过直接构建路径绕过 sub_dir 默认值
            base_path = (
                self.local_storage_path
                / self.MATERIALS_DIR
                / str(owner_admin_id)
                / resource_type.value
                / str(resource_id)
            )

            logger.info(f"[StorageService] Deleting material directory: {base_path}")

            if base_path.exists():
                import shutil

                shutil.rmtree(base_path)
                logger.info(f"[StorageService] Deleted material directory: {base_path}")
                return True
            else:
                logger.warning(
                    f"[StorageService] Material directory does not exist: {base_path}"
                )
                return False

        except Exception as e:
            logger.error(
                f"[StorageService] Failed to delete material directory: {e}",
                exc_info=True,
            )
            return False


# 全局存储服务实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    获取存储服务单例

    Returns:
        StorageService: 存储服务实例
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
