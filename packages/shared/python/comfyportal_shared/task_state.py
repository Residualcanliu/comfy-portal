"""任务状态机（规格书 §4 tasks.status）。

与 TS 侧 packages/shared/ts/src/task-state.ts 保持同步。
"""

from enum import Enum


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 终态：进入后不再流转
TERMINAL_STATES = frozenset({TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED})
