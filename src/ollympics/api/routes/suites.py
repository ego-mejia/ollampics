from fastapi import APIRouter
from pydantic import BaseModel

from ollympics.suites.loader import list_suites, load_suite

router = APIRouter()


class TaskMeta(BaseModel):
    task_id: str
    version: int
    description: str
    max_tries: int


class SuiteMeta(BaseModel):
    name: str
    tasks: list[TaskMeta]


@router.get("/suites", response_model=list[SuiteMeta])
async def get_suites() -> list[SuiteMeta]:
    out: list[SuiteMeta] = []
    for name in list_suites():
        try:
            specs = load_suite(name)
        except Exception:
            specs = []
        out.append(
            SuiteMeta(
                name=name,
                tasks=[
                    TaskMeta(
                        task_id=s.task_id,
                        version=s.version,
                        description=s.description,
                        max_tries=s.max_tries,
                    )
                    for s in specs
                ],
            )
        )
    return out
