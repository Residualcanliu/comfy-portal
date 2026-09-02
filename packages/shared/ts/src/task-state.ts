// 任务状态机（规格书 §4 tasks.status）
// 变更时必须同步 packages/shared/python/comfyportal_shared/task_state.py

export const TASK_STATUSES = [
  "queued",
  "running",
  "success",
  "failed",
  "cancelled",
] as const;

export type TaskStatus = (typeof TASK_STATUSES)[number];

/** 终态：进入后不再流转 */
export const TERMINAL_STATES: ReadonlySet<TaskStatus> = new Set([
  "success",
  "failed",
  "cancelled",
]);

/** 模型变体，用于 A/B 量化对比（default / 各 GGUF 变体） */
export type ModelVariant = string;
