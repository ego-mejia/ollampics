from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ollympics.api.routes import (
    attempts,
    compare,
    health,
    leaderboard,
    models,
    runs,
    suites,
    tests,
    ws,
)
from ollympics.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="OLLAMPICS API",
    version="0.1.0",
    description="Benchmark harness for local LLMs.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(suites.router, prefix="/api", tags=["suites"])
app.include_router(runs.router, prefix="/api", tags=["runs"])
app.include_router(attempts.router, prefix="/api", tags=["attempts"])
app.include_router(leaderboard.router, prefix="/api", tags=["leaderboard"])
app.include_router(tests.router, prefix="/api", tags=["tests"])
app.include_router(compare.router, prefix="/api", tags=["compare"])
app.include_router(ws.router, prefix="/api", tags=["ws"])

# In production / docker, serve the built frontend from /. In dev (vite),
# this directory doesn't exist and the API stays on its own.
_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")
    _icons = _dist / "icons"
    if _icons.is_dir():
        app.mount("/icons", StaticFiles(directory=_icons), name="icons")

    _dist_resolved = _dist.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str) -> FileResponse:
        if full_path:
            candidate = (_dist / full_path).resolve()
            if candidate.is_file() and _dist_resolved in candidate.parents:
                return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
