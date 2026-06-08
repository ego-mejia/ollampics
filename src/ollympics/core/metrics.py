"""Background sampler for hardware metrics during a task attempt.

Captures:
  - peak_vram_mb: polls `GET /api/ps` and tracks the model's `size_vram` field.
    No special permissions needed.
  - avg_watts: parses output of `powermetrics --samplers gpu_power`. Opt-in.
    Requires sudo. Falls back gracefully (returns None) if it fails.

Usage:
    async with MetricsSampler(model_name) as s:
        await client.generate(...)
    print(s.peak_vram_mb, s.avg_watts)
"""

from __future__ import annotations

import asyncio
import re
import shutil

import httpx

from ollympics.core.config import settings

_WATTS_LINE = re.compile(r"GPU Power:\s+(\d+)\s+mW", re.IGNORECASE)


class MetricsSampler:
    def __init__(
        self,
        model_name: str,
        *,
        host: str | None = None,
        interval_ms: int | None = None,
        enable_watts: bool | None = None,
    ) -> None:
        self.model_name = model_name
        self.host = (host or settings.ollama_host).rstrip("/")
        self.interval = (interval_ms or settings.sampler_interval_ms) / 1000.0
        self.enable_watts = (
            enable_watts if enable_watts is not None else settings.enable_watts
        )

        self._peak_vram_bytes: int = 0
        self._watts_samples: list[float] = []
        self._stop = False
        self._vram_task: asyncio.Task | None = None
        self._pm_proc: asyncio.subprocess.Process | None = None
        self._pm_reader: asyncio.Task | None = None

    @property
    def peak_vram_mb(self) -> int | None:
        if self._peak_vram_bytes <= 0:
            return None
        return self._peak_vram_bytes // (1024 * 1024)

    @property
    def avg_watts(self) -> float | None:
        if not self._watts_samples:
            return None
        return sum(self._watts_samples) / len(self._watts_samples)

    async def __aenter__(self) -> MetricsSampler:
        self._vram_task = asyncio.create_task(self._sample_vram_loop())
        if self.enable_watts:
            await self._start_powermetrics()
        return self

    async def __aexit__(self, *_exc) -> None:
        self._stop = True
        if self._vram_task is not None:
            try:
                await asyncio.wait_for(self._vram_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._vram_task.cancel()
        await self._stop_powermetrics()

    async def _sample_vram_loop(self) -> None:
        async with httpx.AsyncClient(timeout=2.0) as client:
            while not self._stop:
                try:
                    r = await client.get(f"{self.host}/api/ps")
                    if r.status_code == 200:
                        for m in r.json().get("models", []):
                            if (
                                m.get("name") == self.model_name
                                or m.get("model") == self.model_name
                            ):
                                vram = int(m.get("size_vram", 0) or 0)
                                if vram > self._peak_vram_bytes:
                                    self._peak_vram_bytes = vram
                                break
                except Exception:
                    pass
                await asyncio.sleep(self.interval)

    async def _start_powermetrics(self) -> None:
        if shutil.which("powermetrics") is None:
            return
        try:
            interval_ms = int(self.interval * 1000)
            self._pm_proc = await asyncio.create_subprocess_exec(
                "sudo",
                "-n",
                "powermetrics",
                "--samplers",
                "gpu_power",
                "-i",
                str(interval_ms),
                "-n",
                "100000",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception:
            self._pm_proc = None
            return

        self._pm_reader = asyncio.create_task(self._read_powermetrics())

    async def _read_powermetrics(self) -> None:
        if self._pm_proc is None or self._pm_proc.stdout is None:
            return
        try:
            while not self._stop:
                line = await self._pm_proc.stdout.readline()
                if not line:
                    return
                m = _WATTS_LINE.search(line.decode(errors="ignore"))
                if m:
                    self._watts_samples.append(int(m.group(1)) / 1000.0)
        except Exception:
            return

    async def _stop_powermetrics(self) -> None:
        if self._pm_proc is None:
            return
        try:
            self._pm_proc.terminate()
            try:
                await asyncio.wait_for(self._pm_proc.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                self._pm_proc.kill()
                await self._pm_proc.wait()
        except Exception:
            pass
        if self._pm_reader is not None:
            self._pm_reader.cancel()
            try:
                await self._pm_reader
            except (asyncio.CancelledError, Exception):
                pass
