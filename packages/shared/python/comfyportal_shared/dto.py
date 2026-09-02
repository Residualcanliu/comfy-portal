"""API DTO（规格书 §4 数据模型 + §5 API 设计）。

与 TS 侧 packages/shared/ts/src/dto.ts 保持同步。
加了 `from_attributes=True`，使这些 DTO 可直接作为 FastAPI 的 response_model 接收 ORM 对象。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class Slot(BaseModel):
    """工作流参数槽（规格书 §2 slots 参数槽）。"""

    model_config = ConfigDict(from_attributes=True)

    key: str
    node: str
    input: str
    type: Literal["text", "int", "float"]
    required: bool = True
    label: str
    min: Optional[float] = None
    max: Optional[float] = None
    default: Optional[str | int | float] = None


class WorkflowSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    slots: list[Slot] = []
    model_refs: list[str] = []
    is_official: bool = False
    available: bool = True


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: str
    attempt: int
    params: dict
    model_variant: str
    error: Optional[str] = None
    comfy_prompt_id: Optional[str] = None
    created_at: datetime
    enqueued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class Artifact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    kind: str
    filename: str
    size_bytes: int
    width: int
    height: int
    created_at: datetime
