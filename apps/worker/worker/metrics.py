"""worker Prometheus 指标（规格书 §6）：VRAM 采样 + /metrics（绑 9101）。

独立进程运行：
    python -m worker.metrics
"""

import logging
import os
import threading
import time

import httpx
from prometheus_client import Gauge, start_http_server

from worker.config import settings

logger = logging.getLogger(__name__)

VRAM_USED = Gauge("comfyui_gpu_vram_used_bytes", "GPU 已用显存（字节）")


def _sample_vram() -> None:
    while True:
        try:
            d = httpx.get(f"{settings.comfyui_url}/system_stats", timeout=10).json()
            dev = d["devices"][0]
            VRAM_USED.set(dev["vram_total"] - dev["vram_free"])
        except Exception:
            logger.exception("VRAM 采样失败")
        time.sleep(10)


def main() -> None:
    # prometheus_client 的 start_http_server 默认 addr='0.0.0.0'，会让这台日常使用的
    # Windows 主机把 9101 暴露给同局域网任何设备。默认收紧到回环。
    # 需要跨机抓取（deploy/prometheus.yml 抓 __WORKER_IP__:9101）时，
    # 在 .env 里显式设 METRICS_ADDR 为该主机的 tailnet IP。
    addr = os.environ.get("METRICS_ADDR", "127.0.0.1")
    start_http_server(settings.metrics_port, addr=addr)
    threading.Thread(target=_sample_vram, daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
