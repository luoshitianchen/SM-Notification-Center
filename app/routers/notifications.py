"""通知渠道/模板/发送记录路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.notification import (
    ChannelCreate,
    ChannelStatusUpdate,
    ChannelUpdate,
    NotificationDeliver,
    NotificationSend,
    TemplateCreate,
    TemplateUpdate,
)
from app.services.notification_channel import ChannelService
from app.services.notification_record import NotificationRecordService
from app.services.notification_template import TemplateService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ── 渠道 ──
@router.get("/channels")
async def list_channels(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    channel_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    keyword: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.list_channels(
        session, limit=limit, offset=offset,
        channel_type=channel_type, status_filter=status_filter, keyword=keyword,
    )


@router.post("/channels", status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: ChannelCreate, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.create_channel(session, payload, request)


@router.get("/channels/{channel_id}")
async def get_channel(
    channel_id: str, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.get_channel(session, channel_id)


@router.patch("/channels/{channel_id}")
async def update_channel(
    channel_id: str, payload: ChannelUpdate, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.update_channel(session, channel_id, payload, request)


@router.patch("/channels/{channel_id}/status")
async def update_channel_status(
    channel_id: str, payload: ChannelStatusUpdate, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.update_status(session, channel_id, payload.status, request)


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await ChannelService.delete_channel(session, channel_id, request)


# ── 模板 ──
@router.get("/templates")
async def list_templates(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    channel_type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await TemplateService.list_templates(
        session, limit=limit, offset=offset,
        channel_type=channel_type, keyword=keyword,
    )


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await TemplateService.create_template(session, payload, request)


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await TemplateService.get_template(session, template_id)


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str, payload: TemplateUpdate, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await TemplateService.update_template(session, template_id, payload, request)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await TemplateService.delete_template(session, template_id, request)


# ── 发送记录 ──
@router.get("/records")
async def list_records(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    channel_id: str | None = Query(default=None),
    template_code: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await NotificationRecordService.list_records(
        session, limit=limit, offset=offset, status_filter=status_filter,
        channel_id=channel_id, template_code=template_code, keyword=keyword,
    )


@router.post("/records", status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationSend, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await NotificationRecordService.send(session, payload, request)


@router.get("/records/{record_id}")
async def get_record(
    record_id: str, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await NotificationRecordService.get_record(session, record_id)


@router.post("/records/{record_id}/deliver")
async def deliver_notification(
    record_id: str, payload: NotificationDeliver, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await NotificationRecordService.deliver(session, record_id, payload, request)
