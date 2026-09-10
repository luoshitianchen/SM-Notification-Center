"""告警接入路由：供内部服务按令牌上报告警事件。"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import internal_write_allowed
from app.schemas.alert import AlertIngest
from app.services.audit import record_audit

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_alert(
    payload: AlertIngest, request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """接入外部告警：需内部令牌 (X-Internal-Token)。"""
    if not internal_write_allowed(request):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "内部写入令牌无效")

    alert_id = str(uuid.uuid4())
    await record_audit(
        session, "alert.ingested", payload.source,
        detail=f"alert_id={alert_id} severity={payload.severity} summary={payload.summary}",
        request=request,
    )
    return {"status": "accepted", "alert_id": alert_id, "severity": payload.severity}
