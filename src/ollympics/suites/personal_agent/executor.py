"""Multi-turn conversational benchmark with tools + recall probes.

Each script defines N user turns. For each turn, we:
  1. Append the scripted user message.
  2. Call the model (chat with tools enabled, history accumulated).
  3. Execute any tool_calls the model emitted, feed results back, re-invoke.
  4. Capture per-turn metrics (ttft, tps, tokens, vram-snapshot).
  5. If turn type is `recall_probe`: check if the assistant's final response
     contains any of the expected substrings (case-insensitive).
  6. If turn has `expect_tool`: check the tool was actually called with valid
     args.

Aggregated outputs (returned + persisted in transcript_json):
  - `recall_rate`: fraction of recall probes passed
  - `tool_fidelity`: fraction of expected tool calls correctly made
  - `ttft_drift_ms`: difference between turn 2 ttft and last-turn ttft
  - `tps_drift`: difference between first decode tps and last
  - `closing_summary_ok`: substring check on the final summary turn
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ollympics.core.judge import _check_schema
from ollympics.core.ollama import OllamaClient
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec
from ollympics.suites.tool_calling.catalog import CATALOG, get_tools


@dataclass
class PersonalAgentResult:
    transcript: list[dict[str, Any]] = field(default_factory=list)
    per_turn_metrics: list[dict[str, Any]] = field(default_factory=list)
    recall_results: list[dict[str, Any]] = field(default_factory=list)
    tool_call_results: list[dict[str, Any]] = field(default_factory=list)
    closing_summary_ok: bool | None = None
    n_turns: int = 0
    wall_time_s: float = 0.0
    ttft_first_ms: int | None = None
    ttft_last_ms: int | None = None
    tps_first: float | None = None
    tps_last: float | None = None
    tokens_in_total: int = 0
    tokens_out_total: int = 0
    error: str | None = None

    @property
    def recall_rate(self) -> float:
        if not self.recall_results:
            return 1.0
        passed = sum(1 for r in self.recall_results if r.get("passed"))
        return passed / len(self.recall_results)

    @property
    def tool_fidelity(self) -> float:
        if not self.tool_call_results:
            return 1.0
        ok = sum(1 for r in self.tool_call_results if r.get("matched"))
        return ok / len(self.tool_call_results)


def _parse_args(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def _substr_any(haystack: str, needles: list[str]) -> bool:
    if not needles:
        return True
    h = haystack.lower()
    return any(n.lower() in h for n in needles)


def _substr_all(haystack: str, needles: list[str]) -> bool:
    if not needles:
        return True
    h = haystack.lower()
    return all(n.lower() in h for n in needles)


async def run_personal_agent_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> PersonalAgentResult:
    assert spec.personal_agent is not None
    pa = spec.personal_agent
    result = PersonalAgentResult()
    start = time.monotonic()

    tools = get_tools(pa.tools_enabled)
    tool_defs = [t.ollama_definition() for t in tools]

    messages: list[dict[str, Any]] = []
    if spec.prompt.system:
        messages.append({"role": "system", "content": spec.prompt.system})

    options = runtime.ollama_options()
    plants: dict[str, str] = {}

    for turn_spec in pa.script:
        result.n_turns += 1
        messages.append({"role": "user", "content": turn_spec.message})
        plants.update(turn_spec.plants)
        result.transcript.append(
            {"turn": turn_spec.turn, "role": "user", "content": turn_spec.message}
        )

        turn_metrics: dict[str, Any] = {
            "turn": turn_spec.turn,
            "type": turn_spec.type,
        }
        turn_start = time.monotonic()

        # Outer loop: keep invoking model until it returns a turn without tool_calls
        # (or we hit a soft cap of 3 inner iterations per turn to avoid runaways).
        emitted_tool_calls: list[dict[str, Any]] = []
        final_text = ""
        for _ in range(3):
            try:
                resp = await client.chat(
                    model=model_name,
                    messages=messages,
                    tools=tool_defs,
                    options=options,
                    timeout_s=spec.timeout_s,
                )
            except Exception as e:
                result.error = f"turn {turn_spec.turn}: {type(e).__name__}: {e}"
                turn_metrics["error"] = str(e)
                break

            turn_metrics.setdefault("tokens_in", 0)
            turn_metrics["tokens_in"] += int(resp.get("prompt_eval_count") or 0)
            turn_metrics.setdefault("tokens_out", 0)
            turn_metrics["tokens_out"] += int(resp.get("eval_count") or 0)
            eval_ns = int(resp.get("eval_duration") or 0)
            if eval_ns > 0 and resp.get("eval_count"):
                turn_metrics["tps_decode"] = int(resp["eval_count"]) / (eval_ns / 1e9)
            msg = resp.get("message", {}) or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()
            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                    **({"tool_calls": tool_calls} if tool_calls else {}),
                }
            )
            if tool_calls:
                emitted_tool_calls.extend(tool_calls)
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    tool_name = fn.get("name", "")
                    args = _parse_args(fn.get("arguments")) or {}
                    if tool_name in CATALOG:
                        try:
                            tres = CATALOG[tool_name].execute(args)
                        except Exception as e:
                            tres = {"error": f"{type(e).__name__}: {e}"}
                    else:
                        tres = {"error": f"unknown tool: {tool_name}"}
                    messages.append(
                        {
                            "role": "tool",
                            "name": tool_name or "unknown",
                            "content": json.dumps(tres),
                        }
                    )
                # Loop again so the model can incorporate the tool result
                continue
            else:
                final_text = content
                break
        else:
            # exhausted inner iterations
            turn_metrics.setdefault("warning", "inner_loop_max_reached")

        wall_turn = time.monotonic() - turn_start
        turn_metrics["wall_s"] = wall_turn
        # Crude per-turn TTFT proxy: time from sending request to receiving response.
        # Non-streaming chat doesn't expose true ttft; we use wall_turn as upper bound.
        turn_metrics["ttft_ms"] = int(wall_turn * 1000)

        result.transcript.append(
            {
                "turn": turn_spec.turn,
                "role": "assistant",
                "content": final_text,
                "tool_calls": emitted_tool_calls,
            }
        )
        result.per_turn_metrics.append(turn_metrics)

        # Update aggregates
        result.tokens_in_total += int(turn_metrics.get("tokens_in") or 0)
        result.tokens_out_total += int(turn_metrics.get("tokens_out") or 0)
        if result.ttft_first_ms is None:
            result.ttft_first_ms = turn_metrics.get("ttft_ms")
        result.ttft_last_ms = turn_metrics.get("ttft_ms")
        if "tps_decode" in turn_metrics:
            if result.tps_first is None:
                result.tps_first = turn_metrics["tps_decode"]
            result.tps_last = turn_metrics["tps_decode"]

        # Recall probe check
        if turn_spec.type == "recall_probe":
            passed = _substr_any(final_text, turn_spec.expect_substr_any)
            result.recall_results.append(
                {
                    "turn": turn_spec.turn,
                    "expected_any": turn_spec.expect_substr_any,
                    "passed": passed,
                    "got": final_text[:200],
                }
            )

        # Closing summary check
        if turn_spec.type == "closing_summary":
            ok = _substr_all(final_text, turn_spec.expect_substr_all)
            result.closing_summary_ok = ok

        # Tool fidelity check
        if turn_spec.expect_tool is not None:
            etc = turn_spec.expect_tool
            matched = False
            for tc in emitted_tool_calls:
                fn = tc.get("function") or {}
                if fn.get("name") != etc.name:
                    continue
                if etc.args_schema:
                    args = _parse_args(fn.get("arguments")) or {}
                    ok, _err = _check_schema(args, etc.args_schema)
                    if not ok:
                        continue
                matched = True
                break
            result.tool_call_results.append(
                {
                    "turn": turn_spec.turn,
                    "expected_tool": etc.name,
                    "matched": matched,
                    "emitted_tools": [
                        (tc.get("function") or {}).get("name", "?")
                        for tc in emitted_tool_calls
                    ],
                }
            )

        if result.error:
            break

    result.wall_time_s = time.monotonic() - start
    return result
