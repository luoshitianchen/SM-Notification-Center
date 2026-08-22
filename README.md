# SM Notification Center

企业通知中心：邮件、短信、企业微信和钉钉通知审计。

```powershell
git clone https://github.com/luoshitianchen/SM-Notification-Center.git
cd SM-Notification-Center
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8470
```

接口：`/health`、`/readyz`、`/api/overview`、`/api/items`、`/api/ops/metrics`、`/api/crypto/status`。

内置 TrustedHost、安全响应头、CSP、国密状态接口和容器加固。
