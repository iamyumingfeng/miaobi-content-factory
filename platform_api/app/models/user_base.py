"""
用户抽象基类 (user_base.py)

定义三个用户表共用的表结构，确保物理隔离的同时保持结构一致。

Author: Claude Code
Date: 2025
"""

from datetime import datetime

from sqlalchemy import (BigInteger, Column, DateTime, Enum, Integer, String)

from app.core.database import Base


class UserBase(Base):
    """
    用户抽象基类

    定义所有用户表共用的字段结构，确保三个用户表（super_admin、operator、sub_user）
    具有完全一致的表结构，但物理上独立存储。

    子类只需定义 __tablename__ 和各自的关系即可。
    """

    __abstract__ = True

    # 基础字段
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    userid = Column(
        String(64), unique=True, nullable=False, index=True, comment="用户ID（登录用）"
    )
    nickname = Column(String(100), nullable=False, comment="【管理备注名】管理员备注名")
    display_name = Column(
        String(100), nullable=True, comment="【自定义昵称】用户自定义昵称"
    )
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")

    # 微信绑定字段
    wechat_openid = Column(String(100), nullable=True, comment="微信OpenID")
    wechat_unionid = Column(String(100), nullable=True, comment="微信UnionID")

    # 状态字段（统一使用 online/offline/disabled）
    status = Column(
        Enum("online", "offline", "disabled", name="user_status_enum"),
        nullable=False,
        default="offline",
        index=True,
        comment="状态：online（在线）/ offline（已离线）/ disabled（已禁用）",
    )

    # 登录安全
    login_failure_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="连续登录失败次数",
    )
    locked_until = Column(DateTime, nullable=True, comment="账号锁定截止时间")

    # 用户定位字段（所有表统一包含）
    # 要点2【账号定位】：核心赛道、核心价值、目标受众匹配、账号层级等
    user_positioning = Column(
        String(500), nullable=True, comment="账号定位（核心赛道/价值/受众/层级等）"
    )
    user_category = Column(String(100), nullable=True, comment="账号的运营分类")

    # 创作者专属字段（所有表统一包含，保持结构一致）
    # 要点1【粉丝画像】：年龄、职业、地域、核心需求、偏好、禁忌等
    fan_profile = Column(
        String(500),
        nullable=True,
        comment="粉丝画像（年龄/职业/地域/需求/偏好/禁忌等）",
    )
    # 要点3【内容风格】：语气、排版逻辑、呈现形式、核心调性、固定句式/口头禅等
    content_style = Column(
        String(500), nullable=True, comment="内容风格（语气/排版/调性/句式等）"
    )
    account_type = Column(String(255), nullable=True, comment="账号类型")

    # 时间字段
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_password_changed_at = Column(
        DateTime, nullable=True, comment="最后密码修改时间"
    )
    created_at = Column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 外键字段（所有表统一包含，保持结构一致）
    # 注意：具体表中某些外键可能为 null，但结构保持一致
    created_by = Column(BigInteger, nullable=True, index=True, comment="创建者用户ID")
    owner_operator_id = Column(
        BigInteger, nullable=True, index=True, comment="所属创作管理员ID（数据隔离用）"
    )
    managed_by = Column(
        BigInteger, nullable=True, index=True, comment="当前管理者用户ID（支持转移）"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, userid={self.userid}, nickname={self.nickname})>"
