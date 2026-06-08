"""Builds/loads the vector store from tasks/rag/corpus/*.md."""

from __future__ import annotations

from pathlib import Path

from ollympics.core.config import settings
from ollympics.core.embedder import Embedder
from ollympics.core.vector_store import Chunk, VectorStore
from ollympics.suites.rag.chunker import chunk_markdown


def vector_store_path() -> Path:
    return Path("data") / "vectors.jsonl"


def corpus_dir() -> Path:
    return settings.tasks_dir / "rag" / "corpus"


async def build_vector_store(
    *, force: bool = False, embedder: Embedder | None = None
) -> VectorStore:
    """Indexes all markdown docs in tasks/rag/corpus/. Idempotent unless `force`."""
    store = VectorStore(vector_store_path())
    if len(store) > 0 and not force:
        return store

    if force:
        store.clear()

    embedder = embedder or Embedder()
    cdir = corpus_dir()
    if not cdir.exists():
        raise FileNotFoundError(
            f"No existe {cdir}. Genera el corpus primero con `oly corpus generate`."
        )

    new_chunks: list[Chunk] = []
    for md in sorted(cdir.glob("*.md")):
        raw_chunks = chunk_markdown(md)
        texts = [c.text for c in raw_chunks]
        embeddings = await embedder.embed_batch(texts)
        for rc, emb in zip(raw_chunks, embeddings, strict=True):
            new_chunks.append(
                Chunk(
                    id=rc.id,
                    doc=rc.doc,
                    section=rc.section,
                    text=rc.text,
                    embedding=emb,
                )
            )

    store.upsert(new_chunks)
    store.save()
    return store
