"""通知渠道仓储层。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_channel import NotificationChannel


async def get_channel(session: AsyncSession, channel_id: str) -> NotificationChannel | None:
    result = await session.execute(select(NotificationChannel).where(NotificationChannel.id == channel_id))
    return result.scalar_one_or_none()


async def get_channel_by_name(session: AsyncSession, name: str) -> NotificationChannel | None:
    result = await session.execute(select(NotificationChannel).where(NotificationChannel.name == name))
    return result.scalar_one_or_none()


async def list_channels(
    session: AsyncSession, limit: int = 100, offset: int = 0,
    channel_type: str | None = None, status: str | None = None, keyword: str | None = None,
) -> list[NotificationChannel]:
    stmt = select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
    if channel_type:
        stmt = stmt.where(NotificationChannel.channel_type == channel_type)
    if status:
        stmt = stmt.where(NotificationChannel.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(
            NotificationChannel.name.like(pattern),
        ))
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_channels(
    session: AsyncSession, channel_type: str | None = None,
    status: str | None = None, keyword: str | None = None,
) -> int:
    stmt = select(func.count(NotificationChannel.id))
    if channel_type:
        stmt = stmt.where(NotificationChannel.channel_type == channel_type)
    if status:
        stmt = stmt.where(NotificationChannel.status == status)
    if keyword:
        stmt = stmt.where(NotificationChannel.name.like(f"%{keyword}%"))
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def create_channel(session: AsyncSession, channel: NotificationChannel) -> NotificationChannel:
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


async def update_channel(session: AsyncSession, channel: NotificationChannel) -> NotificationChannel:
    await session.commit()
    await session.refresh(channel)
    return channel


async def delete_channel(session: AsyncSession, channel: NotificationChannel) -> None:
    await session.delete(channel)
    await session.commit()
