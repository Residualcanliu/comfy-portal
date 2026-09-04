"""GPU 离线陈旧恢复（规格书 §1 关机设计）。

心跳丢失 → running 任务 10min 无 progress（last_activity 过期）→
    attempt < 2 → 回队列（attempt+1），否则 failed。
"""

import logging
import threading
import time
from datetime import UTC, datetime

from app.core.prompt import resolve_prompt_api
from app.core.redis import generation_queue, redis_client
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30  # 秒


def _stale_check() -> None:
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            if redis_client.exists("worker:heartbeat"):
                continue  # GPU 在线，跳过

            db = SessionLocal()
            try:
                running = db.query(Task).filter(Task.status == "running").all()
                for task in running:
                    # last_activity 由 worker 每次 progress 刷新（TTL 600s）；不存在=10min 无进度
                    if redis_client.exists(f"task:{task.id}:last_activity"):
                        continue
                    if task.attempt < 2:
                        task.status = "queued"
                        task.attempt += 1
                        task.started_at = None
                        wf = db.get(Workflow, task.workflow_id)
                        resolved = resolve_prompt_api(wf.prompt_api, wf.slots, task.params)
                        db.commit()
                        generation_queue.enqueue(
                            "worker.main.run_job",
                            task.id,
                            resolved,
                            job_timeout=1800,
                            result_ttl=0,
                        )
                    else:
                        task.status = "failed"
                        task.error = "GPU 离线，任务超时（attempt 耗尽）"
                        task.finished_at = datetime.now(UTC)
                        db.commit()
            finally:
                db.close()
        except Exception:  # 后台线程必须兜底，不崩
            logger.exception("陈旧恢复检查失败")


def start_stale_recovery() -> None:
    threading.Thread(target=_stale_check, daemon=True).start()
