"""WebSocket for real-time run events.

Replaces the 2s HTTP polling in the frontend. The runner's `on_event`
callback funnels into `broadcast()`, which delivers the JSON-encoded
event to every connected subscriber for that run.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Global registry: run_id → set of active WebSocket connections.
_subscribers: dict[int, set[WebSocket]] = defaultdict(set)
_lock = asyncio.Lock()


async def broadcast(run_id: int, event: str, payload: dict[str, Any]) -> None:
    """Send an event to all connected subscribers of a run."""
    if run_id not in _subscribers or not _subscribers[run_id]:
        return
    msg = json.dumps({"event": event, "payload": payload})
    dead: list[WebSocket] = []
    async with _lock:
        for ws in list(_subscribers[run_id]):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _subscribers[run_id].discard(ws)


def make_broadcast_callback(run_id: int):
    """Build an `on_event` callback that routes runner events into the broadcast."""

    async def callback(event: str, payload: dict[str, Any]) -> None:
        await broadcast(run_id, event, payload)

    return callback


@router.websocket("/runs/{run_id}/ws")
async def run_events_ws(ws: WebSocket, run_id: int) -> None:
    """Client connects to live-tail a run. The server pushes JSON events as
    `{event, payload}`; the client never needs to send anything."""
    await ws.accept()
    async with _lock:
        _subscribers[run_id].add(ws)
    try:
        # Send an initial hello so the client knows it's connected
        await ws.send_text(json.dumps({"event": "ws.connected", "payload": {"run_id": run_id}}))
        # Hold the connection open until the client disconnects
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _subscribers[run_id].discard(ws)
