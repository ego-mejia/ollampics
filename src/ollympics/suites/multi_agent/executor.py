"""LangGraph multi-role workflow: Researcher → Critic → Writer.

State machine:
  START → researcher → critic → writer → END
  (with iterations>1: → critic → writer → ... until iterations consumed)

Each role is a single `generate` call with a role-specific system prompt.
Final answer is the writer's last output.

We use LangGraph instead of CrewAI because CrewAI 0.x pins rich<13.7 and
typer<0.9 which conflict with our pinned 15.x / 0.26.x. CrewAI 1.x is
pre-release. The role pattern is the same; LangGraph just gives us less
opinionated prompting (which arguably gives a cleaner measurement signal).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ollympics.core.ollama import OllamaClient
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec

RESEARCHER_SYSTEM = (
    "Eres un investigador. Recibes un tema y produces notas estructuradas "
    "con 4-6 hallazgos clave, en formato lista markdown. Cada hallazgo en "
    "una línea, concreto, sin marketing. Idioma: español."
)

CRITIC_SYSTEM = (
    "Eres un revisor crítico. Recibes notas de investigación y produces una "
    "lista de gaps, contradicciones o puntos débiles. Sé directo y concreto. "
    "Lista markdown corta (3-5 puntos). Idioma: español."
)

WRITER_SYSTEM = (
    "Eres un redactor técnico. Recibes (a) tema, (b) notas del investigador, "
    "(c) críticas del revisor. Produces un reporte final en markdown con "
    "encabezados (##), conciso pero completo. Integra las críticas. "
    "Idioma: español."
)


class MultiAgentState(TypedDict, total=False):
    topic: str
    research_notes: str
    critique: str
    final_report: str
    iteration: int
    max_iterations: int
    error: str | None
    tokens_in_total: int
    tokens_out_total: int
    eval_duration_ns_total: int
    n_turns: int
    ttft_ms: int | None
    # role-level breakdown for transcript
    transcripts: list[dict[str, Any]]
    # injected
    _client: OllamaClient
    _model: str
    _runtime: RuntimeConfig
    _timeout_s: int
    _researcher_system: str
    _critic_system: str
    _writer_system: str


async def _generate(
    state: MultiAgentState, system: str, user: str, role: str
) -> str:
    client = state["_client"]
    res = await client.generate(
        model=state["_model"],
        prompt=user,
        system=system,
        options=state["_runtime"].ollama_options(),
        timeout_s=state["_timeout_s"],
    )
    state["tokens_in_total"] = state.get("tokens_in_total", 0) + (res.tokens_in or 0)
    state["tokens_out_total"] = state.get("tokens_out_total", 0) + (res.tokens_out or 0)
    state["eval_duration_ns_total"] = state.get("eval_duration_ns_total", 0) + int(
        res.raw_final.get("eval_duration") or 0
    )
    state["n_turns"] = state.get("n_turns", 0) + 1
    if state.get("ttft_ms") is None:
        state["ttft_ms"] = res.ttft_ms
    state.setdefault("transcripts", []).append(
        {
            "role": role,
            "iteration": state.get("iteration", 0),
            "system": system[:200],
            "user": user[:500],
            "output": res.text,
            "tokens_in": res.tokens_in,
            "tokens_out": res.tokens_out,
        }
    )
    return res.text


async def researcher_node(state: MultiAgentState) -> MultiAgentState:
    user = (
        f"Tema a investigar: {state['topic']}\n\n"
        f"Produce 4-6 hallazgos clave en lista markdown."
    )
    text = await _generate(state, state["_researcher_system"], user, "researcher")
    state["research_notes"] = text.strip()
    return state


async def critic_node(state: MultiAgentState) -> MultiAgentState:
    prior = ""
    if state.get("final_report"):
        prior = f"\n\nBorrador previo:\n{state['final_report']}\n"
    user = (
        f"Tema: {state['topic']}\n\n"
        f"Notas del investigador:\n{state.get('research_notes', '')}\n"
        f"{prior}"
        f"Identifica 3-5 gaps, contradicciones o puntos débiles."
    )
    text = await _generate(state, state["_critic_system"], user, "critic")
    state["critique"] = text.strip()
    return state


async def writer_node(state: MultiAgentState) -> MultiAgentState:
    user = (
        f"Tema: {state['topic']}\n\n"
        f"Notas del investigador:\n{state.get('research_notes', '')}\n\n"
        f"Críticas del revisor:\n{state.get('critique', '')}\n\n"
        f"Produce el reporte final integrando las críticas."
    )
    text = await _generate(state, state["_writer_system"], user, "writer")
    state["final_report"] = text.strip()
    state["iteration"] = state.get("iteration", 0) + 1
    return state


def should_iterate(state: MultiAgentState) -> str:
    if state.get("iteration", 0) >= state.get("max_iterations", 1):
        return "end"
    return "critic"


def _build_graph() -> Any:
    g = StateGraph(MultiAgentState)
    g.add_node("researcher", researcher_node)
    g.add_node("critic", critic_node)
    g.add_node("writer", writer_node)
    g.add_edge(START, "researcher")
    g.add_edge("researcher", "critic")
    g.add_edge("critic", "writer")
    g.add_conditional_edges("writer", should_iterate, {"end": END, "critic": "critic"})
    return g.compile()


@dataclass
class MultiAgentResult:
    final_report: str
    research_notes: str
    critique: str
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    n_turns: int = 0
    ttft_ms: int | None = None
    wall_time_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    tps_decode: float | None = None
    error: str | None = None


async def run_multi_agent_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> MultiAgentResult:
    assert spec.multi_agent is not None
    start = time.monotonic()

    initial: MultiAgentState = {
        "topic": spec.prompt.user,
        "iteration": 0,
        "max_iterations": spec.multi_agent.iterations,
        "tokens_in_total": 0,
        "tokens_out_total": 0,
        "eval_duration_ns_total": 0,
        "n_turns": 0,
        "ttft_ms": None,
        "transcripts": [],
        "_client": client,
        "_model": model_name,
        "_runtime": runtime,
        "_timeout_s": spec.timeout_s,
        "_researcher_system": spec.multi_agent.researcher_system or RESEARCHER_SYSTEM,
        "_critic_system": spec.multi_agent.critic_system or CRITIC_SYSTEM,
        "_writer_system": spec.multi_agent.writer_system or WRITER_SYSTEM,
    }

    graph = _build_graph()
    final = await graph.ainvoke(initial)

    wall = time.monotonic() - start
    tokens_out = int(final.get("tokens_out_total", 0))
    eval_ns = int(final.get("eval_duration_ns_total", 0))
    tps = tokens_out / (eval_ns / 1e9) if eval_ns > 0 and tokens_out > 0 else None

    return MultiAgentResult(
        final_report=final.get("final_report", ""),
        research_notes=final.get("research_notes", ""),
        critique=final.get("critique", ""),
        transcripts=final.get("transcripts", []),
        n_turns=int(final.get("n_turns", 0)),
        ttft_ms=final.get("ttft_ms"),
        wall_time_s=wall,
        tokens_in=int(final.get("tokens_in_total", 0)),
        tokens_out=tokens_out,
        tps_decode=tps,
        error=final.get("error"),
    )
