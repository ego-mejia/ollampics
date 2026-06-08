from __future__ import annotations

from pydantic import BaseModel


class ToolsSpec(BaseModel):
    """Defines tool calling context for a task.

    `enabled` lists tool names from the global catalog that the model can call.
    `max_turns` caps the chat loop to prevent runaway loops.
    """

    enabled: list[str]
    max_turns: int = 6
