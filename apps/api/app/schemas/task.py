"""任务请求 schema。响应复用 shared 的 TaskSummary。"""

from typing import Any

from pydantic import BaseModel


class TaskCreate(BaseModel):
    workflow_id: int
    params: dict[str, Any] = {}
    model_variant: str = "default"
