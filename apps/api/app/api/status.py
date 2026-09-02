"""系统状态（规格书 §5 GET /api/status，无需登录）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.redis import generation_queue, redis_client
from app.models.task import Task

router = APIRouter()


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict:
    gpu_online = bool(redis_client.exists("worker:heartbeat"))
    queue_length = generation_queue.count
    pending_tasks = db.query(Task).filter(Task.status == "queued").count()
    return {
        "gpu_online": gpu_online,
        "queue_length": queue_length,
        "pending_tasks": pending_tasks,
    }
