from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class RegexVerifier(BaseModel):
    type: Literal["regex"]
    pattern: str
    flags: str = ""


class ExactMatchVerifier(BaseModel):
    type: Literal["exact_match"]
    expected: str | list[str]
    case_sensitive: bool = False
    fuzzy: bool = False


class JsonSchemaVerifier(BaseModel):
    type: Literal["json_schema"]
    schema_: dict[str, Any] = Field(alias="schema")


class CompositeVerifier(BaseModel):
    type: Literal["composite"]
    all_of: list[Verifier] | None = None
    any_of: list[Verifier] | None = None


class LLMJudgeVerifier(BaseModel):
    type: Literal["llm_judge"]
    rubric: str
    pass_threshold: float = 0.7
    judge_model: str | None = None  # override; defaults to LLM_MODEL from .env


class ExpectedCall(BaseModel):
    tool: str
    args_schema: dict[str, Any] | None = None


class ToolTraceVerifier(BaseModel):
    type: Literal["tool_trace"]
    expected_calls: list[ExpectedCall] = Field(default_factory=list)
    final_message: "Verifier | None" = None
    allow_extra_calls: bool = False
    strict_order: bool = False
    max_format_errors: int = 0


class PersonalAgentVerifier(BaseModel):
    type: Literal["personal_agent"]
    min_recall_rate: float = 0.66
    min_tool_fidelity: float = 0.6
    require_closing_summary: bool = True


Verifier = Annotated[
    RegexVerifier
    | ExactMatchVerifier
    | JsonSchemaVerifier
    | CompositeVerifier
    | LLMJudgeVerifier
    | ToolTraceVerifier
    | PersonalAgentVerifier,
    Field(discriminator="type"),
]


CompositeVerifier.model_rebuild()
ToolTraceVerifier.model_rebuild()
