"""通知中心业务深化测试：渠道/模板/发送记录全生命周期。"""
from __future__ import annotations

H = {"X-Internal-Token": "test-internal-key-12345"}
BAD = {"X-Internal-Token": "wrong"}


# ═══════════════════════════════════════════════════════════
# 通知渠道
# ═══════════════════════════════════════════════════════════

class TestNotificationChannel:
    async def test_create_channel_success(self, client):
        resp = await client.post("/api/notifications/channels", json={
            "name": "email-primary", "channel_type": "email",
            "config": '{"smtp":"smtp.example.com"}',
        }, headers=H)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "email-primary"
        assert data["channel_type"] == "email"
        assert data["status"] == "active"

    async def test_create_channel_duplicate_name(self, client):
        payload = {"name": "ch-dup", "channel_type": "sms"}
        first = await client.post("/api/notifications/channels", json=payload, headers=H)
        assert first.status_code == 201
        second = await client.post("/api/notifications/channels", json=payload, headers=H)
        assert second.status_code == 409

    async def test_create_channel_invalid_json_config(self, client):
        resp = await client.post("/api/notifications/channels", json={
            "name": "ch-bad", "channel_type": "email", "config": "not-json",
        }, headers=H)
        assert resp.status_code == 400

    async def test_create_channel_requires_token(self, client):
        resp = await client.post("/api/notifications/channels", json={
            "name": "ch-notoken", "channel_type": "email",
        })
        assert resp.status_code in (401, 403)

    async def test_list_channels_filter_and_keyword(self, client):
        await client.post("/api/notifications/channels", json={
            "name": "ch-webhook-search", "channel_type": "webhook", "config": "{}",
        }, headers=H)
        resp = await client.get(
            "/api/notifications/channels?channel_type=webhook&keyword=search", headers=H,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["channel_type"] == "webhook"

    async def test_update_channel_status_disabled(self, client):
        create = await client.post("/api/notifications/channels", json={
            "name": "ch-status", "channel_type": "push", "config": "{}",
        }, headers=H)
        channel_id = create.json()["id"]
        resp = await client.patch(f"/api/notifications/channels/{channel_id}/status", json={
            "status": "disabled",
        }, headers=H)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"

    async def test_update_channel_config(self, client):
        create = await client.post("/api/notifications/channels", json={
            "name": "ch-cfg", "channel_type": "email", "config": "{}",
        }, headers=H)
        channel_id = create.json()["id"]
        resp = await client.patch(f"/api/notifications/channels/{channel_id}", json={
            "config": '{"smtp":"new.example.com"}',
        }, headers=H)
        assert resp.status_code == 200
        assert "new.example.com" in resp.json()["config"]

    async def test_get_channel_not_found(self, client):
        resp = await client.get("/api/notifications/channels/nonexistent", headers=H)
        assert resp.status_code == 404

    async def test_delete_channel(self, client):
        create = await client.post("/api/notifications/channels", json={
            "name": "ch-del", "channel_type": "email", "config": "{}",
        }, headers=H)
        channel_id = create.json()["id"]
        resp = await client.delete(f"/api/notifications/channels/{channel_id}", headers=H)
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True


# ═══════════════════════════════════════════════════════════
# 通知模板
# ═══════════════════════════════════════════════════════════

class TestNotificationTemplate:
    async def test_create_template_success(self, client):
        resp = await client.post("/api/notifications/templates", json={
            "code": "tpl-welcome", "name": "欢迎邮件", "channel_type": "email",
            "title_template": "欢迎 {{name}}", "body_template": "您好，欢迎加入",
        }, headers=H)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "tpl-welcome"
        assert data["channel_type"] == "email"

    async def test_create_template_duplicate_code(self, client):
        payload = {"code": "tpl-dup", "channel_type": "sms", "body_template": "x"}
        first = await client.post("/api/notifications/templates", json=payload, headers=H)
        assert first.status_code == 201
        second = await client.post("/api/notifications/templates", json=payload, headers=H)
        assert second.status_code == 409

    async def test_create_template_empty_body_rejected(self, client):
        resp = await client.post("/api/notifications/templates", json={
            "code": "tpl-empty", "channel_type": "email", "body_template": "",
        }, headers=H)
        assert resp.status_code == 400

    async def test_list_templates_filter_and_keyword(self, client):
        await client.post("/api/notifications/templates", json={
            "code": "tpl-search", "name": "告警通知", "channel_type": "push",
            "body_template": "服务异常",
        }, headers=H)
        resp = await client.get(
            "/api/notifications/templates?channel_type=push&keyword=告警", headers=H,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_update_template(self, client):
        create = await client.post("/api/notifications/templates", json={
            "code": "tpl-upd", "channel_type": "email", "body_template": "旧正文",
        }, headers=H)
        template_id = create.json()["id"]
        resp = await client.patch(f"/api/notifications/templates/{template_id}", json={
            "body_template": "新正文", "description": "更新说明",
        }, headers=H)
        assert resp.status_code == 200
        assert resp.json()["body_template"] == "新正文"
        assert resp.json()["description"] == "更新说明"

    async def test_get_template_not_found(self, client):
        resp = await client.get("/api/notifications/templates/nonexistent", headers=H)
        assert resp.status_code == 404

    async def test_delete_template(self, client):
        create = await client.post("/api/notifications/templates", json={
            "code": "tpl-del", "channel_type": "email", "body_template": "x",
        }, headers=H)
        template_id = create.json()["id"]
        resp = await client.delete(f"/api/notifications/templates/{template_id}", headers=H)
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True


# ═══════════════════════════════════════════════════════════
# 通知发送记录
# ═══════════════════════════════════════════════════════════

class TestNotificationRecord:
    async def _make_channel(self, client, name="rec-ch"):
        resp = await client.post("/api/notifications/channels", json={
            "name": name, "channel_type": "email", "config": "{}",
        }, headers=H)
        return resp.json()["id"]

    async def test_send_success_pending(self, client):
        channel_id = await self._make_channel(client, "rec-send")
        resp = await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "template_code": "tpl-welcome",
            "recipient": "user@example.com", "subject": "标题", "body": "正文",
        }, headers=H)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["recipient"] == "user@example.com"

    async def test_send_channel_not_found(self, client):
        resp = await client.post("/api/notifications/records", json={
            "channel_id": "no-such", "recipient": "a@b.com",
        }, headers=H)
        assert resp.status_code == 404

    async def test_send_disabled_channel_rejected(self, client):
        channel_id = await self._make_channel(client, "rec-disabled")
        await client.patch(f"/api/notifications/channels/{channel_id}/status", json={
            "status": "disabled",
        }, headers=H)
        resp = await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "recipient": "a@b.com",
        }, headers=H)
        assert resp.status_code == 409

    async def test_deliver_sent(self, client):
        channel_id = await self._make_channel(client, "rec-deliver")
        send = await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "recipient": "ok@example.com",
        }, headers=H)
        record_id = send.json()["id"]
        resp = await client.post(f"/api/notifications/records/{record_id}/deliver", json={
            "status": "sent",
        }, headers=H)
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"
        assert resp.json()["sent_at"] is not None

    async def test_deliver_failed_with_error(self, client):
        channel_id = await self._make_channel(client, "rec-fail")
        send = await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "recipient": "bad",
        }, headers=H)
        record_id = send.json()["id"]
        resp = await client.post(f"/api/notifications/records/{record_id}/deliver", json={
            "status": "failed", "error": "收件人格式错误",
        }, headers=H)
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"
        assert "收件人" in resp.json()["error"]

    async def test_deliver_invalid_transition_rejected(self, client):
        channel_id = await self._make_channel(client, "rec-state")
        send = await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "recipient": "x@y.com",
        }, headers=H)
        record_id = send.json()["id"]
        await client.post(f"/api/notifications/records/{record_id}/deliver", json={
            "status": "sent",
        }, headers=H)
        # 终态 sent 不可再次迁移
        resp = await client.post(f"/api/notifications/records/{record_id}/deliver", json={
            "status": "failed",
        }, headers=H)
        assert resp.status_code == 409

    async def test_list_records_filter_and_keyword(self, client):
        channel_id = await self._make_channel(client, "rec-list")
        await client.post("/api/notifications/records", json={
            "channel_id": channel_id, "recipient": "search@example.com",
            "subject": "月度账单",
        }, headers=H)
        resp = await client.get(
            f"/api/notifications/records?channel_id={channel_id}&keyword=账单", headers=H,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_send_requires_token(self, client):
        resp = await client.post("/api/notifications/records", json={
            "channel_id": "any", "recipient": "a@b.com",
        }, headers=BAD)
        assert resp.status_code in (401, 403)

    async def test_get_record_not_found(self, client):
        resp = await client.get("/api/notifications/records/nonexistent", headers=H)
        assert resp.status_code == 404
