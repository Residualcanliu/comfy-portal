"""worker 心跳（规格书 §6）：每 30s 写 worker:heartbeat（TTL 60s）。

独立进程运行，与 rq worker 并行：
    python -m worker.heartbeat
"""

import logging
import time

import redis

from worker.config import settings

logger = logging.getLogger(__name__)

INTERVAL = 30  # 秒
TTL = 60


def main() -> None:
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    while True:
        try:
            r.set("worker:heartbeat", "1", ex=TTL)
        except Exception:
            logger.exception("心跳写入失败，下次重试")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
