"""通知模板模型：可复用的消息标题/正文模板。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class NotificationTemplate(Base):
    """通知模板：按编码唯一，绑定渠道类型。"""

    __tablename__ = "notification_templates"
    __table_args__ = (UniqueConstraint("code", name="uq_template_code"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    # 适用渠道类型：email / sms / webhook / push
    channel_type: Mapped[str] = mapped_column(String(16), nullable=False, default="email", index=True)
    title_template: Mapped[str] = mapped_column(Text, default="")
    body_template: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
