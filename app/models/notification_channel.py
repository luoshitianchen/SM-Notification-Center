"""通知渠道模型：邮件/短信/Webhook/推送渠道配置。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class NotificationChannel(Base):
    """通知渠道：按名称唯一，记录渠道类型与连接配置。"""

    __tablename__ = "notification_channels"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    # 渠道类型：email / sms / webhook / push
    channel_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # 渠道连接配置（JSON 字符串，脱敏后存储）
    config: Mapped[str] = mapped_column(Text, default="{}")
    # 渠道状态：active / disabled
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
