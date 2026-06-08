"""Loads task specs from `tasks/<suite>/*.yaml`.

A "suite" is just the folder name. Tasks are discovered by globbing for *.yaml.
Validation happens via Pydantic — bad YAML fails loud with a useful message.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from ollympics.core.config import settings
from ollympics.schemas.task import TaskSpec


class TaskLoadError(RuntimeError):
    pass


def list_suites(tasks_dir: Path | None = None) -> list[str]:
    base = tasks_dir or settings.tasks_dir
    if not base.exists():
        return []
    return sorted([p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")])


def load_suite(suite: str, tasks_dir: Path | None = None) -> list[TaskSpec]:
    # RAG uses a dedicated loader: qa.yaml has a different shape (a list of
    # QAEntry, not a TaskSpec dict).
    if suite == "rag":
        from ollympics.suites.rag.loader import load_rag_tasks

        return load_rag_tasks(tasks_dir)

    # Planning emits two TaskSpec variants (4a + 4b) per logical YAML.
    if suite == "planning":
        from ollympics.suites.planning.loader import load_planning_tasks

        return load_planning_tasks(tasks_dir)

    base = tasks_dir or settings.tasks_dir
    suite_dir = base / suite
    if not suite_dir.exists():
        raise TaskLoadError(f"suite '{suite}' no existe en {base}")

    specs: list[TaskSpec] = []
    for path in sorted(suite_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text())
            spec = TaskSpec.model_validate(raw)
        except (yaml.YAMLError, ValidationError) as e:
            raise TaskLoadError(f"error cargando {path}: {e}") from e
        if spec.suite != suite:
            raise TaskLoadError(
                f"{path}: campo suite='{spec.suite}' no coincide con carpeta '{suite}'"
            )
        specs.append(spec)
    return specs


def load_all(tasks_dir: Path | None = None) -> dict[str, list[TaskSpec]]:
    return {s: load_suite(s, tasks_dir) for s in list_suites(tasks_dir)}
