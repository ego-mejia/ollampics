from __future__ import annotations

from pydantic import BaseModel, Field

from ollympics.schemas.multi_agent import MultiAgentSpec
from ollympics.schemas.personal_agent import PersonalAgentSpec
from ollympics.schemas.planning import PlanningSpec
from ollympics.schemas.rag import RagContextSpec
from ollympics.schemas.tools import ToolsSpec
from ollympics.schemas.verifier import Verifier


class PromptSpec(BaseModel):
    system: str | None = None
    user: str


class TaskSpec(BaseModel):
    task_id: str
    version: int = 1
    suite: str
    description: str = ""
    max_tries: int = 1
    timeout_s: int = 60
    prompt: PromptSpec
    verifier: Verifier
    tools: ToolsSpec | None = None
    rag: RagContextSpec | None = None
    planning: PlanningSpec | None = None
    personal_agent: PersonalAgentSpec | None = None
    multi_agent: MultiAgentSpec | None = None
    metrics_focus: list[str] = Field(default_factory=list)
