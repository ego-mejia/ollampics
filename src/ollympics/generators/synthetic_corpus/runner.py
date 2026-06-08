"""High-level entrypoint for the synthetic corpus agent.

Used by:
- CLI: `oly corpus generate`
- API: `POST /api/corpus/generate`
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ollympics.core.config import settings
from ollympics.generators.synthetic_corpus.agent import build_graph
from ollympics.generators.synthetic_corpus.prompts import write_default_prompts


@dataclass
class GenerationResult:
    docs_written: list[str]
    qa_yaml_path: str
    prompts_dir: str


def corpus_dir() -> Path:
    return settings.tasks_dir / "rag" / "corpus"


def prompts_dir() -> Path:
    return settings.tasks_dir / "rag" / "prompts"


def qa_yaml_path() -> Path:
    return settings.tasks_dir / "rag" / "qa.yaml"


def generate_corpus(*, overwrite: bool = False) -> GenerationResult:
    """Runs the LangGraph agent and writes all output files.

    Args:
        overwrite: if False, skip docs that already exist on disk.

    Returns:
        Paths of files written.
    """
    pdir = prompts_dir()
    cdir = corpus_dir()
    qa_path = qa_yaml_path()

    # 1. Ensure default prompts are on disk (only writes missing ones).
    write_default_prompts(pdir)

    # 2. Read canonical facts (the agent uses them as preamble).
    canonical = (pdir / "canonical_facts.md").read_text()

    # 3. Run the graph.
    graph = build_graph()
    final: dict = graph.invoke(
        {
            "prompts_dir": pdir,
            "canonical": canonical,
            "docs": {},
        }
    )

    # 4. Persist docs + qa.yaml.
    cdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, content in (final.get("docs") or {}).items():
        target = cdir / f"{name}.md"
        if target.exists() and not overwrite:
            continue
        target.write_text(content)
        written.append(str(target))

    if final.get("qa_yaml") and (not qa_path.exists() or overwrite):
        qa_path.write_text(final["qa_yaml"])

    return GenerationResult(
        docs_written=written,
        qa_yaml_path=str(qa_path),
        prompts_dir=str(pdir),
    )
