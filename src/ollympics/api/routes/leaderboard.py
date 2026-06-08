from __future__ import annotations

from collections import defaultdict
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from ollympics.db.models import Attempt, Model, RuntimeConfigRow, TaskRow
from ollympics.db.session import session_scope

router = APIRouter()


class LeaderboardEntry(BaseModel):
    model: str
    runtime_hash: str
    suite: str
    n_tasks: int
    successes: int
    success_rate: float
    avg_tps: float | None
    avg_ttft_ms: float | None
    avg_tries: float
    peak_vram_mb: int | None


Metric = Literal["success_rate", "avg_tps", "avg_ttft_ms"]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    suite: str | None = Query(None),
    metric: Metric = Query("success_rate"),
) -> list[LeaderboardEntry]:
    with session_scope() as s:
        stmt = (
            select(Attempt, Model, RuntimeConfigRow, TaskRow)
            .join(Model, Attempt.model_id == Model.id)
            .join(RuntimeConfigRow, Attempt.runtime_id == RuntimeConfigRow.id)
            .join(TaskRow, Attempt.task_id == TaskRow.id)
        )
        if suite:
            stmt = stmt.where(TaskRow.suite == suite)

        rows = s.execute(stmt).all()

        # Best attempt per (model, runtime, task): success > fail > error, low try_n wins
        best: dict[tuple[str, str, int], tuple[Attempt, str]] = {}
        attempt_count: dict[tuple[str, str, int], int] = defaultdict(int)
        for a, m, rc, tr in rows:
            key = (m.name, rc.hash, tr.id)
            attempt_count[key] += 1
            current = best.get(key)
            if current is None:
                best[key] = (a, tr.suite)
                continue
            cur_a, _ = current
            if cur_a.status != "success" and a.status == "success":
                best[key] = (a, tr.suite)
            elif cur_a.status == a.status and a.try_n < cur_a.try_n:
                best[key] = (a, tr.suite)

        # Aggregate by (model, runtime, suite)
        groups: dict[tuple[str, str, str], dict] = defaultdict(
            lambda: {
                "n_tasks": 0,
                "successes": 0,
                "tps_sum": 0.0,
                "tps_n": 0,
                "ttft_sum": 0.0,
                "ttft_n": 0,
                "tries_sum": 0,
                "vram_max": 0,
            }
        )
        for key, (a, suite_name) in best.items():
            gk = (key[0], key[1], suite_name)
            g = groups[gk]
            g["n_tasks"] += 1
            if a.status == "success":
                g["successes"] += 1
            if a.tps_decode is not None:
                g["tps_sum"] += a.tps_decode
                g["tps_n"] += 1
            if a.ttft_ms is not None:
                g["ttft_sum"] += a.ttft_ms
                g["ttft_n"] += 1
            g["tries_sum"] += attempt_count[key]
            if a.peak_vram_mb and a.peak_vram_mb > g["vram_max"]:
                g["vram_max"] = a.peak_vram_mb

        entries = [
            LeaderboardEntry(
                model=model_name,
                runtime_hash=runtime_hash,
                suite=suite_name,
                n_tasks=g["n_tasks"],
                successes=g["successes"],
                success_rate=g["successes"] / g["n_tasks"] if g["n_tasks"] else 0.0,
                avg_tps=g["tps_sum"] / g["tps_n"] if g["tps_n"] else None,
                avg_ttft_ms=g["ttft_sum"] / g["ttft_n"] if g["ttft_n"] else None,
                avg_tries=g["tries_sum"] / g["n_tasks"] if g["n_tasks"] else 0.0,
                peak_vram_mb=g["vram_max"] or None,
            )
            for (model_name, runtime_hash, suite_name), g in groups.items()
        ]

        def sort_key(e: LeaderboardEntry):
            if metric == "success_rate":
                return (-e.success_rate, -(e.avg_tps or 0))
            if metric == "avg_tps":
                return (-(e.avg_tps or 0),)
            if metric == "avg_ttft_ms":
                return (e.avg_ttft_ms or 1e18,)
            return (0,)

        entries.sort(key=sort_key)
        return entries
