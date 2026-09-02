"""ComfyPortal 共享契约：任务状态机 + SSE 事件 + DTO（与 TS 侧 packages/shared/ts 双份同步）。"""

from .task_state import TaskStatus, TERMINAL_STATES
from .events import (
    ArtifactSummary,
    StatusPayload,
    ProgressPayload,
    DonePayload,
    ErrorPayload,
)
from .dto import Slot, WorkflowSummary, TaskSummary, Artifact

__all__ = [
    "TaskStatus",
    "TERMINAL_STATES",
    "ArtifactSummary",
    "StatusPayload",
    "ProgressPayload",
    "DonePayload",
    "ErrorPayload",
    "Slot",
    "WorkflowSummary",
    "TaskSummary",
    "Artifact",
]
