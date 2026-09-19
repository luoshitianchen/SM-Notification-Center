"""通知模板仓储层。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_template import NotificationTemplate


async def get_template(session: AsyncSession, template_id: str) -> NotificationTemplate | None:
    result = await session.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    return result.scalar_one_or_none()


async def get_template_by_code(session: AsyncSession, code: str) -> NotificationTemplate | None:
    result = await session.execute(select(NotificationTemplate).where(NotificationTemplate.code == code))
    return result.scalar_one_or_none()


async def list_templates(
    session: AsyncSession, limit: int = 100, offset: int = 0,
    channel_type: str | None = None, keyword: str | None = None,
) -> list[NotificationTemplate]:
    stmt = select(NotificationTemplate).order_by(NotificationTemplate.created_at.desc())
    if channel_type:
        stmt = stmt.where(NotificationTemplate.channel_type == channel_type)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(
            NotificationTemplate.code.like(pattern),
            NotificationTemplate.name.like(pattern),
        ))
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_templates(
    session: AsyncSession, channel_type: str | None = None, keyword: str | None = None,
) -> int:
    stmt = select(func.count(NotificationTemplate.id))
    if channel_type:
        stmt = stmt.where(NotificationTemplate.channel_type == channel_type)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(or_(
            NotificationTemplate.code.like(pattern),
            NotificationTemplate.name.like(pattern),
        ))
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def create_template(session: AsyncSession, template: NotificationTemplate) -> NotificationTemplate:
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def update_template(session: AsyncSession, template: NotificationTemplate) -> NotificationTemplate:
    await session.commit()
    await session.refresh(template)
    return template


async def delete_template(session: AsyncSession, template: NotificationTemplate) -> None:
    await session.delete(template)
    await session.commit()
