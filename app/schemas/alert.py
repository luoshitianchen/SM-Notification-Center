"""告警接入相关 Pydantic 模型。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AlertIngest(BaseModel):
    """外部服务上报的告警事件。"""

    source: str = Field(min_length=1, max_length=80)
    severity: Literal["critical", "warning", "info"] = "warning"
    summary: str = Field(min_length=1, max_length=500)
    details: str = Field(default="", max_length=2000)


class AlertIngestResponse(BaseModel):
    status: str
    alert_id: str
    severity: str
