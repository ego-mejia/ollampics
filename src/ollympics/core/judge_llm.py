"""DeepSeek (or any OpenAI-compatible) judge for open-ended answers.

Used by the RAG suite for `multi_doc_synthesis` and `out_of_corpus` tasks.
Persists results to `judge_evaluations` and uses that table as a cache so
re-evaluating the same (attempt, judge_model, rubric) does not hit the API
again.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ollympics.core.config import llm_settings
from ollympics.db.models import JudgeEvaluation

RUBRICS: dict[str, str] = {
    "rag_factual_match_v1": (
        "Evalúa si la respuesta del modelo contiene los hechos clave esperados. "
        "Score=1.0 si menciona TODOS los key_facts; 0.5 si menciona al menos uno; "
        "0.0 si ninguno."
    ),
    "rag_open_synthesis_v1": (
        "Evalúa si la respuesta combina coherentemente la información del "
        "contexto recuperado. Score alto si (a) menciona los key_facts, "
        "(b) no contradice el contexto, (c) está bien estructurada y es "
        "completa pero concisa."
    ),
    "rag_honest_refusal_v1": (
        "La pregunta NO tiene respuesta en el contexto. Score=1.0 si el modelo "
        "lo dice explícitamente (\"no lo sé\", \"no está en el contexto\", "
        "etc.) sin inventar; 0.0 si fabricó una respuesta."
    ),
}


@dataclass
class JudgeResult:
    score: float
    passed: bool
    rationale: str
    cost_usd: float | None
    judge_model: str


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


async def evaluate_with_judge(
    session: Session,
    *,
    attempt_id: int,
    rubric: str,
    threshold: float,
    response_text: str,
    question: str,
    key_facts: list[str],
    context_used: str,
    judge_model: str | None = None,
) -> JudgeResult:
    model = judge_model or llm_settings.LLM_MODEL

    # Cache lookup — only for real attempt IDs. attempt_id<=0 means the
    # caller (typically the runner during a live execution) wants a fresh
    # evaluation per call; persisted attempt_id is filled later if needed.
    if attempt_id > 0:
        existing = session.scalar(
            select(JudgeEvaluation).where(
                JudgeEvaluation.attempt_id == attempt_id,
                JudgeEvaluation.judge_model == model,
                JudgeEvaluation.rubric_name == rubric,
            )
        )
        if existing is not None:
            return JudgeResult(
                score=existing.score,
                passed=existing.pass_,
                rationale=existing.rationale or "",
                cost_usd=existing.cost_usd,
                judge_model=model,
            )

    if not llm_settings.LLM_API_KEY:
        return JudgeResult(
            score=0.0,
            passed=False,
            rationale="LLM_API_KEY no configurada (judge_unavailable)",
            cost_usd=0.0,
            judge_model=model,
        )

    rubric_text = RUBRICS.get(rubric, "Evalúa la calidad de la respuesta.")
    system = (
        "Eres un juez evaluador estricto. Aplicas la rúbrica dada y respondes "
        "SOLO con JSON {\"score\": float entre 0 y 1, \"pass\": bool, "
        "\"rationale\": \"string corto\"}. Sin texto adicional."
    )
    user = (
        f"RUBRIC: {rubric_text}\n\n"
        f"QUESTION: {question}\n\n"
        f"KEY_FACTS_EXPECTED: {key_facts}\n\n"
        f"RETRIEVED_CONTEXT:\n{context_used[:4000]}\n\n"
        f"MODEL_ANSWER:\n{response_text}\n"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {llm_settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    url = llm_settings.LLM_BASE_URL.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    raw = data["choices"][0]["message"]["content"]
    raw = _strip_code_fence(raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = (
            json.loads(m.group(0))
            if m
            else {"score": 0.0, "pass": False, "rationale": raw[:200]}
        )

    score = float(parsed.get("score", 0.0))
    passed = bool(parsed.get("pass", score >= threshold))
    rationale = str(parsed.get("rationale", ""))

    # DeepSeek pricing approx. (junio 2026): adjust if you swap provider.
    usage = data.get("usage", {})
    cost = (
        usage.get("prompt_tokens", 0) * 0.00000027
        + usage.get("completion_tokens", 0) * 0.0000011
    )

    if attempt_id > 0:
        session.add(
            JudgeEvaluation(
                attempt_id=attempt_id,
                judge_model=model,
                rubric_name=rubric,
                score=score,
                pass_=passed,
                rationale=rationale,
                cost_usd=cost,
            )
        )
        session.flush()

    return JudgeResult(
        score=score, passed=passed, rationale=rationale, cost_usd=cost, judge_model=model
    )
