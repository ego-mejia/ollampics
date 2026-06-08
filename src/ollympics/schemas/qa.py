from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

QATier = Literal["factual_single_doc", "multi_doc_synthesis", "out_of_corpus"]


class QAEntry(BaseModel):
    """One entry from tasks/rag/qa.yaml.

    The loader converts each QAEntry into a TaskSpec at runtime; we don't ship
    50 individual YAML files.
    """

    qa_id: str
    tier: QATier
    question: str
    expected_answer: str | None = None
    key_facts: list[str] = Field(default_factory=list)
    source_chunks: list[str] = Field(default_factory=list)
    judge_rubric: str | None = None
