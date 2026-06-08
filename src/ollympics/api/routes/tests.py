"""Routes for the /tests page in the frontend.

A "test" here = a benchmark suite. The page shows cards per suite, and clicking
a card reveals details + (for RAG) the corpus and prompts.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ollympics.generators.synthetic_corpus.runner import (
    corpus_dir,
    prompts_dir,
    qa_yaml_path,
)
from ollympics.suites.loader import list_suites, load_suite

router = APIRouter()


SUITE_META: dict[str, dict[str, str]] = {
    "baseline": {
        "label": "Baseline",
        "description": "Sanity check rápido: generación, JSON, factual, instrucciones, listas.",
        "icon": "✓",
    },
    "tool_calling": {
        "label": "Tool Calling",
        "description": "Capacidad de elegir y llamar tools correctamente. 6 tools mockeadas, 8 tasks.",
        "icon": "⚙",
    },
    "rag": {
        "label": "RAG",
        "description": "Retrieval-Augmented Generation sobre corpus ficticio. 50 Q&A en 3 tiers.",
        "icon": "📚",
    },
    "planning": {
        "label": "Planning",
        "description": "Planeación + ejecución con LangGraph. Cada task corre en modo 4a (plan propio) y 4b (plan dado) para aislar capacidades.",
        "icon": "🧭",
    },
    "personal_agent": {
        "label": "Personal Agent",
        "description": "20 turnos de conversación con tools y recall probes. Mide memoria de contexto, fidelidad de tool calls, y drift de latencia.",
        "icon": "🤝",
    },
    "multi_agent": {
        "label": "Multi-agent",
        "description": "Workflow multi-rol Researcher → Critic → Writer con LangGraph. Mide colaboración entre roles y calidad de reporte final.",
        "icon": "🎭",
    },
}


class SuiteCard(BaseModel):
    name: str
    label: str
    description: str
    icon: str
    n_tasks: int
    has_corpus: bool


class TaskMeta(BaseModel):
    task_id: str
    version: int
    description: str
    max_tries: int


class SuiteDetail(BaseModel):
    name: str
    label: str
    description: str
    icon: str
    n_tasks: int
    tasks: list[TaskMeta]


class CorpusDoc(BaseModel):
    name: str
    size_bytes: int
    n_lines: int
    preview: str
    content: str | None = None


class PromptFile(BaseModel):
    name: str
    size_bytes: int
    content: str


class GenerateResponse(BaseModel):
    status: str
    started_at: str


@router.get("/tests", response_model=list[SuiteCard])
async def get_tests() -> list[SuiteCard]:
    out: list[SuiteCard] = []
    for name in list_suites():
        try:
            specs = load_suite(name)
            n = len(specs)
        except Exception:
            n = 0
        meta = SUITE_META.get(
            name,
            {"label": name, "description": "", "icon": "•"},
        )
        out.append(
            SuiteCard(
                name=name,
                label=meta["label"],
                description=meta["description"],
                icon=meta["icon"],
                n_tasks=n,
                has_corpus=(name == "rag" and corpus_dir().exists()),
            )
        )
    return out


@router.get("/tests/{suite}", response_model=SuiteDetail)
async def get_test_detail(suite: str) -> SuiteDetail:
    if suite not in list_suites():
        raise HTTPException(404, f"suite '{suite}' no existe")
    meta = SUITE_META.get(suite, {"label": suite, "description": "", "icon": "•"})
    # RAG uses a dedicated loader (Phase 4). For now the detail page renders
    # the corpus + prompts directly, so we skip the generic task loader.
    if suite == "rag":
        return SuiteDetail(
            name=suite,
            label=meta["label"],
            description=meta["description"],
            icon=meta["icon"],
            n_tasks=0,
            tasks=[],
        )
    try:
        specs = load_suite(suite)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
    return SuiteDetail(
        name=suite,
        label=meta["label"],
        description=meta["description"],
        icon=meta["icon"],
        n_tasks=len(specs),
        tasks=[
            TaskMeta(
                task_id=s.task_id,
                version=s.version,
                description=s.description,
                max_tries=s.max_tries,
            )
            for s in specs
        ],
    )


@router.get("/corpus/rag", response_model=list[CorpusDoc])
async def list_corpus_docs(include_content: bool = False) -> list[CorpusDoc]:
    cdir = corpus_dir()
    if not cdir.exists():
        return []
    out: list[CorpusDoc] = []
    for md in sorted(cdir.glob("*.md")):
        text = md.read_text()
        out.append(
            CorpusDoc(
                name=md.name,
                size_bytes=md.stat().st_size,
                n_lines=text.count("\n") + 1,
                preview=_first_paragraph(text, 240),
                content=text if include_content else None,
            )
        )
    return out


@router.get("/corpus/rag/{doc_name}", response_model=CorpusDoc)
async def get_corpus_doc(doc_name: str) -> CorpusDoc:
    cdir = corpus_dir()
    path = cdir / doc_name
    if not path.exists() or not path.is_file() or path.suffix != ".md":
        raise HTTPException(404, "doc no existe")
    if not _safe_under(path, cdir):
        raise HTTPException(400, "path inválido")
    text = path.read_text()
    return CorpusDoc(
        name=path.name,
        size_bytes=path.stat().st_size,
        n_lines=text.count("\n") + 1,
        preview=_first_paragraph(text, 240),
        content=text,
    )


@router.get("/corpus/prompts", response_model=list[PromptFile])
async def list_prompts() -> list[PromptFile]:
    pdir = prompts_dir()
    if not pdir.exists():
        return []
    out: list[PromptFile] = []
    for p in sorted(pdir.glob("*.md")):
        out.append(
            PromptFile(
                name=p.name,
                size_bytes=p.stat().st_size,
                content=p.read_text(),
            )
        )
    return out


@router.post("/corpus/generate", response_model=GenerateResponse, status_code=202)
async def trigger_generate(
    background_tasks: BackgroundTasks,
    overwrite: bool = False,
) -> GenerateResponse:
    """Dispara la generación en background. Devuelve inmediatamente."""
    from datetime import datetime

    from ollympics.generators.synthetic_corpus.runner import generate_corpus

    def _run():
        try:
            generate_corpus(overwrite=overwrite)
        except Exception as e:
            # Log only — there's no UI for errors yet.
            print(f"[corpus generate] error: {e}")

    background_tasks.add_task(asyncio.to_thread, _run)
    return GenerateResponse(
        status="started",
        started_at=datetime.utcnow().isoformat(),
    )


def _first_paragraph(text: str, max_chars: int) -> str:
    """Returns the first non-heading paragraph trimmed to max_chars."""
    for block in text.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        return block[:max_chars] + ("…" if len(block) > max_chars else "")
    return text[:max_chars]


def _safe_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
