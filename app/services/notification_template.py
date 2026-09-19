"""通知模板服务层：模板 CRUD。"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import internal_write_allowed
from app.models.notification_template import NotificationTemplate
from app.repositories import notification_template as repo
from app.schemas.notification import TemplateCreate, TemplateUpdate
from app.services.audit import record_audit


def _template_to_dict(t: NotificationTemplate) -> dict:
    return {
        "id": t.id, "code": t.code, "name": t.name, "channel_type": t.channel_type,
        "title_template": t.title_template, "body_template": t.body_template,
        "description": t.description,
        "created_at": t.created_at.isoformat() if t.created_at else "",
        "updated_at": t.updated_at.isoformat() if t.updated_at else "",
    }


class TemplateService:
    @staticmethod
    async def list_templates(
        session: AsyncSession, limit: int, offset: int,
        channel_type: str | None, keyword: str | None,
    ) -> dict:
        items = await repo.list_templates(
            session, limit=limit, offset=offset,
            channel_type=channel_type, keyword=keyword,
        )
        total = await repo.count_templates(
            session, channel_type=channel_type, keyword=keyword,
        )
        return {"total": total, "items": [_template_to_dict(t) for t in items]}

    @staticmethod
    async def get_template(session: AsyncSession, template_id: str) -> dict:
        template = await repo.get_template(session, template_id)
        if not template:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知模板不存在")
        return _template_to_dict(template)

    @staticmethod
    async def create_template(session: AsyncSession, payload: TemplateCreate, request: Request) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        if not payload.body_template:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "模板正文不能为空")
        if await repo.get_template_by_code(session, payload.code):
            raise HTTPException(status.HTTP_409_CONFLICT, "模板编码已存在")
        template = NotificationTemplate(
            id=str(uuid.uuid4()),
            code=payload.code,
            name=payload.name,
            channel_type=payload.channel_type,
            title_template=payload.title_template,
            body_template=payload.body_template,
            description=payload.description,
        )
        template = await repo.create_template(session, template)
        await record_audit(session, "template.created", "internal",
                           f"code={payload.code}", request)
        return _template_to_dict(template)

    @staticmethod
    async def update_template(
        session: AsyncSession, template_id: str, payload: TemplateUpdate, request: Request,
    ) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        template = await repo.get_template(session, template_id)
        if not template:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知模板不存在")
        if payload.name is not None:
            template.name = payload.name
        if payload.title_template is not None:
            template.title_template = payload.title_template
        if payload.body_template is not None:
            template.body_template = payload.body_template
        if payload.description is not None:
            template.description = payload.description
        template = await repo.update_template(session, template)
        await record_audit(session, "template.updated", "internal", f"id={template_id}", request)
        return _template_to_dict(template)

    @staticmethod
    async def delete_template(session: AsyncSession, template_id: str, request: Request) -> dict:
        if not internal_write_allowed(request):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")
        template = await repo.get_template(session, template_id)
        if not template:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知模板不存在")
        await repo.delete_template(session, template)
        await record_audit(session, "template.deleted", "internal", f"id={template_id}", request)
        return {"deleted": True, "id": template_id}
