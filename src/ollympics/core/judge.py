"""Deterministic verifiers + stub for LLM judge.

Each verifier takes (response_text, verifier_spec) and returns a Verdict.
Composite verifiers recurse. LLM judge is a stub in phase 0+1.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass

from ollympics.schemas.verifier import (
    CompositeVerifier,
    ExactMatchVerifier,
    JsonSchemaVerifier,
    LLMJudgeVerifier,
    PersonalAgentVerifier,
    RegexVerifier,
    ToolTraceVerifier,
    Verifier,
)


def find_llm_judges(verifier: Verifier) -> list[LLMJudgeVerifier]:
    """Walks a verifier tree and returns all LLM judge nodes.

    Used by the runner to know whether async judge evaluation is needed.
    """
    if isinstance(verifier, LLMJudgeVerifier):
        return [verifier]
    if isinstance(verifier, CompositeVerifier):
        out: list[LLMJudgeVerifier] = []
        for sub in (verifier.all_of or []) + (verifier.any_of or []):
            out.extend(find_llm_judges(sub))
        return out
    return []


@dataclass
class Verdict:
    passed: bool
    reason: str = ""
    details: dict | None = None


def verify(
    response_text: str,
    verifier: Verifier,
    *,
    trace: list[dict] | None = None,
    format_errors: int = 0,
    llm_results: dict[int, Verdict] | None = None,
    pa_result: dict | None = None,
) -> Verdict:
    """Sync verifier. For LLM judges, the runner pre-evaluates them async and
    passes the results via `llm_results` keyed by `id(verifier_node)`. For
    personal-agent verifiers, the runner passes structured stats via
    `pa_result`.
    """
    match verifier:
        case RegexVerifier():
            return _verify_regex(response_text, verifier)
        case ExactMatchVerifier():
            return _verify_exact(response_text, verifier)
        case JsonSchemaVerifier():
            return _verify_json_schema(response_text, verifier)
        case CompositeVerifier():
            return _verify_composite(
                response_text,
                verifier,
                trace=trace,
                format_errors=format_errors,
                llm_results=llm_results,
            )
        case ToolTraceVerifier():
            return _verify_tool_trace(
                response_text, verifier, trace or [], format_errors
            )
        case PersonalAgentVerifier():
            return _verify_personal_agent(verifier, pa_result or {})
        case LLMJudgeVerifier():
            if llm_results and id(verifier) in llm_results:
                return llm_results[id(verifier)]
            return Verdict(
                passed=False,
                reason="llm_judge: sin resultado (LLM_API_KEY no configurada)",
            )
    return Verdict(passed=False, reason=f"verifier desconocido: {verifier!r}")


def _verify_personal_agent(v: PersonalAgentVerifier, pa: dict) -> Verdict:
    recall = float(pa.get("recall_rate", 0.0))
    fidelity = float(pa.get("tool_fidelity", 0.0))
    closing_ok = pa.get("closing_summary_ok")
    fails: list[str] = []
    if recall < v.min_recall_rate:
        fails.append(f"recall_rate={recall:.2f} < {v.min_recall_rate}")
    if fidelity < v.min_tool_fidelity:
        fails.append(f"tool_fidelity={fidelity:.2f} < {v.min_tool_fidelity}")
    if v.require_closing_summary and closing_ok is False:
        fails.append("closing_summary missing required items")
    if fails:
        return Verdict(False, "; ".join(fails), details={"recall": recall, "fidelity": fidelity})
    return Verdict(
        True,
        f"recall={recall:.2f} fidelity={fidelity:.2f}",
        details={"recall": recall, "fidelity": fidelity},
    )


def _verify_regex(text: str, v: RegexVerifier) -> Verdict:
    flags = 0
    if "i" in v.flags.lower():
        flags |= re.IGNORECASE
    if "m" in v.flags.lower():
        flags |= re.MULTILINE
    if "s" in v.flags.lower():
        flags |= re.DOTALL
    match = re.search(v.pattern, text, flags)
    if match:
        return Verdict(True, f"matched: {match.group(0)[:80]!r}")
    return Verdict(False, f"no match para patrón {v.pattern!r}")


def _verify_exact(text: str, v: ExactMatchVerifier) -> Verdict:
    candidates = v.expected if isinstance(v.expected, list) else [v.expected]
    response = text if v.case_sensitive else text.lower()
    response_norm = " ".join(response.split())
    for cand in candidates:
        target = cand if v.case_sensitive else cand.lower()
        target_norm = " ".join(target.split())
        if v.fuzzy:
            ratio = difflib.SequenceMatcher(None, response_norm, target_norm).ratio()
            if ratio >= 0.85 or target_norm in response_norm:
                return Verdict(True, f"matched (fuzzy ratio={ratio:.2f}): {cand!r}")
        else:
            if target_norm in response_norm:
                return Verdict(True, f"contains: {cand!r}")
    return Verdict(False, f"no match contra {candidates!r}")


def _verify_json_schema(text: str, v: JsonSchemaVerifier) -> Verdict:
    payload = _extract_json(text)
    if payload is None:
        return Verdict(False, "respuesta no contiene JSON parseable")
    ok, err = _check_schema(payload, v.schema_)
    if ok:
        return Verdict(True, "JSON valida contra schema")
    return Verdict(False, f"schema violation: {err}", details={"parsed": payload})


def _verify_composite(
    text: str,
    v: CompositeVerifier,
    *,
    trace: list[dict] | None,
    format_errors: int,
    llm_results: dict[int, Verdict] | None = None,
) -> Verdict:
    if v.all_of:
        results = [
            verify(
                text,
                sub,
                trace=trace,
                format_errors=format_errors,
                llm_results=llm_results,
            )
            for sub in v.all_of
        ]
        if all(r.passed for r in results):
            return Verdict(True, "all_of: pasaron todos")
        failed = [r.reason for r in results if not r.passed]
        return Verdict(False, f"all_of: fallaron {failed}")
    if v.any_of:
        results = [
            verify(
                text,
                sub,
                trace=trace,
                format_errors=format_errors,
                llm_results=llm_results,
            )
            for sub in v.any_of
        ]
        if any(r.passed for r in results):
            return Verdict(True, "any_of: al menos uno pasó")
        return Verdict(False, "any_of: ninguno pasó")
    return Verdict(False, "composite vacío")


def _verify_tool_trace(
    text: str,
    v: ToolTraceVerifier,
    trace: list[dict],
    format_errors: int,
) -> Verdict:
    if format_errors > v.max_format_errors:
        return Verdict(
            False,
            f"format_errors={format_errors} > max={v.max_format_errors}",
        )

    if v.strict_order:
        if len(trace) < len(v.expected_calls):
            return Verdict(
                False,
                f"trace tiene {len(trace)} calls, esperados {len(v.expected_calls)}",
            )
        for i, expected in enumerate(v.expected_calls):
            actual = trace[i]
            if actual.get("tool") != expected.tool:
                return Verdict(
                    False,
                    f"pos {i}: esperado {expected.tool!r}, recibido {actual.get('tool')!r}",
                )
            if expected.args_schema:
                ok, err = _check_schema(actual.get("args") or {}, expected.args_schema)
                if not ok:
                    return Verdict(False, f"pos {i} args: {err}")
    else:
        used: set[int] = set()
        for expected in v.expected_calls:
            found = False
            for j, actual in enumerate(trace):
                if j in used or actual.get("tool") != expected.tool:
                    continue
                if expected.args_schema:
                    ok, _err = _check_schema(actual.get("args") or {}, expected.args_schema)
                    if not ok:
                        continue
                used.add(j)
                found = True
                break
            if not found:
                return Verdict(False, f"no se encontró match para tool {expected.tool!r}")

    if not v.allow_extra_calls and len(trace) > len(v.expected_calls):
        return Verdict(
            False,
            f"trace tiene {len(trace)} calls, esperado max {len(v.expected_calls)}",
        )

    if v.final_message is not None:
        sub = verify(text, v.final_message, trace=trace, format_errors=format_errors)
        if not sub.passed:
            return Verdict(False, f"final_message: {sub.reason}")

    return Verdict(
        True,
        f"trace ok ({len(trace)} calls, {format_errors} format errors)",
    )


def _extract_json(text: str) -> dict | list | None:
    """Find first JSON object/array in text. Tolerates code fences and prefixes."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if not match:
            return None
        candidate = match.group(1)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _check_schema(value, schema: dict) -> tuple[bool, str | None]:
    """Minimal JSON Schema check: type + required + properties + enum + pattern.

    Subset chosen to cover task verifier needs without pulling jsonschema dep.
    """
    if "enum" in schema:
        choices = schema["enum"]
        if isinstance(value, str) and all(isinstance(c, str) for c in choices):
            if value.strip().lower() not in {c.lower() for c in choices}:
                return False, f"valor {value!r} no en enum {choices!r}"
        elif value not in choices:
            return False, f"valor {value!r} no en enum {choices!r}"
    if "pattern" in schema and isinstance(value, str):
        if not re.search(schema["pattern"], value):
            return False, f"valor {value!r} no matchea pattern {schema['pattern']!r}"
    expected_type = schema.get("type")
    if expected_type and not _type_matches(value, expected_type):
        return False, f"esperado type={expected_type}, recibido {type(value).__name__}"
    if expected_type == "object":
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                return False, f"falta key requerido: {key}"
        props = schema.get("properties") or {}
        for key, subschema in props.items():
            if key in value:
                ok, err = _check_schema(value[key], subschema)
                if not ok:
                    return False, f"en .{key}: {err}"
    elif expected_type == "array":
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(value):
                ok, err = _check_schema(item, items_schema)
                if not ok:
                    return False, f"en [{i}]: {err}"
    return True, None


def _type_matches(value, expected: str) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    py_type = mapping.get(expected)
    if py_type is None:
        return True
    if expected == "integer" and isinstance(value, bool):
        return False
    if expected == "number" and isinstance(value, bool):
        return False
    return isinstance(value, py_type)
