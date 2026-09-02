"""SSE 事件 payload（规格书 §5「SSE 协议」）。

与 TS 侧 packages/shared/ts/src/events.ts 保持同步。
event: 字段值为 status/progress/done/error，对应下方各 Payload。
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from .task_state import TaskStatus


class ArtifactSummary(BaseModel):
    id: int
    kind: str
    url: str
    width: int
    height: int


class StatusPayload(BaseModel):
    state: TaskStatus
    position: Optional[int] = None  # queued 时存在
    comfy_prompt_id: Optional[str] = None  # running 时存在


class ProgressPayload(BaseModel):
    pct: float  # 0-100
    node: str  # 当前节点，如 "KSampler"
    step: int
    max_steps: int


class DonePayload(BaseModel):
    state: Literal["success"]
    artifacts: list[ArtifactSummary]


class ErrorPayload(BaseModel):
    state: Literal["failed"]
    error: str
