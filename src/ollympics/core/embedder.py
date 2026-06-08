"""nomic-embed-text via Ollama. Returns 768-dim vectors."""

from __future__ import annotations

import httpx

from ollympics.core.config import settings

EMBEDDER_MODEL = "nomic-embed-text"


class Embedder:
    def __init__(self, host: str | None = None, model: str = EMBEDDER_MODEL) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            if r.status_code == 404:
                raise RuntimeError(
                    f"modelo de embeddings '{self.model}' no está disponible en Ollama. "
                    f"Ejecuta: ollama pull {self.model}"
                )
            r.raise_for_status()
            return r.json()["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Ollama embeddings API does not support batching; sequential is fast
        # at this scale (~30-60 chunks).
        return [await self.embed(t) for t in texts]
