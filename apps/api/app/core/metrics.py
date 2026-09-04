"""Prometheus 指标（规格书 §7）。"""

from prometheus_client import Counter, Gauge, Histogram

# 任务数（按状态，rate 可得日任务数）
TASKS_TOTAL = Counter("comfyui_tasks_total", "任务总数", ["status"])

# 生成耗时（started→finished，按 variant + status 分线）
TASK_DURATION = Histogram(
    "comfyui_task_duration_seconds",
    "生成耗时（started→finished）",
    ["variant", "status"],
)

# 队列等待（enqueued→started）
QUEUE_WAIT = Histogram("comfyui_queue_wait_seconds", "队列等待（enqueued→started）")

# 队列长度（LLEN）
QUEUE_LENGTH = Gauge("comfyui_queue_length", "当前队列长度")

# GPU 在线状态（心跳）
GPU_ONLINE = Gauge("comfyui_gpu_online", "GPU 在线状态（1=在线）")
