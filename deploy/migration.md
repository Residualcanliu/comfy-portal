# GPU 节点迁移 Runbook（规格书 §10，2027-06 还电脑时用）

> 原则：GitHub 为唯一事实源，VPS 零改动。新机器全程 1–2h。

## 步骤

1. 新机器装 Python 3.11+ + git + Tailscale（加入同一 tailnet）
2. `git clone` 仓库 → `pip install -e .`（api/worker 各自 venv）
3. 按 `scripts/models.txt` 重下模型（~20GB，hf-mirror，1–2h）
4. 配 Windows 任务计划程序开机自启（.bat 起 ComfyUI → 等健康 → 起 rq worker）
5. 电源"接通电源永不睡眠"
6. 验证：提交一个测试任务，确认 SSE 进度 + 画廊出图

## 关键目录（老师机器）

- `D:\ComfyUI` — ComfyUI 本体
- `D:\comfy-portal-worker` — worker，README 说明用途
