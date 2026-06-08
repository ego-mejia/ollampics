"""LangGraph executor for the Planning suite.

State machine:
  START → plan_node ──┐
                       ├──→ step_node ──→ (loop or synth)
                       │       │
                       │       └──conditional──→ synthesize_node → END
                       │
  (4b skips plan_node and uses canonical_plan directly)

Each node calls `OllamaClient.generate` once. The final answer is what the
verifier checks. Metrics are aggregated across all turns.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ollympics.core.ollama import OllamaClient
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec


class PlanState(TypedDict, total=False):
    problem: str
    system_prompt: str | None
    plan: list[str]
    step_idx: int
    step_results: list[str]
    final_answer: str
    error: str | None
    # Metrics accumulator
    tokens_in_total: int
    tokens_out_total: int
    eval_duration_ns_total: int
    n_turns: int
    ttft_ms: int | None
    # Injected (not part of state lifecycle)
    _client: OllamaClient
    _model: str
    _runtime: RuntimeConfig
    _timeout_s: int


PLAN_SYSTEM = (
    "Eres un planificador. Recibes un problema y produces un plan ejecutable "
    "como JSON array de pasos cortos (strings imperativos). Sin explicaciones, "
    "solo el array. Ejemplo: [\"Paso 1\", \"Paso 2\", \"Paso 3\"]"
)

STEP_SYSTEM_TEMPLATE = (
    "Eres un ejecutor metódico. Estás siguiendo un plan paso a paso para "
    "resolver un problema. Concéntrate SOLO en el paso actual; no avances "
    "ni resumas todo. Sé conciso (máx 6 líneas)."
)

SYNTH_SYSTEM = (
    "Eres un sintetizador. Recibes los resultados de ejecutar varios pasos "
    "y produces la respuesta final coherente al problema original. Sé directo."
)


def _extract_json_array(text: str) -> list[str] | None:
    """Try to find a JSON list of strings in `text`. Tolerates code fences."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        candidate = m.group(0) if m else None
    if not candidate:
        return None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list) and all(isinstance(x, str) for x in data):
        return data
    return None


async def _generate(state: PlanState, system: str, user: str) -> str:
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
    return res.text


async def plan_node(state: PlanState) -> PlanState:
    """Only executed in mode 4a. Asks the model for a plan."""
    if state.get("plan"):
        return state
    user = f"Problema: {state['problem']}\n\nProduce el plan como JSON array."
    try:
        text = await _generate(state, PLAN_SYSTEM, user)
    except Exception as e:
        state["error"] = f"plan_node error: {e}"
        state["plan"] = []
        return state
    plan = _extract_json_array(text) or []
    if not plan:
        # fallback: treat the text as a single step so we still execute something
        plan = [state["problem"]]
    state["plan"] = plan[: 8]  # cap to max_steps default
    return state


async def step_node(state: PlanState) -> PlanState:
    idx = state.get("step_idx", 0)
    plan = state.get("plan") or []
    if idx >= len(plan):
        return state
    current_step = plan[idx]
    prior = "\n".join(
        f"- Resultado paso {i + 1}: {r[:300]}"
        for i, r in enumerate(state.get("step_results", []))
    )
    user = (
        f"Problema: {state['problem']}\n\n"
        f"Plan completo: {json.dumps(plan, ensure_ascii=False)}\n\n"
        f"{'Resultados previos:\n' + prior + '\n' if prior else ''}"
        f"Paso actual ({idx + 1}/{len(plan)}): {current_step}\n\n"
        f"Ejecuta SOLO este paso."
    )
    try:
        text = await _generate(state, STEP_SYSTEM_TEMPLATE, user)
    except Exception as e:
        state["error"] = f"step_node {idx + 1} error: {e}"
        return state
    state.setdefault("step_results", []).append(text.strip())
    state["step_idx"] = idx + 1
    return state


def should_continue(state: PlanState) -> str:
    if state.get("error"):
        return "synthesize"
    plan = state.get("plan") or []
    if state.get("step_idx", 0) >= len(plan):
        return "synthesize"
    return "step"


async def synthesize_node(state: PlanState) -> PlanState:
    results = state.get("step_results", [])
    if not results:
        state["final_answer"] = ""
        return state
    joined = "\n\n".join(
        f"=== Paso {i + 1} ===\n{r}" for i, r in enumerate(results)
    )
    user = (
        f"Problema original: {state['problem']}\n\n"
        f"Resultados de ejecutar los pasos:\n{joined}\n\n"
        f"Produce la respuesta final al problema original."
    )
    try:
        text = await _generate(state, SYNTH_SYSTEM, user)
    except Exception as e:
        state["error"] = f"synthesize_node error: {e}"
        state["final_answer"] = "\n\n".join(results)
        return state
    state["final_answer"] = text.strip()
    return state


def _build_graph_4a():
    g = StateGraph(PlanState)
    g.add_node("plan", plan_node)
    g.add_node("step", step_node)
    g.add_node("synthesize", synthesize_node)
    g.add_edge(START, "plan")
    g.add_edge("plan", "step")
    g.add_conditional_edges("step", should_continue, {"step": "step", "synthesize": "synthesize"})
    g.add_edge("synthesize", END)
    return g.compile()


def _build_graph_4b():
    g = StateGraph(PlanState)
    g.add_node("step", step_node)
    g.add_node("synthesize", synthesize_node)
    g.add_edge(START, "step")
    g.add_conditional_edges("step", should_continue, {"step": "step", "synthesize": "synthesize"})
    g.add_edge("synthesize", END)
    return g.compile()


@dataclass
class PlanningResult:
    final_answer: str
    plan: list[str]
    step_results: list[str]
    n_turns: int
    ttft_ms: int | None
    wall_time_s: float
    tokens_in: int
    tokens_out: int
    tps_decode: float | None
    error: str | None = None
    raw_state: dict[str, Any] = field(default_factory=dict)


async def run_planning_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> PlanningResult:
    assert spec.planning is not None, "spec.planning requerido"
    start = time.monotonic()

    state: PlanState = {
        "problem": spec.prompt.user,
        "system_prompt": spec.prompt.system,
        "step_idx": 0,
        "step_results": [],
        "tokens_in_total": 0,
        "tokens_out_total": 0,
        "eval_duration_ns_total": 0,
        "n_turns": 0,
        "ttft_ms": None,
        "_client": client,
        "_model": model_name,
        "_runtime": runtime,
        "_timeout_s": spec.timeout_s,
    }

    if spec.planning.mode == "4b":
        state["plan"] = list(spec.planning.canonical_plan)
        graph = _build_graph_4b()
    else:
        graph = _build_graph_4a()

    final_state = await graph.ainvoke(state)

    wall = time.monotonic() - start
    tokens_out = int(final_state.get("tokens_out_total", 0))
    eval_ns = int(final_state.get("eval_duration_ns_total", 0))
    tps = tokens_out / (eval_ns / 1e9) if eval_ns > 0 and tokens_out > 0 else None

    return PlanningResult(
        final_answer=final_state.get("final_answer", ""),
        plan=final_state.get("plan", []),
        step_results=final_state.get("step_results", []),
        n_turns=int(final_state.get("n_turns", 0)),
        ttft_ms=final_state.get("ttft_ms"),
        wall_time_s=wall,
        tokens_in=int(final_state.get("tokens_in_total", 0)),
        tokens_out=tokens_out,
        tps_decode=tps,
        error=final_state.get("error"),
        raw_state={
            k: v for k, v in final_state.items() if not k.startswith("_")
        },
    )
