"""工作流请求 schema。响应复用 shared 的 WorkflowSummary。"""

from typing import Any

from comfyportal_shared.dto import Slot
from pydantic import BaseModel


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    prompt_api: dict[str, Any]
    slots: list[Slot] = []
    model_refs: list[str] = []
