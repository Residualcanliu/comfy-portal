"""worker Prometheus 指标（规格书 §6）：VRAM 采样 + /metrics（绑 9101）。

独立进程运行：
    python -m worker.metrics
"""

import logging
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
    start_http_server(settings.metrics_port)  # 9101，Prometheus 抓取目标
    threading.Thread(target=_sample_vram, daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
