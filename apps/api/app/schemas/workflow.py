"""工作流请求 schema。响应复用 shared 的 WorkflowSummary。"""

from typing import Any

from pydantic import BaseModel

from comfyportal_shared.dto import Slot


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    prompt_api: dict[str, Any]
    slots: list[Slot] = []
    model_refs: list[str] = []
