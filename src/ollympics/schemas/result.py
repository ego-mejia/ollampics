from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AttemptStatus = Literal["success", "fail", "error", "timeout"]


class AttemptResult(BaseModel):
    status: AttemptStatus
    wall_time_s: float
    ttft_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    tps_decode: float | None = None
    peak_vram_mb: int | None = None
    avg_watts: float | None = None
    error_type: str | None = None
    error_message: str | None = None
    transcript: dict[str, Any] = Field(default_factory=dict)
