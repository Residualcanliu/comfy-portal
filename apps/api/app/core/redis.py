"""Redis 客户端 + RQ 队列。"""

from app.core.config import settings
import redis
import redis.asyncio as aioredis
from rq import Queue

# 同步客户端（状态 / 配额 / pub/sub 发布），字符串解码
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# RQ 队列用独立连接（RQ 需要原始字节）
_rq_conn = redis.Redis.from_url(settings.redis_url, decode_responses=False)
generation_queue = Queue("generation", connection=_rq_conn)

# 异步客户端（SSE 订阅转发）
async_redis = aioredis.from_url(settings.redis_url, decode_responses=True)
