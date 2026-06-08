from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TurnType = Literal["scripted_user", "recall_probe", "closing_summary"]


class ExpectedToolCall(BaseModel):
    name: str
    args_schema: dict[str, Any] | None = None


class TurnSpec(BaseModel):
    """One scripted user turn in a Personal Agent task."""

    turn: int
    type: TurnType = "scripted_user"
    message: str
    plants: dict[str, str] = Field(default_factory=dict)
    expect_tool: ExpectedToolCall | None = None
    # For recall_probe: list of substrings the assistant's reply must contain
    # (any-of). Case-insensitive substring match.
    expect_substr_any: list[str] = Field(default_factory=list)
    # For closing_summary: substrings the reply must mention (all-of).
    expect_substr_all: list[str] = Field(default_factory=list)


class PersonalAgentSpec(BaseModel):
    """Multi-turn conversational benchmark with tools + recall probes."""

    tools_enabled: list[str] = Field(default_factory=list)
    script: list[TurnSpec]
    # Cap on assistant turns generated; the runner won't iterate past this.
    max_turns: int = 25
