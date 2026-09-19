"""通知渠道服务层：渠道 CRUD 与启停。"""
from __future__ import annotations

import json
import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import internal_write_allowed
from app.models.notification_channel import NotificationChannel
from app.repositories import notification_channel as repo
from app.schemas.notification import ChannelCreate, ChannelUpdate
from app.services.audit import record_audit


def _channel_to_dict(c: NotificationChannel) -> dict:
    return {
        "id": c.id, "name": c.name, "channel_type": c.channel_type,
        "config": c.config, "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "updated_at": c.updated_at.isoformat() if c.updated_at else "",
    }


class ChannelService:
    @staticmethod
    async def list_channels(
        session: AsyncSession, limit: int, offset: int,
        channel_type: str | None, status_filter: str | None, keyword: str | None,
    ) -> dict:
        items = await repo.list_channels(
            session, limit=limit, offset=offset,
            channel_type=channel_type, status=status_filter, keyword=keyword,
        )
        total = await repo.count_channels(
            session, channel_type=channel_type,
            status=status_filter, keyword=keyword,
        )
        return {"total": total, "items": [_channel_to_dict(c) for c in items]}

    @staticmethod
    async def get_channel(session: AsyncSession, channel_id: str) -> dict:
        channel = await repo.get_channel(session, channel_id)
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知渠道不存在")
        return _channel_to_dict(channel)

    @staticmethod
    async def create_channel(session: AsyncSession, payload: ChannelCreate, request: Request) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        # 校验 config 必须是合法 JSON
        try:
            json.loads(payload.config)
        except (json.JSONDecodeError, TypeError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "config 必须是合法 JSON") from exc
        if await repo.get_channel_by_name(session, payload.name):
            raise HTTPException(status.HTTP_409_CONFLICT, "渠道名称已存在")
        channel = NotificationChannel(
            id=str(uuid.uuid4()),
            name=payload.name,
            channel_type=payload.channel_type,
            config=payload.config,
            status="active",
        )
        channel = await repo.create_channel(session, channel)
        await record_audit(session, "channel.created", "internal",
                           f"name={payload.name} type={payload.channel_type}", request)
        return _channel_to_dict(channel)

    @staticmethod
    async def update_channel(
        session: AsyncSession, channel_id: str, payload: ChannelUpdate, request: Request,
    ) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        channel = await repo.get_channel(session, channel_id)
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知渠道不存在")
        if payload.config is not None:
            try:
                json.loads(payload.config)
            except (json.JSONDecodeError, TypeError) as exc:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "config 必须是合法 JSON") from exc
            channel.config = payload.config
        channel = await repo.update_channel(session, channel)
        await record_audit(session, "channel.updated", "internal", f"id={channel_id}", request)
        return _channel_to_dict(channel)

    @staticmethod
    async def update_status(
        session: AsyncSession, channel_id: str, new_status: str, request: Request,
    ) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        channel = await repo.get_channel(session, channel_id)
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知渠道不存在")
        channel.status = new_status
        channel = await repo.update_channel(session, channel)
        await record_audit(session, "channel.status_changed", "internal",
                           f"id={channel_id} status={new_status}", request)
        return _channel_to_dict(channel)

    @staticmethod
    async def delete_channel(session: AsyncSession, channel_id: str, request: Request) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        channel = await repo.get_channel(session, channel_id)
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知渠道不存在")
        await repo.delete_channel(session, channel)
        await record_audit(session, "channel.deleted", "internal", f"id={channel_id}", request)
        return {"deleted": True, "id": channel_id}
