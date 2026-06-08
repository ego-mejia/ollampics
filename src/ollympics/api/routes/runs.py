from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ollympics.core.runner import execute_run
from ollympics.db.models import Attempt, Model, Run, TaskRow
from ollympics.db.session import session_scope
from ollympics.schemas.run import RunConfig

router = APIRouter()


class RunSummary(BaseModel):
    id: int
    created_at: datetime
    status: str
    config: dict[str, Any]
    notes: str | None
    n_attempts: int
    n_successes: int


class AttemptSummary(BaseModel):
    id: int
    model: str
    task_id: str
    try_n: int
    status: str
    tps_decode: float | None
    ttft_ms: int | None
    tokens_in: int | None
    tokens_out: int | None
    peak_vram_mb: int | None
    avg_watts: float | None
    wall_time_s: float | None


class RunDetail(RunSummary):
    attempts: list[AttemptSummary]


@router.get("/runs", response_model=list[RunSummary])
async def list_runs(limit: int = 50) -> list[RunSummary]:
    with session_scope() as session:
        runs = session.scalars(
            select(Run).order_by(Run.id.desc()).limit(limit)
        ).all()
        out: list[RunSummary] = []
        for r in runs:
            attempts = session.scalars(
                select(Attempt).where(Attempt.run_id == r.id)
            ).all()
            successes = sum(1 for a in attempts if a.status == "success")
            out.append(
                RunSummary(
                    id=r.id,
                    created_at=r.created_at,
                    status=r.status,
                    config=r.config_json or {},
                    notes=r.notes,
                    n_attempts=len(attempts),
                    n_successes=successes,
                )
            )
        return out


class RunStatus(BaseModel):
    id: int
    status: str
    n_attempts: int
    n_successes: int


@router.get("/runs/{run_id}/status", response_model=RunStatus)
async def get_run_status(run_id: int) -> RunStatus:
    """Lightweight endpoint for polling — no attempt details."""
    from fastapi import HTTPException
    from sqlalchemy import func

    with session_scope() as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(404, "run no existe")
        total = session.scalar(
            select(func.count(Attempt.id)).where(Attempt.run_id == run_id)
        ) or 0
        successes = session.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.run_id == run_id, Attempt.status == "success"
            )
        ) or 0
        return RunStatus(
            id=run.id, status=run.status, n_attempts=total, n_successes=successes
        )


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: int) -> RunDetail:
    with session_scope() as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(404, "run no existe")
        attempts = session.scalars(
            select(Attempt).where(Attempt.run_id == run_id).order_by(Attempt.id)
        ).all()
        models_by_id = {m.id: m.name for m in session.scalars(select(Model)).all()}
        tasks_by_id = {t.id: t.task_id for t in session.scalars(select(TaskRow)).all()}

        attempt_summaries = [
            AttemptSummary(
                id=a.id,
                model=models_by_id.get(a.model_id, "?"),
                task_id=tasks_by_id.get(a.task_id, "?"),
                try_n=a.try_n,
                status=a.status,
                tps_decode=a.tps_decode,
                ttft_ms=a.ttft_ms,
                tokens_in=a.tokens_in,
                tokens_out=a.tokens_out,
                peak_vram_mb=a.peak_vram_mb,
                avg_watts=a.avg_watts,
                wall_time_s=a.wall_time_s,
            )
            for a in attempts
        ]
        successes = sum(1 for a in attempts if a.status == "success")
        return RunDetail(
            id=run.id,
            created_at=run.created_at,
            status=run.status,
            config=run.config_json or {},
            notes=run.notes,
            n_attempts=len(attempts),
            n_successes=successes,
            attempts=attempt_summaries,
        )


@router.post("/runs", response_model=RunSummary, status_code=202)
async def create_run_endpoint(config: RunConfig) -> RunSummary:
    """Encola una corrida y la ejecuta en background. Devuelve el run inmediatamente.

    The run row is created synchronously so the client can open a WebSocket
    subscription to `/api/runs/{id}/ws` BEFORE the background task starts
    emitting events.
    """
    from ollympics.api.routes.ws import make_broadcast_callback
    from ollympics.db.repo import create_run

    with session_scope() as session:
        run = create_run(session, config.model_dump(), notes=config.notes)
        run_id = run.id
        created_at = run.created_at
        run_status = run.status
        config_json = run.config_json or {}
        notes = run.notes

    callback = make_broadcast_callback(run_id)
    asyncio.create_task(execute_run(config, on_event=callback, run_id=run_id))

    return RunSummary(
        id=run_id,
        created_at=created_at,
        status=run_status,
        config=config_json,
        notes=notes,
        n_attempts=0,
        n_successes=0,
    )


@router.delete("/runs/{run_id}", status_code=204)
async def delete_run(run_id: int) -> None:
    """Delete a run and all of its attempts (judge_evaluations cascade via FK)."""
    from sqlalchemy import delete

    from ollympics.db.models import Attempt

    with session_scope() as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(404, "run no existe")
        # Delete attempts first; judge_evaluations cascade via FK ondelete.
        session.execute(delete(Attempt).where(Attempt.run_id == run_id))
        session.delete(run)
    return None
