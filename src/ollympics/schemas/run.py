from __future__ import annotations

from pydantic import BaseModel, Field

from ollympics.schemas.runtime import DEFAULT_RUNTIME, RuntimeConfig


class RunConfig(BaseModel):
    models: list[str]
    runtime_configs: list[RuntimeConfig] = Field(default_factory=lambda: [DEFAULT_RUNTIME])
    suites: list[str]
    notes: str | None = None
