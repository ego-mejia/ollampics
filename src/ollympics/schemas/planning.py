from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PlanningMode = Literal["4a", "4b"]


class PlanningSpec(BaseModel):
    """Planning + execution config for a single task variant.

    - `4a` (plan-propio): the model must produce its own plan, then execute.
    - `4b` (plan-dado): the model receives `canonical_plan` and only executes.

    The same logical task spawns two TaskSpec instances (one per mode) so the
    benchmark can isolate planning capability from execution capability.
    """

    mode: PlanningMode
    canonical_plan: list[str] = Field(default_factory=list)
    max_steps: int = 8
