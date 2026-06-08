"""RAG pipeline: embed query → retrieve top-k → augment prompt → generate."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ollympics.core.embedder import Embedder
from ollympics.core.ollama import OllamaClient
from ollympics.core.vector_store import VectorStore
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec
from ollympics.suites.rag.corpus import vector_store_path

RAG_USER_TEMPLATE = (
    "Contexto recuperado:\n"
    "---\n"
    "{context}\n"
    "---\n\n"
    "Pregunta: {question}"
)


@dataclass
class RagResult:
    answer: str
    retrieved_chunks: list[dict[str, Any]]
    context_used: str
    retrieval_recall_at_k: float | None
    ttft_ms: int | None
    wall_time_s: float
    tokens_in: int | None
    tokens_out: int | None
    tps_decode: float | None
    error: str | None = None
    raw_ollama_final: dict[str, Any] = field(default_factory=dict)


async def run_rag_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> RagResult:
    assert spec.rag is not None, "spec.rag requerido para rag executor"
    start = time.monotonic()

    store = VectorStore(vector_store_path())
    if len(store) == 0:
        return RagResult(
            answer="",
            retrieved_chunks=[],
            context_used="",
            retrieval_recall_at_k=None,
            ttft_ms=None,
            wall_time_s=time.monotonic() - start,
            tokens_in=None,
            tokens_out=None,
            tps_decode=None,
            error="Vector store vacío. Ejecuta `oly corpus build`.",
        )

    embedder = Embedder()
    try:
        q_emb = await embedder.embed(spec.prompt.user)
    except Exception as e:
        return RagResult(
            answer="",
            retrieved_chunks=[],
            context_used="",
            retrieval_recall_at_k=None,
            ttft_ms=None,
            wall_time_s=time.monotonic() - start,
            tokens_in=None,
            tokens_out=None,
            tps_decode=None,
            error=f"embedder error: {e}",
        )

    hits = store.search(q_emb, k=spec.rag.top_k)
    chunks_data = [
        {
            "id": c.id,
            "doc": c.doc,
            "section": c.section,
            "text": c.text,
            "score": score,
        }
        for c, score in hits
    ]
    context = "\n\n---\n\n".join(
        f"[{c['id']} · {c['section']}]\n{c['text']}" for c in chunks_data
    )
    user_prompt = RAG_USER_TEMPLATE.format(
        context=context, question=spec.prompt.user
    )

    try:
        gen = await client.generate(
            model=model_name,
            prompt=user_prompt,
            system=spec.prompt.system,
            options=runtime.ollama_options(),
            timeout_s=spec.timeout_s,
        )
    except Exception as e:
        return RagResult(
            answer="",
            retrieved_chunks=chunks_data,
            context_used=context,
            retrieval_recall_at_k=None,
            ttft_ms=None,
            wall_time_s=time.monotonic() - start,
            tokens_in=None,
            tokens_out=None,
            tps_decode=None,
            error=f"generate error: {e}",
        )

    expected = set(spec.rag.expected_chunks)
    if expected:
        retrieved = {c["id"] for c in chunks_data}
        recall = len(expected & retrieved) / len(expected)
    else:
        recall = None

    return RagResult(
        answer=gen.text,
        retrieved_chunks=chunks_data,
        context_used=context,
        retrieval_recall_at_k=recall,
        ttft_ms=gen.ttft_ms,
        wall_time_s=time.monotonic() - start,
        tokens_in=gen.tokens_in,
        tokens_out=gen.tokens_out,
        tps_decode=gen.tps_decode,
        raw_ollama_final=gen.raw_final,
    )
