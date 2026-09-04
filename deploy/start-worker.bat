@echo off
REM ComfyPortal 本地节点开机自启（规格书 §10）
REM 流程：起 ComfyUI → 等健康 → 起 rq worker + 心跳 + 指标
REM 用任务计划程序开机运行本脚本（不依赖登录会话）；电源设"接通电源永不睡眠"

REM 1. 起 ComfyUI（standalone；PYTHONUTF8=1 避免 GBK 编码打印 emoji 崩溃）
set PYTHONUTF8=1
start "ComfyUI" cmd /c "cd /d D:\Comfy-Desktop\ComfyUI-Installs\ALL\ComfyUI && .venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188"

REM 2. 等 ComfyUI 健康（8188 响应）
:wait_health
timeout /t 5 /nobreak >nul
curl -s http://127.0.0.1:8188/system_stats >nul 2>&1
if errorlevel 1 goto wait_health

REM 3. 起 worker（SimpleWorker，Windows 无 fork）+ 心跳 + 指标
cd /d D:\claudework\work\2026年-09月-02日-ComfyPortal\comfy-portal\apps\worker
set VENV=D:\claudework\work\2026年-09月-02日-ComfyPortal\comfy-portal\.venv\Scripts
start "rq-worker" cmd /c "%VENV%\rq.exe worker generation -w rq.worker.SimpleWorker"
start "heartbeat" cmd /c "%VENV%\python.exe -m worker.heartbeat"
start "metrics"   cmd /c "%VENV%\python.exe -m worker.metrics"

echo ComfyPortal 本地节点已启动（ComfyUI + worker + 心跳 + 指标）
