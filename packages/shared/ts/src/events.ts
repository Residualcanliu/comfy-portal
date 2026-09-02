// SSE 事件协议（规格书 §5「SSE 协议」）
// 变更时必须同步 packages/shared/python/comfyportal_shared/events.py

import type { TaskStatus } from "./task-state";

/** SSE 的 event: 字段值，前端按此分发 */
export type SSEEventType = "status" | "progress" | "done" | "error";

export interface ArtifactSummary {
  id: number;
  kind: string;
  url: string;
  width: number;
  height: number;
}

/** event: status */
export interface StatusPayload {
  state: TaskStatus;
  position?: number; // 队列位置，queued 时存在
  comfy_prompt_id?: string; // running 时存在
}

/** event: progress */
export interface ProgressPayload {
  pct: number; // 0-100
  node: string; // 当前节点，如 "KSampler"
  step: number;
  max_steps: number;
}

/** event: done */
export interface DonePayload {
  state: "success";
  artifacts: ArtifactSummary[];
}

/** event: error */
export interface ErrorPayload {
  state: "failed";
  error: string;
}

export type SSEPayload = StatusPayload | ProgressPayload | DonePayload | ErrorPayload;
