"""Repository functions for common DB queries used by runner, CLI, and API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ollympics.db.models import (
    Attempt,
    Model,
    Run,
    RuntimeConfigRow,
    TaskRow,
)
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec


def get_or_create_model(session: Session, name: str, size_bytes: int | None = None) -> Model:
    m = session.scalar(select(Model).where(Model.name == name))
    if m is not None:
        return m
    family, *_ = name.partition(":")
    backend = "mlx" if "mlx" in name.lower() else "gguf"
    m = Model(name=name, family=family, backend=backend, size_bytes=size_bytes)
    session.add(m)
    session.flush()
    return m


def get_or_create_runtime(session: Session, rc: RuntimeConfig) -> RuntimeConfigRow:
    h = rc.hash()
    row = session.scalar(select(RuntimeConfigRow).where(RuntimeConfigRow.hash == h))
    if row is not None:
        return row
    row = RuntimeConfigRow(
        hash=h,
        num_ctx=rc.num_ctx,
        kv_cache_type=rc.kv_cache_type,
        temperature=rc.temperature,
        seed=rc.seed,
        top_p=rc.top_p,
        num_gpu=rc.num_gpu,
        num_thread=rc.num_thread,
        extra_json=rc.extra or None,
    )
    session.add(row)
    session.flush()
    return row


def get_or_create_task(session: Session, spec: TaskSpec) -> TaskRow:
    row = session.scalar(
        select(TaskRow).where(
            TaskRow.task_id == spec.task_id, TaskRow.version == spec.version
        )
    )
    if row is not None:
        return row
    judge_required = _spec_uses_judge(spec)
    row = TaskRow(
        task_id=spec.task_id,
        version=spec.version,
        suite=spec.suite,
        spec_json=spec.model_dump(by_alias=True),
        judge_required=judge_required,
    )
    session.add(row)
    session.flush()
    return row


def _spec_uses_judge(spec: TaskSpec) -> bool:
    stack: list[Any] = [spec.verifier]
    while stack:
        v = stack.pop()
        t = getattr(v, "type", None)
        if t == "llm_judge":
            return True
        if t == "composite":
            stack.extend(v.all_of or [])
            stack.extend(v.any_of or [])
    return False


def create_run(session: Session, config_json: dict[str, Any], notes: str | None = None) -> Run:
    run = Run(status="running", harness_sha="dev", config_json=config_json, notes=notes)
    session.add(run)
    session.flush()
    return run


def mark_run_finished(session: Session, run_id: int, status: str = "done") -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.status = status


def already_succeeded(
    session: Session, model_id: int, runtime_id: int, task_id: int
) -> bool:
    stmt = select(Attempt.id).where(
        Attempt.model_id == model_id,
        Attempt.runtime_id == runtime_id,
        Attempt.task_id == task_id,
        Attempt.status == "success",
    )
    return session.scalar(stmt) is not None


def insert_attempt(
    session: Session,
    *,
    run_id: int,
    model_id: int,
    runtime_id: int,
    task_id: int,
    try_n: int,
    status: str,
    started_at: datetime,
    finished_at: datetime,
    wall_time_s: float,
    ttft_ms: int | None,
    tokens_in: int | None,
    tokens_out: int | None,
    tps_decode: float | None,
    peak_vram_mb: int | None,
    avg_watts: float | None,
    error_type: str | None,
    error_message: str | None,
    transcript_json: dict[str, Any],
) -> Attempt:
    a = Attempt(
        run_id=run_id,
        model_id=model_id,
        runtime_id=runtime_id,
        task_id=task_id,
        try_n=try_n,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        wall_time_s=wall_time_s,
        ttft_ms=ttft_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tps_decode=tps_decode,
        peak_vram_mb=peak_vram_mb,
        avg_watts=avg_watts,
        error_type=error_type,
        error_message=error_message,
        transcript_json=transcript_json,
    )
    session.add(a)
    session.flush()
    return a
