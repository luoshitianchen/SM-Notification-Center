"""通知发送记录仓储层。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_record import NotificationRecord


async def get_record(session: AsyncSession, record_id: str) -> NotificationRecord | None:
    result = await session.execute(select(NotificationRecord).where(NotificationRecord.id == record_id))
    return result.scalar_one_or_none()


async def list_records(
    session: AsyncSession, limit: int = 100, offset: int = 0,
    status: str | None = None, channel_id: str | None = None,
    template_code: str | None = None, keyword: str | None = None,
) -> list[NotificationRecord]:
    stmt = select(NotificationRecord).order_by(NotificationRecord.created_at.desc())
    if status:
        stmt = stmt.where(NotificationRecord.status == status)
    if channel_id:
        stmt = stmt.where(NotificationRecord.channel_id == channel_id)
    if template_code:
        stmt = stmt.where(NotificationRecord.template_code == template_code)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(
            NotificationRecord.recipient.like(pattern),
            NotificationRecord.subject.like(pattern),
        ))
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_records(
    session: AsyncSession, status: str | None = None,
    channel_id: str | None = None, template_code: str | None = None,
    keyword: str | None = None,
) -> int:
    stmt = select(func.count(NotificationRecord.id))
    if status:
        stmt = stmt.where(NotificationRecord.status == status)
    if channel_id:
        stmt = stmt.where(NotificationRecord.channel_id == channel_id)
    if template_code:
        stmt = stmt.where(NotificationRecord.template_code == template_code)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(
            NotificationRecord.recipient.like(pattern),
            NotificationRecord.subject.like(pattern),
        ))
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def create_record(session: AsyncSession, record: NotificationRecord) -> NotificationRecord:
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def update_record(session: AsyncSession, record: NotificationRecord) -> NotificationRecord:
    await session.commit()
    await session.refresh(record)
    return record
