from __future__ import annotations

from pydantic import BaseModel, Field


class RagContextSpec(BaseModel):
    """Retrieval context for a single RAG task.

    Lives on TaskSpec.rag. When present, the runner dispatches to the RAG
    executor (embed → retrieve → augment prompt → generate).
    """

    enabled: bool = True
    top_k: int = 4
    chunk_size_chars: int = 2000
    chunk_overlap_chars: int = 200
    # Chunk IDs that the answer is expected to draw from. Used to compute
    # retrieval_recall@k separately from answer quality.
    expected_chunks: list[str] = Field(default_factory=list)
    # If True, the question has no answer in the corpus (honesty test).
    out_of_corpus: bool = False
