"""通知发送记录服务层：投递流水与状态机。"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import internal_write_allowed
from app.models.notification_record import NotificationRecord
from app.repositories import notification_channel as channel_repo
from app.repositories import notification_record as repo
from app.schemas.notification import NotificationDeliver, NotificationSend
from app.services.audit import record_audit

# 状态机：pending -> sent / failed；终态不可再变
_TRANSITIONS = {
    "pending": {"sent", "failed"},
    "sent": set(),
    "failed": set(),
}


def _record_to_dict(r: NotificationRecord) -> dict:
    return {
        "id": r.id, "channel_id": r.channel_id, "template_code": r.template_code,
        "recipient": r.recipient, "subject": r.subject, "body": r.body,
        "status": r.status, "error": r.error,
        "created_at": r.created_at.isoformat() if r.created_at else "",
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
    }


class NotificationRecordService:
    @staticmethod
    async def list_records(
        session: AsyncSession, limit: int, offset: int,
        status_filter: str | None, channel_id: str | None,
        template_code: str | None, keyword: str | None,
    ) -> dict:
        items = await repo.list_records(
            session, limit=limit, offset=offset, status=status_filter,
            channel_id=channel_id, template_code=template_code, keyword=keyword,
        )
        total = await repo.count_records(
            session, status=status_filter, channel_id=channel_id,
            template_code=template_code, keyword=keyword,
        )
        return {"total": total, "items": [_record_to_dict(r) for r in items]}

    @staticmethod
    async def get_record(session: AsyncSession, record_id: str) -> dict:
        record = await repo.get_record(session, record_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "发送记录不存在")
        return _record_to_dict(record)

    @staticmethod
    async def send(session: AsyncSession, payload: NotificationSend, request: Request) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        channel = await channel_repo.get_channel(session, payload.channel_id)
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知渠道不存在")
        if channel.status != "active":
            raise HTTPException(status.HTTP_409_CONFLICT, "渠道已停用，不可投递")
        record = NotificationRecord(
            id=str(uuid.uuid4()),
            channel_id=payload.channel_id,
            template_code=payload.template_code,
            recipient=payload.recipient,
            subject=payload.subject,
            body=payload.body,
            status="pending",
        )
        record = await repo.create_record(session, record)
        await record_audit(session, "notification.sent", "internal",
                           f"channel={payload.channel_id} recipient={payload.recipient}", request)
        return _record_to_dict(record)

    @staticmethod
    async def deliver(
        session: AsyncSession, record_id: str, payload: NotificationDeliver, request: Request,
    ) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        record = await repo.get_record(session, record_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "发送记录不存在")
        if payload.status not in _TRANSITIONS.get(record.status, set()):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"不允许从 {record.status} 迁移到 {payload.status}",
            )
        record.status = payload.status
        if payload.error is not None:
            record.error = payload.error
        if payload.status == "sent":
            record.sent_at = datetime.now(UTC)
        record = await repo.update_record(session, record)
        await record_audit(session, "notification.delivered", "internal",
                           f"id={record_id} status={payload.status}", request)
        return _record_to_dict(record)
