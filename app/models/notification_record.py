"""通知发送记录模型：每条消息的投递流水。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class NotificationRecord(Base):
    """通知发送记录：状态机 pending -> sent / failed。"""

    __tablename__ = "notification_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    template_code: Mapped[str] = mapped_column(String(128), nullable=False, default="", index=True)
    recipient: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(256), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    # 投递状态：pending / sent / failed
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
