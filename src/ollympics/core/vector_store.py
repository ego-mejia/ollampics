"""Local persistent vector store. JSONL on disk + numpy cosine similarity.

For our scale (~50 chunks per corpus) this is faster and lighter than chromadb.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Chunk:
    id: str
    doc: str
    section: str
    text: str
    embedding: list[float]


class VectorStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._chunks: list[Chunk] = []
        self._matrix: np.ndarray | None = None
        if path.exists():
            self.load()

    def load(self) -> None:
        self._chunks = []
        with self.path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                self._chunks.append(Chunk(**d))
        self._rebuild_matrix()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            for c in self._chunks:
                f.write(
                    json.dumps(
                        {
                            "id": c.id,
                            "doc": c.doc,
                            "section": c.section,
                            "text": c.text,
                            "embedding": c.embedding,
                        }
                    )
                    + "\n"
                )

    def upsert(self, chunks: list[Chunk]) -> int:
        """Add chunks whose id isn't already present. Returns # added."""
        existing = {c.id for c in self._chunks}
        new = [c for c in chunks if c.id not in existing]
        self._chunks.extend(new)
        self._rebuild_matrix()
        return len(new)

    def clear(self) -> None:
        self._chunks = []
        self._matrix = None

    def _rebuild_matrix(self) -> None:
        if not self._chunks:
            self._matrix = None
            return
        m = np.array([c.embedding for c in self._chunks], dtype=np.float32)
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        # L2-normalize so cosine similarity == dot product
        self._matrix = m / np.maximum(norms, 1e-9)

    def search(
        self, query_embedding: list[float], k: int = 4
    ) -> list[tuple[Chunk, float]]:
        if self._matrix is None or not self._chunks:
            return []
        q = np.array(query_embedding, dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-9)
        scores = self._matrix @ q
        idx = np.argsort(-scores)[:k]
        return [(self._chunks[int(i)], float(scores[int(i)])) for i in idx]

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def __len__(self) -> int:
        return len(self._chunks)
