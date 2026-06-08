from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ollympics.core.ollama import OllamaClient

router = APIRouter()


class ModelInfo(BaseModel):
    name: str
    size_bytes: int
    modified_at: str | None = None


@router.get("/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    client = OllamaClient()
    try:
        raw = await client.list_models()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama no responde: {e}") from e
    return [
        ModelInfo(
            name=m.get("name", "?"),
            size_bytes=m.get("size", 0),
            modified_at=m.get("modified_at"),
        )
        for m in raw
    ]
