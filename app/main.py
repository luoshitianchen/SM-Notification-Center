"""SM Notification Center —— 企业通知中心：渠道、模板、消息发送与投递回执。"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field

from app import base

SERVICE = "sm-notification-center"
VERSION = "2.0.0"
NAME = "SM Notification Center"
DESCRIPTION = "企业通知中心：渠道、模板、消息发送与投递回执"
PORT = 8470


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _init() -> None:
    with base.db_ctx() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, channel_type TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}', enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, channel_type TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '', body TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY, channel TEXT NOT NULL, template TEXT,
                recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                error TEXT, created_at TEXT NOT NULL, sent_at TEXT, delivered_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status, created_at DESC);
            """
        )


app = base.create_app(
    service=SERVICE, name=NAME, description=DESCRIPTION, version=VERSION, port=PORT,
    dependencies=["sm-iam", "sm-event-bus", "sm-audit-log-center"],
    events=["notification.sent", "notification.failed", "notification.delivered"],
    overview_fn=lambda _r: {
        "summary": {
            "channels": base.get_db().execute("SELECT COUNT(*) FROM channels").fetchone()[0],
            "templates": base.get_db().execute("SELECT COUNT(*) FROM templates").fetchone()[0],
            "sent": base.get_db().execute("SELECT COUNT(*) FROM notifications WHERE status='sent'").fetchone()[0],
            "failed": base.get_db().execute("SELECT COUNT(*) FROM notifications WHERE status='failed'").fetchone()[0],
        }
    },
)
_init()


class ChannelIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    channel_type: str = Field(pattern=r"^(email|sms|webhook|inapp)$")
    config: dict[str, Any] = Field(default_factory=dict)


class TemplateIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    channel_type: str = Field(pattern=r"^(email|sms|webhook|inapp)$")
    subject: str = Field(default="", max_length=200)
    body: str = Field(min_length=1, max_length=4000)


class SendIn(BaseModel):
    channel: str = Field(min_length=1, max_length=80)
    recipient: str = Field(min_length=1, max_length=200)
    template: str | None = Field(default=None, max_length=80)
    subject: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=4000)
    payload: dict[str, Any] = Field(default_factory=dict)


def _render(template: str, payload: dict[str, Any]) -> str:
    for key, value in payload.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


@app.get("/api/notifications/channels")
def list_channels() -> dict[str, Any]:
    with base.db_ctx() as conn:
        rows = conn.execute("SELECT * FROM channels ORDER BY created_at DESC").fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@app.post("/api/notifications/channels", status_code=status.HTTP_201_CREATED)
def create_channel(payload: ChannelIn, request: Request) -> dict[str, Any]:
    base.require_internal_token(request)
    channel_id = str(uuid.uuid4())
    with base.db_ctx() as conn:
        try:
            conn.execute("INSERT INTO channels VALUES (?,?,?,?,?,?)", (channel_id, payload.name, payload.channel_type, json.dumps(payload.config, ensure_ascii=False), 1, _now()))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status.HTTP_409_CONFLICT, "渠道已存在") from exc
    return {"id": channel_id, "name": payload.name}


@app.get("/api/notifications/templates")
def list_templates() -> dict[str, Any]:
    with base.db_ctx() as conn:
        rows = conn.execute("SELECT * FROM templates ORDER BY created_at DESC").fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@app.post("/api/notifications/templates", status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateIn, request: Request) -> dict[str, Any]:
    base.require_internal_token(request)
    template_id = str(uuid.uuid4())
    with base.db_ctx() as conn:
        try:
            conn.execute("INSERT INTO templates VALUES (?,?,?,?,?,?)", (template_id, payload.name, payload.channel_type, payload.subject, payload.body, _now()))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status.HTTP_409_CONFLICT, "模板已存在") from exc
    return {"id": template_id, "name": payload.name}


@app.post("/api/notifications/send", status_code=status.HTTP_201_CREATED)
def send_notification(payload: SendIn, request: Request) -> dict[str, Any]:
    base.require_internal_token(request)
    with base.db_ctx() as conn:
        channel = conn.execute("SELECT * FROM channels WHERE name=?", (payload.channel,)).fetchone()
        if not channel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "渠道不存在")
        if not channel["enabled"]:
            raise HTTPException(status.HTTP_423_LOCKED, "渠道已停用")
        subject, body = payload.subject or "", payload.body or ""
        if payload.template:
            template = conn.execute("SELECT * FROM templates WHERE name=?", (payload.template,)).fetchone()
            if not template:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "模板不存在")
            if template["channel_type"] != channel["channel_type"]:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "模板与渠道类型不匹配")
            subject = _render(template["subject"], payload.payload)
            body = _render(template["body"], payload.payload)
        notif_id = str(uuid.uuid4())
        # 模拟渠道投递：webhook/inapp 视为成功，email/sms 视为已发送
        status_ = "delivered" if channel["channel_type"] in {"webhook", "inapp"} else "sent"
        conn.execute(
            "INSERT INTO notifications (id, channel, template, recipient, subject, body, status, attempts, error, created_at, sent_at, delivered_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (notif_id, payload.channel, payload.template, payload.recipient, subject, body, status_, 1, None, _now(), _now(), _now() if status_ == "delivered" else None),
        )
        base.record_audit("notification.sent", "internal", f"channel={payload.channel} recipient={payload.recipient}", getattr(request.state, "request_id", ""), getattr(request.state, "trace_id", ""), SERVICE)
    return {"id": notif_id, "channel": payload.channel, "recipient": payload.recipient, "status": status_}


@app.get("/api/notifications")
def list_notifications(status_: str | None = None, limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(200, limit))
    with base.db_ctx() as conn:
        if status_:
            rows = conn.execute("SELECT * FROM notifications WHERE status=? ORDER BY created_at DESC LIMIT ?", (status_, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@app.get("/api/notifications/stats")
def stats() -> dict[str, Any]:
    with base.db_ctx() as conn:
        def _count(sql: str) -> int:
            return conn.execute(sql).fetchone()[0]
        return {
            "pending": _count("SELECT COUNT(*) FROM notifications WHERE status='pending'"),
            "sent": _count("SELECT COUNT(*) FROM notifications WHERE status='sent'"),
            "delivered": _count("SELECT COUNT(*) FROM notifications WHERE status='delivered'"),
            "failed": _count("SELECT COUNT(*) FROM notifications WHERE status='failed'"),
            "total": _count("SELECT COUNT(*) FROM notifications"),
        }


@app.get("/api/notifications/{notif_id}")
def get_notification(notif_id: str) -> dict[str, Any]:
    with base.db_ctx() as conn:
        row = conn.execute("SELECT * FROM notifications WHERE id=?", (notif_id,)).fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "通知不存在")
    return dict(row)


@app.post("/api/notifications/{notif_id}/retry")
def retry_notification(notif_id: str, request: Request) -> dict[str, Any]:
    base.require_internal_token(request)
    with base.db_ctx() as conn:
        row = conn.execute("SELECT * FROM notifications WHERE id=?", (notif_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "通知不存在")
        conn.execute("UPDATE notifications SET status='sent', attempts=attempts+1, sent_at=? WHERE id=?", (_now(), notif_id))
    return {"id": notif_id, "status": "sent"}
