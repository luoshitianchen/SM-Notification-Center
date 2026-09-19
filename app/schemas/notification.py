"""通知渠道/模板/发送记录 Pydantic 模型。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ChannelType = Literal["email", "sms", "webhook", "push"]


# ── 渠道 ──
class ChannelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128, pattern=r"^[a-zA-Z0-9_.-]+$")
    channel_type: ChannelType = "email"
    config: str = Field(default="{}", max_length=4096)


class ChannelUpdate(BaseModel):
    config: str | None = Field(default=None, max_length=4096)


class ChannelStatusUpdate(BaseModel):
    status: Literal["active", "disabled"]


class ChannelResponse(BaseModel):
    id: str
    name: str
    channel_type: str
    config: str
    status: str
    created_at: str
    updated_at: str


# ── 模板 ──
class TemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=128, pattern=r"^[a-zA-Z0-9_.-]+$")
    name: str = Field(default="", max_length=128)
    channel_type: ChannelType = "email"
    title_template: str = Field(default="", max_length=512)
    body_template: str = Field(default="", max_length=4096)
    description: str = Field(default="", max_length=1000)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    title_template: str | None = Field(default=None, max_length=512)
    body_template: str | None = Field(default=None, max_length=4096)
    description: str | None = Field(default=None, max_length=1000)


class TemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    channel_type: str
    title_template: str
    body_template: str
    description: str
    created_at: str
    updated_at: str


# ── 发送记录 ──
class NotificationSend(BaseModel):
    channel_id: str = Field(min_length=1, max_length=64)
    template_code: str = Field(default="", max_length=128)
    recipient: str = Field(min_length=1, max_length=256)
    subject: str = Field(default="", max_length=256)
    body: str = Field(default="", max_length=4096)


class NotificationDeliver(BaseModel):
    """投递结果回写。"""
    status: Literal["sent", "failed"]
    error: str | None = Field(default=None, max_length=1000)


class NotificationRecordResponse(BaseModel):
    id: str
    channel_id: str
    template_code: str
    recipient: str
    subject: str
    body: str
    status: str
    error: str
    created_at: str
    sent_at: str | None = None


class NotificationListResponse(BaseModel):
    total: int
    items: list[BaseModel]
