"""系统状态（规格书 §5 GET /api/status，无需登录）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.metrics import GPU_ONLINE, QUEUE_LENGTH
from app.core.redis import generation_queue, redis_client
from app.models.task import Task

router = APIRouter()


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict:
    gpu_online = bool(redis_client.exists("worker:heartbeat"))
    queue_length = generation_queue.count
    pending_tasks = db.query(Task).filter(Task.status == "queued").count()

    GPU_ONLINE.set(1 if gpu_online else 0)
    QUEUE_LENGTH.set(queue_length)
    return {
        "gpu_online": gpu_online,
        "queue_length": queue_length,
        "pending_tasks": pending_tasks,
        # 前端据此切换「开始生成 / 浏览工作流」与演示声明
        "readonly_demo": settings.readonly_demo,
    }
