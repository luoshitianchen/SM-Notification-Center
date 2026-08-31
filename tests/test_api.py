"""SM Notification Center 领域测试：渠道、模板、发送、投递回执与统计。"""

import pytest
from fastapi.testclient import TestClient

from app import base
from app.main import VERSION, app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(base, "internal_api_key", lambda: "TEST")
    base.reset_state()
    from app.main import _init as init_db
    init_db()
    with TestClient(app) as c:
        c.headers["X-Internal-Token"] = "TEST"
        yield c


def test_health_and_version(client):
    r = client.get("/health", headers={"X-Request-Id": "suite-test"})
    assert r.status_code == 200
    assert r.json()["version"] == VERSION


def test_channel_lifecycle(client):
    assert client.post("/api/notifications/channels", json={"name": "alert-email", "channel_type": "email", "config": {"smtp": "smtp.example.com"}}).status_code == 201
    assert client.post("/api/notifications/channels", json={"name": "alert-email", "channel_type": "email"}).status_code == 409
    assert client.get("/api/notifications/channels").json()["total"] == 1


def test_template_render(client):
    client.post("/api/notifications/channels", json={"name": "web", "channel_type": "webhook"})
    client.post("/api/notifications/templates", json={"name": "order", "channel_type": "webhook", "body": "订单 {{order_id}} 已创建"})
    sent = client.post("/api/notifications/send", json={"channel": "web", "template": "order", "recipient": "ops-webhook", "payload": {"order_id": "A-100"}})
    assert sent.status_code == 201
    assert sent.json()["status"] == "delivered"
    body = client.get(f"/api/notifications/{sent.json()['id']}").json()["body"]
    assert body == "订单 A-100 已创建"


def test_send_without_template(client):
    client.post("/api/notifications/channels", json={"name": "mail", "channel_type": "email"})
    sent = client.post("/api/notifications/send", json={"channel": "mail", "recipient": "u@example.com", "subject": "通知", "body": "内容"})
    assert sent.json()["status"] == "sent"
    assert client.get("/api/notifications").json()["total"] == 1


def test_send_validation(client):
    assert client.post("/api/notifications/send", json={"channel": "ghost", "recipient": "x"}).status_code == 404
    client.post("/api/notifications/channels", json={"name": "mail2", "channel_type": "email"})
    assert client.post("/api/notifications/send", json={"channel": "mail2", "template": "nope", "recipient": "x"}).status_code == 404


def test_retry(client):
    client.post("/api/notifications/channels", json={"name": "mail3", "channel_type": "email"})
    notif_id = client.post("/api/notifications/send", json={"channel": "mail3", "recipient": "r", "subject": "s", "body": "b"}).json()["id"]
    assert client.post(f"/api/notifications/{notif_id}/retry").json()["status"] == "sent"


def test_stats(client):
    client.post("/api/notifications/channels", json={"name": "mail4", "channel_type": "email"})
    client.post("/api/notifications/send", json={"channel": "mail4", "recipient": "r", "subject": "s", "body": "b"})
    stats = client.get("/api/notifications/stats").json()
    assert stats["sent"] == 1


def test_manifest_and_crypto(client):
    assert client.get("/api/integration/manifest").json()["version"] == VERSION
    enc = client.post("/api/crypto/encrypt", json={"value": "secret"}).json()["ciphertext"]
    assert client.post("/api/crypto/decrypt", json={"value": enc}).json()["plaintext"] == "secret"


def test_write_requires_auth(client):
    del client.headers["X-Internal-Token"]
    assert client.post("/api/notifications/channels", json={"name": "c", "channel_type": "email"}).status_code == 401
