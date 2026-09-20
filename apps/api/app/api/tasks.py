"""任务提交 / 查询 / 取消 / SSE（规格书 §5）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user, get_db
from app.core.metrics import TASKS_TOTAL
from app.core.prompt import check_prompt, resolve_prompt_api
from app.core.redis import async_redis, generation_queue, redis_client
from app.core.security import (
    SSE_TICKET_TTL_SECONDS,
    create_sse_ticket,
    decode_sse_ticket,
)
from app.models.task import Task
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.task import TaskCreate
from comfyportal_shared.dto import TaskSummary

# 路由级默认认证：本模块所有端点都要求登录。个别端点仍需在签名里再取一次
# `user` 用于归属校验，FastAPI 会复用同一次请求的依赖结果，不会重复解析 token。
# 这样放是防止以后新增端点时忘了在签名里挂认证（task_events 就是这么漏掉的）。
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/tasks", response_model=TaskSummary, status_code=202)
def create_task(
    body: TaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    wf = db.get(Workflow, body.workflow_id)
    # 只能跑官方工作流或自己的工作流。不判归属的话，任何人可以拿别人的私有工作流
    # id 提交任务，从产物反推其 prompt_api 与模型配置。
    if wf is None or (wf.user_id != user.id and not wf.is_official):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    # 违规 prompt 检测（含色情/违规词直接拒绝）
    prompt_text = str(body.params.get("prompt") or "")
    if check_prompt(prompt_text):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="提示词包含违规内容，请修改后重试")

    # 日配额检查（管理员跳过；redis quota:{uid}:{date}，INCR 原子计数，超限回滚）
    if not user.is_admin:
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


# SSE 用独立 router：浏览器的 EventSource 不能自定义请求头，这个端点只能把凭证
# 放进 query string。因此它不能挂 router 级的 Authorization 认证，改走短时票据。
events_router = APIRouter()


@events_router.post("/tasks/{task_id}/ticket")
def create_task_ticket(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """签发一张 60 秒的 SSE 票据。需登录，且只能是任务属主本人。"""
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return {"ticket": create_sse_ticket(user.id), "expires_in": SSE_TICKET_TTL_SECONDS}


@events_router.get("/tasks/{task_id}/events")
async def task_events(
    task_id: int,
    ticket: str = Query(...),
    db: Session = Depends(get_db),
) -> EventSourceResponse:
    """SSE：先发当前状态，再转发 worker 经 Redis pub/sub 推送的进度/完成/错误。

    票据里带 user_id，但仍要重新校验任务归属 —— 票据只证明「是谁」，
    不证明「有权看这个任务」。
    """
    try:
        payload = decode_sse_ticket(ticket)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="无效票据")

    task = db.get(Task, task_id)
    if task is None or task.user_id != user_id:
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
