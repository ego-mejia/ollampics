from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    harness_sha: Mapped[str] = mapped_column(String(64), nullable=False, default="dev")
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempts: Mapped[list[Attempt]] = relationship("Attempt", back_populates="run")


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    family: Mapped[str | None] = mapped_column(String(128))
    size_params_b: Mapped[float | None] = mapped_column(Float)
    quantization: Mapped[str | None] = mapped_column(String(64))
    backend: Mapped[str | None] = mapped_column(String(32))
    size_bytes: Mapped[int | None] = mapped_column(Integer)


class RuntimeConfigRow(Base):
    __tablename__ = "runtime_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    num_ctx: Mapped[int] = mapped_column(Integer, nullable=False)
    kv_cache_type: Mapped[str] = mapped_column(String(16), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    num_gpu: Mapped[int | None] = mapped_column(Integer)
    num_thread: Mapped[int | None] = mapped_column(Integer)
    extra_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class TaskRow(Base):
    __tablename__ = "tasks_registry"
    __table_args__ = (UniqueConstraint("task_id", "version", name="uq_task_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    suite: Mapped[str] = mapped_column(String(64), nullable=False)
    spec_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    judge_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "model_id", "runtime_id", "task_id", "try_n", name="uq_attempt"
        ),
        Index("idx_attempts_model_task", "model_id", "task_id"),
        Index("idx_attempts_run", "run_id"),
        Index("idx_attempts_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    runtime_id: Mapped[int] = mapped_column(ForeignKey("runtime_configs.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks_registry.id"), nullable=False)
    try_n: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    wall_time_s: Mapped[float | None] = mapped_column(Float)
    ttft_ms: Mapped[int | None] = mapped_column(Integer)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    tps_decode: Mapped[float | None] = mapped_column(Float)
    peak_vram_mb: Mapped[int | None] = mapped_column(Integer)
    avg_watts: Mapped[float | None] = mapped_column(Float)
    error_type: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    transcript_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped[Run] = relationship("Run", back_populates="attempts")


class JudgeEvaluation(Base):
    __tablename__ = "judge_evaluations"
    __table_args__ = (
        UniqueConstraint("attempt_id", "judge_model", "rubric_name", name="uq_judge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    judge_model: Mapped[str] = mapped_column(String(64), nullable=False)
    rubric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    pass_: Mapped[bool] = mapped_column("pass", Boolean, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
