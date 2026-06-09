"""Compare two MODELS head-to-head across all their runs.

For every task either model has been measured on, we take the LATEST attempt
per (model, task) — highest run_id wins — and report the per-task metrics
side by side. A run can include several models, so comparing by `run` is
ambiguous; comparing by `model` is what the user actually wants.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ollympics.db.models import Attempt, Model, TaskRow
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


class ModelBrief(BaseModel):
    """Aggregate view of one model across all its attempts."""
    name: str
    n_runs: int
    n_tasks: int
    n_successes: int
    last_seen: datetime | None


class CompareResponse(BaseModel):
    model_a: ModelBrief
    model_b: ModelBrief
    entries: list[CompareEntry]
    summary: dict[str, Any]


def _latest_attempts_for_model(
    session, model_name: str
) -> tuple[dict[int, Attempt], dict[int, tuple[str, str]], set[int], datetime | None]:
    """Returns (latest_attempt_by_task_id, task_meta, run_ids, last_seen).

    For each task the model has been attempted on, pick the attempt from the
    highest run_id (ties broken by lowest try_n).
    """
    rows = session.execute(
        select(Attempt, TaskRow)
        .join(Model, Attempt.model_id == Model.id)
        .join(TaskRow, Attempt.task_id == TaskRow.id)
        .where(Model.name == model_name)
    ).all()

    best: dict[int, Attempt] = {}
    task_meta: dict[int, tuple[str, str]] = {}
    run_ids: set[int] = set()
    last_seen: datetime | None = None

    for a, t in rows:
        task_meta[t.id] = (t.task_id, t.suite)
        run_ids.add(a.run_id)
        if a.created_at and (last_seen is None or a.created_at > last_seen):
            last_seen = a.created_at
        current = best.get(t.id)
        if current is None or a.run_id > current.run_id or (
            a.run_id == current.run_id and a.try_n < current.try_n
        ):
            best[t.id] = a
    return best, task_meta, run_ids, last_seen


def _build_model_brief(session, model_name: str) -> ModelBrief:
    if session.scalar(select(Model).where(Model.name == model_name)) is None:
        raise HTTPException(404, f"model {model_name} no existe")
    best, _meta, run_ids, last_seen = _latest_attempts_for_model(session, model_name)
    n_succ = sum(1 for a in best.values() if a.status == "success")
    return ModelBrief(
        name=model_name,
        n_runs=len(run_ids),
        n_tasks=len(best),
        n_successes=n_succ,
        last_seen=last_seen,
    )


@router.get("/compare", response_model=CompareResponse)
async def compare(model_a: str, model_b: str) -> CompareResponse:
    if model_a == model_b:
        raise HTTPException(400, "model_a y model_b deben ser distintos")
    with session_scope() as session:
        brief_a = _build_model_brief(session, model_a)
        brief_b = _build_model_brief(session, model_b)

        best_a, meta_a, _, _ = _latest_attempts_for_model(session, model_a)
        best_b, meta_b, _, _ = _latest_attempts_for_model(session, model_b)

        task_meta: dict[int, tuple[str, str]] = {**meta_a, **meta_b}
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
            model_a=brief_a,
            model_b=brief_b,
            entries=entries,
            summary={
                "a_only_success": a_only_success,
                "b_only_success": b_only_success,
                "both_success": both_success,
                "n_shared_tasks": len(entries),
            },
        )


@router.get("/compare/options", response_model=list[ModelBrief])
async def compare_options() -> list[ModelBrief]:
    """List all models that have at least one attempt, latest-first."""
    with session_scope() as session:
        names = session.scalars(select(Model.name)).all()
        briefs = []
        for n in names:
            best, _m, run_ids, last_seen = _latest_attempts_for_model(session, n)
            if not best:
                continue
            briefs.append(
                ModelBrief(
                    name=n,
                    n_runs=len(run_ids),
                    n_tasks=len(best),
                    n_successes=sum(1 for a in best.values() if a.status == "success"),
                    last_seen=last_seen,
                )
            )
        briefs.sort(key=lambda b: b.last_seen or datetime.min, reverse=True)
        return briefs
