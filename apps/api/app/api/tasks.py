"""任务提交 / 查询 / 取消 / SSE（规格书 §5）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user, get_db
from app.core.metrics import TASKS_TOTAL
from app.core.prompt import resolve_prompt_api
from app.core.redis import async_redis, generation_queue, redis_client
from app.models.task import Task
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.task import TaskCreate
from comfyportal_shared.dto import TaskSummary

router = APIRouter()


@router.post("/tasks", response_model=TaskSummary, status_code=202)
def create_task(
    body: TaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    wf = db.get(Workflow, body.workflow_id)
    if wf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    # 日配额检查（redis quota:{uid}:{date}，INCR 原子计数，超限回滚）
    quota_key = f"quota:{user.id}:{datetime.now(UTC).strftime('%Y-%m-%d')}"
    used = redis_client.incr(quota_key)
    if used == 1:
        redis_client.expire(quota_key, 86400)  # 每天自然过期（date 在 key 里已按天隔离）
    if used > user.daily_quota:
        redis_client.decr(quota_key)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="今日配额已用完")

    resolved = resolve_prompt_api(wf.prompt_api, wf.slots, body.params)

    task = Task(
        user_id=user.id,
        workflow_id=body.workflow_id,
        status="queued",
        params=body.params,
        model_variant=body.model_variant,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    TASKS_TOTAL.labels(status="queued").inc()

    # 入队：把 resolved prompt_api 一并传给 worker（worker 不直连 PG）
    generation_queue.enqueue(
        "worker.main.run_job", task.id, resolved, job_timeout=1800, result_ttl=0
    )
    task.enqueued_at = datetime.now(UTC)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskSummary])
def list_tasks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100),
    offset: int = 0,
) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.user_id == user.id)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/tasks/{task_id}", response_model=TaskSummary)
def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.post("/tasks/{task_id}/cancel", status_code=204)
def cancel_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.status != "queued":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="仅排队中任务可取消")
    task.status = "cancelled"
    task.finished_at = datetime.now(UTC)
    db.commit()


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: int, db: Session = Depends(get_db)) -> EventSourceResponse:
    """SSE：先发当前状态，再转发 worker 经 Redis pub/sub 推送的进度/完成/错误。"""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")

    channel = f"task:{task_id}"
    pubsub = async_redis.pubsub()
    await pubsub.subscribe(channel)

    async def event_stream():
        try:
            # 连接时先补发当前状态
            yield {
                "event": "status",
                "data": json.dumps({"state": task.status}),
            }
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                payload = json.loads(message["data"])
                # worker 发布格式：{"event": <status|progress|done|error>, "data": {...}}
                yield {
                    "event": payload["event"],
                    "data": json.dumps(payload["data"]),
                }
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return EventSourceResponse(event_stream())
