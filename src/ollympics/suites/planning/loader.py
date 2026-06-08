"""Loads planning tasks.

Each YAML in tasks/planning/ describes ONE logical task with its canonical
plan. The loader emits TWO TaskSpec instances per file:
  - <task_id>.4a (plan propio, sin canonical_plan)
  - <task_id>.4b (plan dado, canonical_plan completo)
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from ollympics.core.config import settings
from ollympics.schemas.planning import PlanningSpec
from ollympics.schemas.task import TaskSpec


class PlanningLoadError(RuntimeError):
    pass


def load_planning_tasks(tasks_dir: Path | None = None) -> list[TaskSpec]:
    base = (tasks_dir or settings.tasks_dir) / "planning"
    if not base.exists():
        return []
    out: list[TaskSpec] = []
    for path in sorted(base.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text())
        except yaml.YAMLError as e:
            raise PlanningLoadError(f"error cargando {path}: {e}") from e
        if not raw or not isinstance(raw, dict):
            continue
        canonical_plan = list(raw.pop("canonical_plan", []) or [])
        max_steps = int(raw.pop("max_steps", 8))
        try:
            base_spec = TaskSpec.model_validate(raw)
        except ValidationError as e:
            raise PlanningLoadError(f"error validando {path}: {e}") from e
        if base_spec.suite != "planning":
            raise PlanningLoadError(
                f"{path}: suite='{base_spec.suite}' debe ser 'planning'"
            )
        # Emit 4a (plan propio).
        out.append(
            base_spec.model_copy(
                update={
                    "task_id": f"{base_spec.task_id}.4a",
                    "planning": PlanningSpec(mode="4a", max_steps=max_steps),
                }
            )
        )
        # Emit 4b (plan dado).
        if canonical_plan:
            out.append(
                base_spec.model_copy(
                    update={
                        "task_id": f"{base_spec.task_id}.4b",
                        "planning": PlanningSpec(
                            mode="4b",
                            canonical_plan=canonical_plan,
                            max_steps=max_steps,
                        ),
                    }
                )
            )
    return out
