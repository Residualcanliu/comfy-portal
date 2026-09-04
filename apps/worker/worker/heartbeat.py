"""worker 心跳（规格书 §6）：每 30s 写 worker:heartbeat（TTL 60s）。

独立进程运行，与 rq worker 并行：
    python -m worker.heartbeat
"""

import time

import redis

from worker.config import settings

INTERVAL = 30  # 秒
TTL = 60


def main() -> None:
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    while True:
        r.set("worker:heartbeat", "1", ex=TTL)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
