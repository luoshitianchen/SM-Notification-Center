"""告警接入端点测试。"""
from __future__ import annotations

import pytest

H = {"X-Internal-Token": "test-internal-key-12345"}
BAD = {"X-Internal-Token": "wrong"}


@pytest.mark.asyncio
async def test_ingest_alert_post_accepted(client):
    """POST /alerts/ingest 携带有效令牌返回 202（修复原 405 方法不匹配）。"""
    resp = await client.post(
        "/alerts/ingest",
        json={"source": "sm-soc", "severity": "critical", "summary": "磁盘使用率过高"},
        headers=H,
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["severity"] == "critical"
    assert body["alert_id"]


@pytest.mark.asyncio
async def test_ingest_alert_get_not_allowed(client):
    """GET /alerts/ingest 不应被路由注册为该方法（405）。"""
    resp = await client.get("/alerts/ingest", headers=H)
    assert resp.status_code == 405


@pytest.mark.asyncio
async def test_ingest_alert_requires_token(client):
    """无令牌或错误令牌接入告警被拒绝（403）。"""
    payload = {"source": "sm-soc", "severity": "info", "summary": "测试"}
    assert (await client.post("/alerts/ingest", json=payload)).status_code == 403
    assert (await client.post("/alerts/ingest", json=payload, headers=BAD)).status_code == 403
