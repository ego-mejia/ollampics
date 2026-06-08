"""HTTP client wrapper around Ollama's local API.

Lives at localhost:11434 by default. Exposes:
  - list_models()           — what's installed
  - pull(name)              — download a model (yields progress)
  - generate(...)           — single-shot generation with streaming + metrics
  - ps()                    — currently loaded models, for VRAM probing
  - stop(name)              — unload via subprocess `ollama stop`

The metrics returned by generate() come from Ollama's `done` event:
  - prompt_eval_count       — input tokens
  - eval_count              — output tokens
  - eval_duration (ns)      — pure decode time
  - prompt_eval_duration    — prompt processing time
We compute time-to-first-token from wall clock around the stream.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ollympics.core.config import settings


@dataclass
class GenerateResult:
    text: str
    ttft_ms: int | None
    wall_time_s: float
    tokens_in: int | None
    tokens_out: int | None
    tps_decode: float | None
    raw_final: dict[str, Any] = field(default_factory=dict)


class OllamaClient:
    def __init__(self, host: str | None = None, timeout: float = 600.0) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.timeout = timeout

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{self.host}/api/tags")
            r.raise_for_status()
            return r.json().get("models", [])

    async def ps(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                r = await client.get(f"{self.host}/api/ps")
                r.raise_for_status()
                return r.json().get("models", [])
            except httpx.HTTPError:
                return []

    async def show(self, name: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{self.host}/api/show", json={"name": name})
            r.raise_for_status()
            return r.json()

    async def pull(self, name: str) -> None:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{self.host}/api/pull", json={"name": name}
            ) as resp:
                resp.raise_for_status()
                async for _line in resp.aiter_lines():
                    pass

    async def stop(self, name: str) -> None:
        """Unload a model from memory. Uses subprocess as a fallback for older Ollama."""
        proc = await asyncio.create_subprocess_exec(
            "ollama", "stop", name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            proc.kill()

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        options: dict[str, Any] | None = None,
        timeout_s: float = 120.0,
    ) -> GenerateResult:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        chunks: list[str] = []
        ttft_ms: int | None = None
        final: dict[str, Any] = {}
        start = time.monotonic()

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            async with client.stream(
                "POST", f"{self.host}/api/generate", json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = evt.get("response", "")
                    if text and ttft_ms is None:
                        ttft_ms = int((time.monotonic() - start) * 1000)
                    if text:
                        chunks.append(text)
                    if evt.get("done"):
                        final = evt

        wall = time.monotonic() - start
        tokens_in = final.get("prompt_eval_count")
        tokens_out = final.get("eval_count")
        eval_duration_ns = final.get("eval_duration")
        tps_decode: float | None = None
        if tokens_out and eval_duration_ns:
            seconds = eval_duration_ns / 1e9
            if seconds > 0:
                tps_decode = tokens_out / seconds

        return GenerateResult(
            text="".join(chunks),
            ttft_ms=ttft_ms,
            wall_time_s=wall,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tps_decode=tps_decode,
            raw_final=final,
        )

    async def warmup(self, model: str, options: dict[str, Any] | None = None) -> None:
        """One-shot tiny prompt to warm up KV cache and weights."""
        await self.generate(
            model=model,
            prompt="ok",
            options={**(options or {}), "num_predict": 1},
            timeout_s=60.0,
        )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
        timeout_s: float = 180.0,
    ) -> dict[str, Any]:
        """Non-streaming chat. Returns the full Ollama response with `message` and timings."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        if options:
            payload["options"] = options
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.post(f"{self.host}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()
