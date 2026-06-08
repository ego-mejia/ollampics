from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ollympics.db.models import Attempt, Model, TaskRow
from ollympics.db.session import session_scope

router = APIRouter()


class AttemptDetail(BaseModel):
    id: int
    run_id: int
    model: str
    task_id: str
    try_n: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    wall_time_s: float | None
    ttft_ms: int | None
    tokens_in: int | None
    tokens_out: int | None
    tps_decode: float | None
    peak_vram_mb: int | None
    avg_watts: float | None
    error_type: str | None
    error_message: str | None
    transcript: dict[str, Any]


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
async def get_attempt(attempt_id: int) -> AttemptDetail:
    with session_scope() as session:
        a = session.get(Attempt, attempt_id)
        if a is None:
            raise HTTPException(404, "attempt no existe")
        model = session.get(Model, a.model_id)
        task = session.get(TaskRow, a.task_id)
        return AttemptDetail(
            id=a.id,
            run_id=a.run_id,
            model=model.name if model else "?",
            task_id=task.task_id if task else "?",
            try_n=a.try_n,
            status=a.status,
            started_at=a.started_at,
            finished_at=a.finished_at,
            wall_time_s=a.wall_time_s,
            ttft_ms=a.ttft_ms,
            tokens_in=a.tokens_in,
            tokens_out=a.tokens_out,
            tps_decode=a.tps_decode,
            peak_vram_mb=a.peak_vram_mb,
            avg_watts=a.avg_watts,
            error_type=a.error_type,
            error_message=a.error_message,
            transcript=a.transcript_json or {},
        )
