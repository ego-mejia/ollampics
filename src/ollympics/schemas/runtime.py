from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    num_ctx: int = 8192
    kv_cache_type: str = "f16"
    temperature: float = 0.0
    seed: int = 42
    top_p: float = 1.0
    num_gpu: int | None = None
    num_thread: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def hash(self) -> str:
        payload = self.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(canonical).hexdigest()[:16]

    def ollama_options(self) -> dict[str, Any]:
        """Maps to Ollama's `options` field for /api/generate and /api/chat."""
        opts: dict[str, Any] = {
            "num_ctx": self.num_ctx,
            "temperature": self.temperature,
            "seed": self.seed,
            "top_p": self.top_p,
        }
        if self.num_gpu is not None:
            opts["num_gpu"] = self.num_gpu
        if self.num_thread is not None:
            opts["num_thread"] = self.num_thread
        opts.update(self.extra)
        return opts


DEFAULT_RUNTIME = RuntimeConfig()
