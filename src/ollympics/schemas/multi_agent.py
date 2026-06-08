from __future__ import annotations

from pydantic import BaseModel, Field


class MultiAgentSpec(BaseModel):
    """Multi-rol research workflow: Researcher → Critic → Writer.

    Substitute for the CrewAI integration mentioned in the blueprint —
    CrewAI pins rich<13.7 and typer<0.9 which conflict with the project's
    pinned versions, so we implement the same role-based pattern with the
    LangGraph runtime that's already in the stack.
    """

    iterations: int = 1
    researcher_system: str | None = None
    critic_system: str | None = None
    writer_system: str | None = None
