"""内部接口（规格书 §5，仅 tailnet 8001 端口，双闸门校验）。"""

from __future__ import annotations

from datetime import UTC, datetime
import ipaddress
import os
import uuid

from comfyportal_shared import TaskStatus
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.metrics import QUEUE_WAIT, TASK_DURATION, TASKS_TOTAL
from app.models.artifact import Artifact
from app.models.task import Task

router = APIRouter()


def verify_internal(
    request: Request,
    x_internal_token: str = Header(default=""),
) -> None:
    """双闸门（§1）：X-Internal-Token + 源 IP ∈ tailnet CIDR。"""
    if x_internal_token != settings.internal_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid internal token")
    ip = request.client.host if request.client else ""
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="invalid IP")
    # 允许 tailnet + 本地回环（M1 本地 dev；M4 部署时收紧为仅 tailnet）
    if ip_obj.is_loopback or ip_obj in ipaddress.ip_network(settings.tailnet_cidr):
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="source IP not in tailnet")


class StateUpdate(BaseModel):
    state: TaskStatus
    error: str | None = None
    comfy_prompt_id: str | None = None


def _as_aware(dt: datetime | None) -> datetime | None:
    """SQLite 存的是 naive datetime，补上 UTC 时区，避免和 aware 时间相减报错。"""
    if dt is None or dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=UTC)


@router.post("/tasks/{task_id}/state", dependencies=[Depends(verify_internal)])
def update_state(
    task_id: int, body: StateUpdate, db: Session = Depends(get_db)
) -> dict:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")

    task.status = body.state.value
    if body.error is not None:
        task.error = body.error
    if body.comfy_prompt_id is not None:
        task.comfy_prompt_id = body.comfy_prompt_id

    now = datetime.now(UTC)
    if body.state == TaskStatus.RUNNING and task.started_at is None:
        task.started_at = now
        enq = _as_aware(task.enqueued_at)
        if enq is not None:
            QUEUE_WAIT.observe((now - enq).total_seconds())
    if body.state in (TaskStatus.SUCCESS, TaskStatus.FAILED):
        task.finished_at = now
        st = _as_aware(task.started_at)
        if st is not None:
            TASK_DURATION.labels(variant=task.model_variant, status=task.status).observe(
                (now - st).total_seconds()
            )
        TASKS_TOTAL.labels(status=task.status).inc()

    db.commit()
    return {"ok": True}


@router.post("/artifacts/upload", dependencies=[Depends(verify_internal)])
async def upload_artifact(
    task_id: int = Form(...),
    kind: str = Form("image"),
    width: int = Form(...),
    height: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="任务不存在")

    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"{task_id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(settings.artifacts_dir, filename)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    artifact = Artifact(
        task_id=task_id,
        kind=kind,
        filename=filename,
        size_bytes=len(content),
        width=width,
        height=height,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return {"id": artifact.id, "url": f"/files/{filename}"}
