"""RQ worker 入口。

M1 阶段实现 run_job 全流程（规格书 §6）：
  1. 取任务（含 resolved prompt_api）
  2. POST ComfyUI /prompt → prompt_id
  3. 连 ws://127.0.0.1:8188/ws?clientId=uuid
  4. 循环收 progress/executing/executed，算 pct，publish task:{id}
  5. 产物读文件 → Pillow 压缩 → 上传 /internal/artifacts/upload → 本地删
  6. /internal state=success / failed

心跳线程（30s 写 worker:heartbeat，TTL 60s）与 /metrics 在 M2/M3 补齐。
"""
