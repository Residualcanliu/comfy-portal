"""系统状态（规格书 §5 GET /api/status，无需登录）。"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.metrics import GPU_ONLINE, QUEUE_LENGTH
from app.core.redis import generation_queue, redis_client
from app.models.artifact import Artifact
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


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """公开只读统计，用于演示页展示系统规模与运行结果。

    只做聚合查询，不暴露用户信息，也不涉及生成能力。
    """
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    success = (
        db.query(func.count(Task.id)).filter(Task.status == "success").scalar() or 0
    )
    failed = db.query(func.count(Task.id)).filter(Task.status == "failed").scalar() or 0
    cancelled = (
        db.query(func.count(Task.id)).filter(Task.status == "cancelled").scalar() or 0
    )
    total_artifacts = db.query(func.count(Artifact.id)).scalar() or 0

    # 最近 200 条成功任务的平均耗时，避免全表扫描
    rows = (
        db.query(Task.started_at, Task.finished_at)
        .filter(
            Task.status == "success",
            Task.started_at.isnot(None),
            Task.finished_at.isnot(None),
        )
        .order_by(Task.finished_at.desc())
        .limit(200)
        .all()
    )
    durations: list[float] = []
    for started, finished in rows:
        if started is None or finished is None:
            continue
        seconds = (finished - started).total_seconds()
        if seconds >= 0:
            durations.append(seconds)
    avg_duration = round(sum(durations) / len(durations), 1) if durations else None

    finished_total = success + failed
    return {
        "gpu_online": bool(redis_client.exists("worker:heartbeat")),
        "queue_length": generation_queue.count,
        "pending_tasks": db.query(func.count(Task.id))
        .filter(Task.status == "queued")
        .scalar()
        or 0,
        "readonly_demo": settings.readonly_demo,
        "totals": {
            "tasks": total_tasks,
            "success": success,
            "failed": failed,
            "cancelled": cancelled,
            "artifacts": total_artifacts,
        },
        "success_rate": round(success / finished_total, 3) if finished_total else None,
        "avg_duration_seconds": avg_duration,
    }
