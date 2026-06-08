"""LangGraph agent that generates the RAG corpus + Q&A via an OpenAI-compatible LLM.

Flow:
    START → generate_manual → generate_hr → generate_changelog → generate_safety
          → generate_qa → END

State accumulates the generated docs. Each `generate_doc_*` node prepends
the canonical facts to its spec prompt, calls the LLM, and stores the result.
The `generate_qa` node feeds the 4 docs back as context.

Provider config (OpenAI-compatible) comes from `llm_settings` (`.env`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from ollympics.core.config import llm_settings
from ollympics.generators.synthetic_corpus.prompts import read_prompt


class GenState(TypedDict, total=False):
    """Mutable state passed through the LangGraph nodes."""

    prompts_dir: Path
    canonical: str
    docs: dict[str, str]      # filename without ext → markdown content
    qa_yaml: str
    errors: list[str]


DOC_TASKS: list[tuple[str, str]] = [
    # (output filename without ext, prompt filename in tasks/rag/prompts/)
    ("helion_manual_x3", "doc_manual_x3.md"),
    ("helion_hr_policy", "doc_hr_policy.md"),
    ("helion_api_changelog", "doc_api_changelog.md"),
    ("helion_safety_protocols", "doc_safety_protocols.md"),
]


def _llm() -> ChatOpenAI:
    if not llm_settings.LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY no está definida en .env. "
            "Configúrala antes de correr el generador."
        )
    return ChatOpenAI(
        model=llm_settings.LLM_MODEL,
        api_key=llm_settings.LLM_API_KEY,
        base_url=llm_settings.LLM_BASE_URL,
        temperature=0.6,
        max_tokens=8000,
    )


SYSTEM_DOC = (
    "Eres un escritor técnico senior. Generas documentación interna coherente, "
    "técnica y sin marketing speech. Sigues estrictamente la estructura y los "
    "hechos canónicos que se te dan. Responde SOLO con el contenido del "
    "documento en markdown — sin meta-comentarios, sin bloques de código que "
    "envuelvan el resultado."
)

SYSTEM_QA = (
    "Eres un diseñador de evaluaciones de RAG. Generas preguntas-respuesta "
    "estratificadas a partir de un corpus. Sigues exactamente el formato YAML "
    "pedido. Respondes SOLO con el YAML — sin meta-comentarios, sin code fences."
)


def _make_doc_node(out_name: str, prompt_file: str) -> Callable[[GenState], GenState]:
    def node(state: GenState) -> GenState:
        llm = _llm()
        spec = read_prompt(state["prompts_dir"], prompt_file)
        user = (
            f"{state['canonical']}\n\n---\n\n{spec}\n\n"
            f"Genera el documento `{out_name}.md` siguiendo la estructura y "
            f"longitud objetivo. Recuerda: idioma español, sin marketing."
        )
        msgs = [SystemMessage(content=SYSTEM_DOC), HumanMessage(content=user)]
        resp = llm.invoke(msgs)
        content = _strip_code_fence(resp.content)
        state.setdefault("docs", {})[out_name] = content
        return state

    node.__name__ = f"generate_{out_name.split('_', 1)[1]}"
    return node


def _generate_qa(state: GenState) -> GenState:
    llm = _llm()
    spec = read_prompt(state["prompts_dir"], "qa_generation.md")
    docs_concat = "\n\n".join(
        f"# === DOC: {name} ===\n\n{content}"
        for name, content in (state.get("docs") or {}).items()
    )
    user = (
        f"{spec}\n\n---\n\nA continuación, el corpus completo. Las preguntas "
        f"deben referirse a hechos contenidos (o no contenidos) en estos "
        f"documentos:\n\n{docs_concat}"
    )
    msgs = [SystemMessage(content=SYSTEM_QA), HumanMessage(content=user)]
    resp = llm.invoke(msgs)
    state["qa_yaml"] = _strip_code_fence(resp.content)
    return state


def _strip_code_fence(text: str) -> str:
    """If the LLM wrapped its answer in ```...```, strip it."""
    text = text.strip()
    if text.startswith("```"):
        # remove first line (```lang) and last ```
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def build_graph() -> "object":
    g = StateGraph(GenState)
    prev = START
    for out_name, prompt_file in DOC_TASKS:
        node_name = f"gen_{out_name}"
        g.add_node(node_name, _make_doc_node(out_name, prompt_file))
        g.add_edge(prev, node_name)
        prev = node_name
    g.add_node("gen_qa", _generate_qa)
    g.add_edge(prev, "gen_qa")
    g.add_edge("gen_qa", END)
    return g.compile()
