"""End-to-end runner: takes a RunConfig, iterates modelos × runtimes × suites × tasks,
calls Ollama, verifies, persists.

Skips tasks that already have a successful attempt for (model, runtime, task) — that's
how idempotency works. The first re-run of the same set is a no-op.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from ollympics.core.judge import find_llm_judges, verify
from ollympics.core.judge_llm import evaluate_with_judge
from ollympics.core.metrics import MetricsSampler
from ollympics.core.ollama import OllamaClient
from ollympics.db.repo import (
    already_succeeded,
    create_run,
    get_or_create_model,
    get_or_create_runtime,
    get_or_create_task,
    insert_attempt,
    mark_run_finished,
)
from ollympics.db.session import session_scope
from ollympics.schemas.result import AttemptResult
from ollympics.schemas.run import RunConfig
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec
from ollympics.suites.loader import load_suite
from ollympics.suites.multi_agent.executor import run_multi_agent_task
from ollympics.suites.personal_agent.executor import run_personal_agent_task
from ollympics.suites.planning.executor import run_planning_task
from ollympics.suites.rag.executor import run_rag_task
from ollympics.suites.tool_calling.executor import run_tool_calling_task

if False:  # for type hints only
    from ollympics.core.judge import Verdict  # noqa: F401

EventCallback = Callable[[str, dict[str, Any]], Awaitable[None]] | None


async def _emit(cb: EventCallback, event: str, payload: dict[str, Any]) -> None:
    if cb is not None:
        await cb(event, payload)


async def execute_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    if spec.tools is not None:
        return await _execute_tool_calling_task(client, model_name, runtime, spec)
    if spec.rag is not None:
        return await _execute_rag_task(client, model_name, runtime, spec)
    if spec.planning is not None:
        return await _execute_planning_task(client, model_name, runtime, spec)
    if spec.personal_agent is not None:
        return await _execute_personal_agent_task(client, model_name, runtime, spec)
    if spec.multi_agent is not None:
        return await _execute_multi_agent_task(client, model_name, runtime, spec)
    return await _execute_generate_task(client, model_name, runtime, spec)


async def _execute_multi_agent_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
        "iterations": spec.multi_agent.iterations if spec.multi_agent else 1,
    }
    sampler = MetricsSampler(model_name)
    async with sampler:
        result = await run_multi_agent_task(client, model_name, runtime, spec)

    transcript["research_notes"] = result.research_notes
    transcript["critique"] = result.critique
    transcript["final_report"] = result.final_report
    transcript["role_transcripts"] = result.transcripts
    transcript["n_turns"] = result.n_turns

    if result.error and not result.final_report:
        return AttemptResult(
            status="error",
            wall_time_s=result.wall_time_s,
            ttft_ms=result.ttft_ms,
            tokens_in=result.tokens_in or None,
            tokens_out=result.tokens_out or None,
            tps_decode=result.tps_decode,
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            error_type="multi_agent_error",
            error_message=result.error,
            transcript=transcript,
        )

    # Sync + async LLM judge merge (same pattern as RAG/Planning).
    judges = find_llm_judges(spec.verifier)
    llm_results: dict[int, Any] = {}
    if judges:
        with session_scope() as session:
            for j in judges:
                from ollympics.core.judge import Verdict as V
                from ollympics.core.judge_llm import evaluate_with_judge as _ewj

                res = await _ewj(
                    session,
                    attempt_id=-1,
                    rubric=j.rubric,
                    threshold=j.pass_threshold,
                    response_text=result.final_report,
                    question=spec.prompt.user,
                    key_facts=[],
                    context_used=result.research_notes + "\n\n" + result.critique,
                    judge_model=j.judge_model,
                )
                llm_results[id(j)] = V(
                    passed=res.passed,
                    reason=res.rationale,
                    details={"score": res.score, "model": res.judge_model},
                )

    verdict = verify(result.final_report, spec.verifier, llm_results=llm_results)
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=result.wall_time_s,
        ttft_ms=result.ttft_ms,
        tokens_in=result.tokens_in or None,
        tokens_out=result.tokens_out or None,
        tps_decode=result.tps_decode,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def _execute_personal_agent_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
    }
    sampler = MetricsSampler(model_name)
    async with sampler:
        result = await run_personal_agent_task(client, model_name, runtime, spec)

    pa_summary = {
        "recall_rate": result.recall_rate,
        "tool_fidelity": result.tool_fidelity,
        "closing_summary_ok": result.closing_summary_ok,
        "n_turns": result.n_turns,
        "ttft_first_ms": result.ttft_first_ms,
        "ttft_last_ms": result.ttft_last_ms,
        "ttft_drift_ms": (
            (result.ttft_last_ms or 0) - (result.ttft_first_ms or 0)
            if result.ttft_first_ms is not None
            else None
        ),
        "tps_first": result.tps_first,
        "tps_last": result.tps_last,
    }
    transcript.update(pa_summary)
    transcript["conversation"] = result.transcript
    transcript["per_turn_metrics"] = result.per_turn_metrics
    transcript["recall_results"] = result.recall_results
    transcript["tool_call_results"] = result.tool_call_results

    if result.error and result.n_turns == 0:
        return AttemptResult(
            status="error",
            wall_time_s=result.wall_time_s,
            tokens_in=result.tokens_in_total or None,
            tokens_out=result.tokens_out_total or None,
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            error_type="personal_agent_error",
            error_message=result.error,
            transcript=transcript,
        )

    verdict = verify(
        "",
        spec.verifier,
        pa_result=pa_summary,
    )
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=result.wall_time_s,
        ttft_ms=result.ttft_first_ms,
        tokens_in=result.tokens_in_total or None,
        tokens_out=result.tokens_out_total or None,
        tps_decode=result.tps_last,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def _execute_planning_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
        "planning_mode": spec.planning.mode if spec.planning else None,
    }
    sampler = MetricsSampler(model_name)
    async with sampler:
        result = await run_planning_task(client, model_name, runtime, spec)

    transcript["plan"] = result.plan
    transcript["step_results"] = result.step_results
    transcript["final_answer"] = result.final_answer
    transcript["n_turns"] = result.n_turns

    if result.error and not result.final_answer:
        return AttemptResult(
            status="error",
            wall_time_s=result.wall_time_s,
            ttft_ms=result.ttft_ms,
            tokens_in=result.tokens_in or None,
            tokens_out=result.tokens_out or None,
            tps_decode=result.tps_decode,
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            error_type="planning_error",
            error_message=result.error,
            transcript=transcript,
        )

    # Two-phase verify: sync determinista + async LLM judges (mismo patrón que RAG).
    judges = find_llm_judges(spec.verifier)
    llm_results: dict[int, Any] = {}
    if judges:
        with session_scope() as session:
            for j in judges:
                from ollympics.core.judge import Verdict as V
                from ollympics.core.judge_llm import evaluate_with_judge as _ewj

                res = await _ewj(
                    session,
                    attempt_id=-1,
                    rubric=j.rubric,
                    threshold=j.pass_threshold,
                    response_text=result.final_answer,
                    question=spec.prompt.user,
                    key_facts=[],
                    context_used="\n\n".join(result.step_results),
                    judge_model=j.judge_model,
                )
                llm_results[id(j)] = V(
                    passed=res.passed,
                    reason=res.rationale,
                    details={"score": res.score, "model": res.judge_model},
                )

    verdict = verify(result.final_answer, spec.verifier, llm_results=llm_results)
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=result.wall_time_s,
        ttft_ms=result.ttft_ms,
        tokens_in=result.tokens_in or None,
        tokens_out=result.tokens_out or None,
        tps_decode=result.tps_decode,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def _execute_rag_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
        "rag_top_k": spec.rag.top_k if spec.rag else None,
    }
    sampler = MetricsSampler(model_name)
    async with sampler:
        result = await run_rag_task(client, model_name, runtime, spec)

    transcript["retrieved_chunks"] = result.retrieved_chunks
    transcript["context_used"] = result.context_used
    transcript["retrieval_recall_at_k"] = result.retrieval_recall_at_k
    transcript["answer"] = result.answer

    if result.error and not result.answer:
        return AttemptResult(
            status="error",
            wall_time_s=result.wall_time_s,
            ttft_ms=result.ttft_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            tps_decode=result.tps_decode,
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            error_type="rag_error",
            error_message=result.error,
            transcript=transcript,
        )

    # Two-phase verify: sync first (regex/exact/etc.), then async for LLM judges.
    judges = find_llm_judges(spec.verifier)
    llm_results: dict[int, Any] = {}
    if judges:
        # Need the attempt_id for cache; insert a preliminary row, then update.
        # Simpler approach: use a temp negative id for cache key during this run.
        # We persist judge_evaluations after the attempt is inserted; for now,
        # call the judge without caching by passing attempt_id=-1.
        with session_scope() as session:
            for j in judges:
                from ollympics.core.judge_llm import evaluate_with_judge as _ewj

                res = await _ewj(
                    session,
                    attempt_id=-1,
                    rubric=j.rubric,
                    threshold=j.pass_threshold,
                    response_text=result.answer,
                    question=spec.prompt.user,
                    key_facts=[],
                    context_used=result.context_used,
                    judge_model=j.judge_model,
                )
                from ollympics.core.judge import Verdict as V

                llm_results[id(j)] = V(
                    passed=res.passed,
                    reason=res.rationale,
                    details={"score": res.score, "model": res.judge_model},
                )

    verdict = verify(
        result.answer,
        spec.verifier,
        llm_results=llm_results,
    )
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=result.wall_time_s,
        ttft_ms=result.ttft_ms,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        tps_decode=result.tps_decode,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def _execute_generate_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    started = datetime.utcnow()
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
    }
    sampler = MetricsSampler(model_name)
    try:
        async with sampler:
            gen = await asyncio.wait_for(
                client.generate(
                    model=model_name,
                    prompt=spec.prompt.user,
                    system=spec.prompt.system,
                    options=runtime.ollama_options(),
                    timeout_s=spec.timeout_s + 5,
                ),
                timeout=spec.timeout_s + 10,
            )
    except asyncio.TimeoutError:
        elapsed = (datetime.utcnow() - started).total_seconds()
        return AttemptResult(
            status="timeout",
            wall_time_s=elapsed,
            error_type="timeout",
            error_message=f"task timeout after {spec.timeout_s}s",
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            transcript=transcript,
        )
    except Exception as e:
        elapsed = (datetime.utcnow() - started).total_seconds()
        return AttemptResult(
            status="error",
            wall_time_s=elapsed,
            error_type=type(e).__name__,
            error_message=str(e),
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            transcript=transcript,
        )

    transcript["response"] = gen.text
    transcript["ollama_final"] = gen.raw_final

    verdict = verify(gen.text, spec.verifier)
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=gen.wall_time_s,
        ttft_ms=gen.ttft_ms,
        tokens_in=gen.tokens_in,
        tokens_out=gen.tokens_out,
        tps_decode=gen.tps_decode,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def _execute_tool_calling_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> AttemptResult:
    transcript: dict[str, Any] = {
        "prompt": {"system": spec.prompt.system, "user": spec.prompt.user},
        "tools_enabled": spec.tools.enabled if spec.tools else [],
    }
    sampler = MetricsSampler(model_name)
    async with sampler:
        result = await run_tool_calling_task(client, model_name, runtime, spec)

    transcript["trace"] = result.trace
    transcript["final_message"] = result.final_message
    transcript["n_turns"] = result.n_turns
    transcript["format_errors"] = result.format_errors
    if result.error:
        transcript["executor_error"] = result.error

    if result.error and not result.trace and not result.final_message:
        return AttemptResult(
            status="error",
            wall_time_s=result.wall_time_s,
            ttft_ms=result.ttft_ms,
            tokens_in=result.tokens_in or None,
            tokens_out=result.tokens_out or None,
            tps_decode=result.tps_decode,
            peak_vram_mb=sampler.peak_vram_mb,
            avg_watts=sampler.avg_watts,
            error_type="executor_error",
            error_message=result.error,
            transcript=transcript,
        )

    verdict = verify(
        result.final_message,
        spec.verifier,
        trace=result.trace,
        format_errors=result.format_errors,
    )
    transcript["verdict"] = {"reason": verdict.reason, "details": verdict.details}

    return AttemptResult(
        status="success" if verdict.passed else "fail",
        wall_time_s=result.wall_time_s,
        ttft_ms=result.ttft_ms,
        tokens_in=result.tokens_in or None,
        tokens_out=result.tokens_out or None,
        tps_decode=result.tps_decode,
        peak_vram_mb=sampler.peak_vram_mb,
        avg_watts=sampler.avg_watts,
        error_type=None if verdict.passed else "wrong_answer",
        error_message=None if verdict.passed else verdict.reason,
        transcript=transcript,
    )


async def execute_run(
    config: RunConfig,
    *,
    on_event: EventCallback = None,
    run_id: int | None = None,
) -> int:
    """Orchestrates a full benchmark run. Returns the run_id.

    If `run_id` is provided, skips creating the Run row (caller already did so —
    useful when the API needs to return the ID to a WebSocket subscriber before
    the background task starts emitting events).
    """
    if run_id is None:
        with session_scope() as session:
            run = create_run(session, config.model_dump(), notes=config.notes)
            run_id = run.id
    await _emit(on_event, "run.started", {"run_id": run_id})

    client = OllamaClient()

    try:
        for model_name in config.models:
            await _emit(on_event, "model.started", {"model": model_name})

            for runtime in config.runtime_configs:
                try:
                    await client.warmup(model_name, options=runtime.ollama_options())
                except Exception as e:
                    await _emit(
                        on_event,
                        "log",
                        {"level": "warn", "message": f"warmup falló para {model_name}: {e}"},
                    )

                for suite_name in config.suites:
                    specs = load_suite(suite_name)
                    await _emit(
                        on_event,
                        "suite.started",
                        {"model": model_name, "suite": suite_name, "n_tasks": len(specs)},
                    )

                    for spec in specs:
                        with session_scope() as session:
                            model_row = get_or_create_model(session, model_name)
                            runtime_row = get_or_create_runtime(session, runtime)
                            task_row = get_or_create_task(session, spec)
                            if already_succeeded(
                                session, model_row.id, runtime_row.id, task_row.id
                            ):
                                await _emit(
                                    on_event,
                                    "task.skipped",
                                    {"task_id": spec.task_id, "reason": "already_succeeded"},
                                )
                                continue
                            model_id, runtime_id, task_id_row = (
                                model_row.id,
                                runtime_row.id,
                                task_row.id,
                            )

                        for try_n in range(1, spec.max_tries + 1):
                            await _emit(
                                on_event,
                                "task.started",
                                {"task_id": spec.task_id, "try_n": try_n},
                            )
                            started_at = datetime.utcnow()
                            result = await execute_task(client, model_name, runtime, spec)
                            finished_at = datetime.utcnow()

                            with session_scope() as session:
                                insert_attempt(
                                    session,
                                    run_id=run_id,
                                    model_id=model_id,
                                    runtime_id=runtime_id,
                                    task_id=task_id_row,
                                    try_n=try_n,
                                    status=result.status,
                                    started_at=started_at,
                                    finished_at=finished_at,
                                    wall_time_s=result.wall_time_s,
                                    ttft_ms=result.ttft_ms,
                                    tokens_in=result.tokens_in,
                                    tokens_out=result.tokens_out,
                                    tps_decode=result.tps_decode,
                                    peak_vram_mb=result.peak_vram_mb,
                                    avg_watts=result.avg_watts,
                                    error_type=result.error_type,
                                    error_message=result.error_message,
                                    transcript_json=result.transcript,
                                )

                            await _emit(
                                on_event,
                                "task.finished",
                                {
                                    "task_id": spec.task_id,
                                    "try_n": try_n,
                                    "status": result.status,
                                    "tps_decode": result.tps_decode,
                                    "ttft_ms": result.ttft_ms,
                                },
                            )

                            if result.status == "success":
                                break

                    await _emit(
                        on_event,
                        "suite.finished",
                        {"model": model_name, "suite": suite_name},
                    )

            await _emit(on_event, "model.finished", {"model": model_name})
            try:
                await client.stop(model_name)
            except Exception:
                pass
    finally:
        with session_scope() as session:
            mark_run_finished(session, run_id, "done")
        await _emit(on_event, "run.finished", {"run_id": run_id})

    return run_id
