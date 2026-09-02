// API DTO（规格书 §4 数据模型 + §5 API 设计）
// 变更时必须同步 packages/shared/python/comfyportal_shared/dto.py

export type SlotType = "text" | "int" | "float";

/** 工作流参数槽（规格书 §2 slots 参数槽） */
export interface Slot {
  key: string;
  node: string;
  input: string;
  type: SlotType;
  required: boolean;
  label: string;
  min?: number;
  max?: number;
  default?: string | number;
}

export interface WorkflowSummary {
  id: number;
  name: string;
  description: string | null;
  slots: Slot[];
  model_refs: string[];
  is_official: boolean;
  available: boolean;
}

export interface TaskSummary {
  id: number;
  workflow_id: number;
  status: TaskStatus;
  attempt: number;
  params: Record<string, unknown>;
  model_variant: string;
  error: string | null;
  comfy_prompt_id: string | null;
  created_at: string;
  enqueued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Artifact {
  id: number;
  task_id: number;
  kind: string;
  filename: string;
  size_bytes: number;
  width: number;
  height: number;
  created_at: string;
}
