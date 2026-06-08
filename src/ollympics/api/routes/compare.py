"""GET /api/compare?a=<run_id>&b=<run_id> — side-by-side diff of two runs.

For each unique task across both runs, picks the best attempt (success first,
then lowest try_n) and reports its key metrics. Useful for comparing
quantizations, runtime configs, or different models on the same suite.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ollympics.db.models import Attempt, Model, Run, RuntimeConfigRow, TaskRow
from ollympics.db.session import session_scope

router = APIRouter()


class CompareEntry(BaseModel):
    task_id: str
    suite: str
    a_status: str | None
    a_tps: float | None
    a_ttft_ms: int | None
    a_tokens_out: int | None
    a_wall_s: float | None
    b_status: str | None
    b_tps: float | None
    b_ttft_ms: int | None
    b_tokens_out: int | None
    b_wall_s: float | None


class RunBrief(BaseModel):
    id: int
    created_at: datetime
    status: str
    model: str | None
    runtime_hash: str | None
    num_ctx: int | None
    kv_cache_type: str | None
    notes: str | None
    n_tasks: int
    n_successes: int


class CompareResponse(BaseModel):
    run_a: RunBrief
    run_b: RunBrief
    entries: list[CompareEntry]
    summary: dict[str, Any]


def _best_attempt_per_task(rows: list[tuple[Attempt, TaskRow]]) -> dict[int, Attempt]:
    out: dict[int, Attempt] = {}
    for a, t in rows:
        existing = out.get(t.id)
        if existing is None:
            out[t.id] = a
            continue
        # Prefer success > non-success; then lowest try_n
        if existing.status != "success" and a.status == "success":
            out[t.id] = a
        elif existing.status == a.status and a.try_n < existing.try_n:
            out[t.id] = a
    return out


def _build_run_brief(session, run_id: int) -> RunBrief:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(404, f"run {run_id} no existe")
    rows = session.execute(
        select(Attempt, Model, RuntimeConfigRow, TaskRow)
        .join(Model, Attempt.model_id == Model.id)
        .join(RuntimeConfigRow, Attempt.runtime_id == RuntimeConfigRow.id)
        .join(TaskRow, Attempt.task_id == TaskRow.id)
        .where(Attempt.run_id == run_id)
    ).all()
    best = _best_attempt_per_task([(a, t) for a, _, _, t in rows])
    n_succ = sum(1 for a in best.values() if a.status == "success")
    # Pull single (model, runtime) since one run is typically one combo.
    model_name = None
    runtime_hash = None
    num_ctx = None
    kv = None
    if rows:
        _, m, rc, _ = rows[0]
        model_name = m.name
        runtime_hash = rc.hash
        num_ctx = rc.num_ctx
        kv = rc.kv_cache_type
    return RunBrief(
        id=run.id,
        created_at=run.created_at,
        status=run.status,
        model=model_name,
        runtime_hash=runtime_hash,
        num_ctx=num_ctx,
        kv_cache_type=kv,
        notes=run.notes,
        n_tasks=len(best),
        n_successes=n_succ,
    )


@router.get("/compare", response_model=CompareResponse)
async def compare(a: int, b: int) -> CompareResponse:
    if a == b:
        raise HTTPException(400, "a y b deben ser runs distintos")
    with session_scope() as session:
        brief_a = _build_run_brief(session, a)
        brief_b = _build_run_brief(session, b)

        rows_a = session.execute(
            select(Attempt, TaskRow)
            .join(TaskRow, Attempt.task_id == TaskRow.id)
            .where(Attempt.run_id == a)
        ).all()
        rows_b = session.execute(
            select(Attempt, TaskRow)
            .join(TaskRow, Attempt.task_id == TaskRow.id)
            .where(Attempt.run_id == b)
        ).all()
        best_a = _best_attempt_per_task(rows_a)
        best_b = _best_attempt_per_task(rows_b)

        # Map task IDs (DB row ID) to (task_id, suite)
        task_meta: dict[int, tuple[str, str]] = {}
        for _, t in rows_a + rows_b:
            task_meta[t.id] = (t.task_id, t.suite)

        all_task_ids = set(best_a.keys()) | set(best_b.keys())
        entries: list[CompareEntry] = []
        for tid in sorted(all_task_ids, key=lambda i: task_meta[i][0]):
            task_id_str, suite = task_meta[tid]
            ax = best_a.get(tid)
            bx = best_b.get(tid)
            entries.append(
                CompareEntry(
                    task_id=task_id_str,
                    suite=suite,
                    a_status=ax.status if ax else None,
                    a_tps=ax.tps_decode if ax else None,
                    a_ttft_ms=ax.ttft_ms if ax else None,
                    a_tokens_out=ax.tokens_out if ax else None,
                    a_wall_s=ax.wall_time_s if ax else None,
                    b_status=bx.status if bx else None,
                    b_tps=bx.tps_decode if bx else None,
                    b_ttft_ms=bx.ttft_ms if bx else None,
                    b_tokens_out=bx.tokens_out if bx else None,
                    b_wall_s=bx.wall_time_s if bx else None,
                )
            )

        # Summary deltas
        a_only_success = sum(
            1 for e in entries if e.a_status == "success" and e.b_status != "success"
        )
        b_only_success = sum(
            1 for e in entries if e.b_status == "success" and e.a_status != "success"
        )
        both_success = sum(
            1 for e in entries if e.a_status == "success" and e.b_status == "success"
        )
        return CompareResponse(
            run_a=brief_a,
            run_b=brief_b,
            entries=entries,
            summary={
                "a_only_success": a_only_success,
                "b_only_success": b_only_success,
                "both_success": both_success,
                "n_shared_tasks": len(entries),
            },
        )


@router.get("/compare/options", response_model=list[RunBrief])
async def compare_options(limit: int = 30) -> list[RunBrief]:
    """List recent runs as candidates for the A/B picker."""
    with session_scope() as session:
        runs = session.scalars(
            select(Run).order_by(Run.id.desc()).limit(limit)
        ).all()
        return [_build_run_brief(session, r.id) for r in runs]
