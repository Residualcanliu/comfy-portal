"""GPU 离线陈旧恢复（规格书 §1 关机设计）。

两件事：
1. 心跳丢失 → running 任务 10min 无 progress（last_activity 过期）→ 回队列重试。
2. queued 任务已不在 RQ 队列里（Redis 重启 / 队列丢失）→ 孤儿，重新入队。
"""

import logging
import threading
import time
from datetime import UTC, datetime

from rq import Job

from app.core.metrics import GPU_ONLINE
from app.core.prompt import resolve_prompt_api
from app.core.redis import generation_queue, redis_client, rq_conn
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30  # 秒
MAX_ATTEMPT = 2
# 宽限期：刚入队的任务先放过，避免 RQ 登记延迟造成误判
ORPHAN_GRACE_SECONDS = 120


def _enqueue(task: Task, db) -> None:
    """按 task 参数重新解析 prompt 并入队。"""
    wf = db.get(Workflow, task.workflow_id)
    if wf is None:
        return
    resolved = resolve_prompt_api(wf.prompt_api, wf.slots, task.params)
    generation_queue.enqueue(
        "worker.main.run_job", task.id, resolved, job_timeout=1800, result_ttl=0
    )


def _recover_running(db) -> None:
    """生成到一半因 GPU 掉线而卡死的任务。"""
    running = db.query(Task).filter(Task.status == "running").all()
    for task in running:
        # last_activity 由 worker 每次 progress 刷新（TTL 600s）；不存在=10min 无进度
        if redis_client.exists(f"task:{task.id}:last_activity"):
            continue
        if task.attempt < MAX_ATTEMPT:
            task.status = "queued"
            task.attempt += 1
            task.started_at = None
            db.commit()
            _enqueue(task, db)
            logger.warning("超时任务重新入队: task_id=%s attempt=%s", task.id, task.attempt)
        else:
            task.status = "failed"
            task.error = "GPU 离线，任务超时（attempt 耗尽）"
            task.finished_at = datetime.now(UTC)
            db.commit()


def _in_flight_task_ids() -> set[int] | None:
    """当前仍在 RQ 队列 / 执行中的 task_id 集合；读取失败返回 None。"""
    try:
        job_ids = set(generation_queue.get_job_ids())
        job_ids |= set(generation_queue.started_job_registry.get_job_ids())
        job_ids |= set(generation_queue.deferred_job_registry.get_job_ids())
        job_ids |= set(generation_queue.scheduled_job_registry.get_job_ids())
    except Exception:
        logger.exception("读取 RQ 队列失败")
        return None

    ids: set[int] = set()
    for job_id in job_ids:
        try:
            job = Job.fetch(job_id, connection=rq_conn)
            if job.args:
                ids.add(int(job.args[0]))  # run_job(task_id, prompt_api)
        except Exception:
            logger.warning("读取 RQ job 失败，跳过: job_id=%s", job_id, exc_info=True)
    return ids


def _recover_orphans(db) -> None:
    """queued 但已不在 RQ 队列里的孤儿任务 → 重新入队。"""
    inflight = _in_flight_task_ids()
    if inflight is None:
        return

    now = datetime.now(UTC)
    for task in db.query(Task).filter(Task.status == "queued").all():
        if task.id in inflight:
            continue
        enqueued = task.enqueued_at or task.created_at
        if enqueued is not None:
            if enqueued.tzinfo is None:  # SQLite 取出来可能是 naive
                enqueued = enqueued.replace(tzinfo=UTC)
            if (now - enqueued).total_seconds() < ORPHAN_GRACE_SECONDS:
                continue
        if task.attempt >= MAX_ATTEMPT:
            task.status = "failed"
            task.error = "任务从队列丢失，重试次数耗尽"
            task.finished_at = now
            db.commit()
            continue
        task.attempt += 1
        task.enqueued_at = now
        db.commit()
        _enqueue(task, db)
        logger.warning("孤儿任务重新入队: task_id=%s attempt=%s", task.id, task.attempt)


def _stale_check() -> None:
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            gpu_online = redis_client.exists("worker:heartbeat")
            GPU_ONLINE.set(1 if gpu_online else 0)

            db = SessionLocal()
            try:
                # 孤儿任务与 GPU 是否在线无关，始终检查
                _recover_orphans(db)
                if not gpu_online:
                    _recover_running(db)
            finally:
                db.close()
        except Exception:  # 后台线程必须兜底，不崩
            logger.exception("陈旧恢复检查失败")


def start_stale_recovery() -> None:
    threading.Thread(target=_stale_check, daemon=True).start()
