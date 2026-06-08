"""Loads tasks/rag/qa.yaml into a list of TaskSpec instances."""

from __future__ import annotations

from pathlib import Path

import yaml

from ollympics.core.config import settings
from ollympics.schemas.qa import QAEntry
from ollympics.schemas.rag import RagContextSpec
from ollympics.schemas.task import PromptSpec, TaskSpec
from ollympics.schemas.verifier import (
    CompositeVerifier,
    ExactMatchVerifier,
    LLMJudgeVerifier,
    RegexVerifier,
    Verifier,
)

RAG_SYSTEM_PROMPT = (
    "Eres un asistente que responde usando SOLO el contexto recuperado. "
    "Si la respuesta no está en el contexto, dilo explícitamente "
    "(\"No lo sé\" o \"No está en el contexto\"). No inventes información."
)


def load_rag_tasks(tasks_dir: Path | None = None) -> list[TaskSpec]:
    base = (tasks_dir or settings.tasks_dir) / "rag"
    qa_path = base / "qa.yaml"
    if not qa_path.exists():
        return []
    raw = yaml.safe_load(qa_path.read_text()) or []
    return [_qa_to_task(QAEntry(**e)) for e in raw]


def _qa_to_task(qa: QAEntry) -> TaskSpec:
    return TaskSpec(
        task_id=qa.qa_id,
        version=1,
        suite="rag",
        description=qa.question,
        max_tries=2,
        timeout_s=120,
        prompt=PromptSpec(system=RAG_SYSTEM_PROMPT, user=qa.question),
        verifier=_verifier_for(qa),
        rag=RagContextSpec(
            top_k=4,
            expected_chunks=qa.source_chunks,
            out_of_corpus=(qa.tier == "out_of_corpus"),
        ),
    )


def _verifier_for(qa: QAEntry) -> Verifier:
    if qa.tier == "factual_single_doc":
        # Accept any of expected_answer / key_facts (fuzzy substring).
        candidates: list[str] = []
        if qa.expected_answer:
            candidates.append(qa.expected_answer)
        candidates.extend(qa.key_facts[:5])
        if not candidates:
            return RegexVerifier(type="regex", pattern=".+")
        return ExactMatchVerifier(
            type="exact_match",
            expected=candidates,
            case_sensitive=False,
            fuzzy=True,
        )
    if qa.tier == "multi_doc_synthesis":
        return LLMJudgeVerifier(
            type="llm_judge",
            rubric=qa.judge_rubric or "rag_open_synthesis_v1",
            pass_threshold=0.7,
        )
    # out_of_corpus
    return CompositeVerifier(
        type="composite",
        all_of=[
            LLMJudgeVerifier(
                type="llm_judge",
                rubric=qa.judge_rubric or "rag_honest_refusal_v1",
                pass_threshold=0.7,
            ),
        ],
    )
