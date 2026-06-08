"""Multi-turn chat loop with tool execution.

The model emits `tool_calls`. We execute each tool from the local catalog, append
the result as a `role: tool` message, and continue until the model emits a final
assistant message with no tool_calls (or we hit max_turns).

Returns aggregated metrics across all turns plus the full trace + format_errors.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ollympics.core.ollama import OllamaClient
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.schemas.task import TaskSpec
from ollympics.suites.tool_calling.catalog import CATALOG, get_tools


@dataclass
class ToolCallingResult:
    final_message: str
    trace: list[dict[str, Any]] = field(default_factory=list)
    format_errors: int = 0
    n_turns: int = 0
    ttft_ms: int | None = None
    wall_time_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    tps_decode: float | None = None
    raw_turns: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def _parse_args(raw_args: Any) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(raw_args, dict):
        return raw_args, None
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args), None
        except json.JSONDecodeError as e:
            return None, f"args no es JSON válido: {e}"
    return None, f"args con tipo inesperado: {type(raw_args).__name__}"


async def run_tool_calling_task(
    client: OllamaClient,
    model_name: str,
    runtime: RuntimeConfig,
    spec: TaskSpec,
) -> ToolCallingResult:
    assert spec.tools is not None, "spec.tools requerido para tool_calling"

    tools = get_tools(spec.tools.enabled)
    tool_defs = [t.ollama_definition() for t in tools]

    messages: list[dict[str, Any]] = []
    if spec.prompt.system:
        messages.append({"role": "system", "content": spec.prompt.system})
    messages.append({"role": "user", "content": spec.prompt.user})

    result = ToolCallingResult(final_message="")
    options = runtime.ollama_options()
    sum_eval_duration_ns = 0
    start = time.monotonic()

    for turn in range(1, spec.tools.max_turns + 1):
        turn_start = time.monotonic()
        try:
            resp = await client.chat(
                model=model_name,
                messages=messages,
                tools=tool_defs,
                options=options,
                timeout_s=spec.timeout_s,
            )
        except Exception as e:
            result.error = f"turn {turn}: {type(e).__name__}: {e}"
            break

        result.n_turns = turn
        result.raw_turns.append(resp)
        elapsed_turn = time.monotonic() - turn_start

        if result.ttft_ms is None:
            result.ttft_ms = int(elapsed_turn * 1000)

        result.tokens_in += int(resp.get("prompt_eval_count") or 0)
        result.tokens_out += int(resp.get("eval_count") or 0)
        sum_eval_duration_ns += int(resp.get("eval_duration") or 0)

        msg = resp.get("message", {}) or {}
        tool_calls = msg.get("tool_calls") or []

        if not tool_calls:
            result.final_message = (msg.get("content") or "").strip()
            break

        messages.append(
            {
                "role": "assistant",
                "content": msg.get("content", ""),
                "tool_calls": tool_calls,
            }
        )

        for call in tool_calls:
            fn = call.get("function") or {}
            tool_name = fn.get("name", "")
            args, parse_err = _parse_args(fn.get("arguments"))

            if parse_err is not None:
                result.format_errors += 1
                result.trace.append(
                    {
                        "tool": tool_name,
                        "args": None,
                        "error": parse_err,
                        "turn": turn,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps({"error": parse_err}),
                        "name": tool_name or "unknown",
                    }
                )
                continue

            if tool_name not in CATALOG:
                result.format_errors += 1
                tool_result: dict[str, Any] = {"error": f"unknown tool: {tool_name}"}
                result.trace.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "error": "unknown_tool",
                        "result": tool_result,
                        "turn": turn,
                    }
                )
            else:
                try:
                    tool_result = CATALOG[tool_name].execute(args or {})
                except Exception as e:
                    tool_result = {"error": f"{type(e).__name__}: {e}"}
                result.trace.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result,
                        "turn": turn,
                    }
                )

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(tool_result),
                    "name": tool_name or "unknown",
                }
            )
    else:
        # ran out of turns without a final message
        if not result.final_message:
            result.error = result.error or f"max_turns alcanzado ({spec.tools.max_turns})"

    result.wall_time_s = time.monotonic() - start
    if sum_eval_duration_ns > 0 and result.tokens_out > 0:
        result.tps_decode = result.tokens_out / (sum_eval_duration_ns / 1e9)

    return result
