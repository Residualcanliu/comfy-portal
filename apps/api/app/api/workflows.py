"""工作流 CRUD（规格书 §5）。响应复用 shared 的 WorkflowSummary。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate
from comfyportal_shared.dto import WorkflowSummary

router = APIRouter()


def _visible_to(user: User | None):
    """可见性条件：官方工作流对所有人可见，私有工作流仅本人可见。

    未登录（user is None）时只剩官方那一条 —— 官网落地页与 /create/{id} 都靠这个
    保持对游客可用，同时不泄露他人的私有工作流。
    """
    cond = Workflow.is_official.is_(True)
    if user is not None:
        cond = or_(cond, Workflow.user_id == user.id)
    return cond


@router.get("/workflows", response_model=list[WorkflowSummary])
def list_workflows(
    official: int = 0,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[Workflow]:
    q = db.query(Workflow)
    if official:
        q = q.filter(Workflow.is_official.is_(True))
    else:
        q = q.filter(_visible_to(user))
    return q.order_by(Workflow.id).all()


@router.post("/workflows", response_model=WorkflowSummary, status_code=201)
def create_workflow(
    body: WorkflowCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workflow:
    wf = Workflow(
        user_id=user.id,
        name=body.name,
        description=body.description,
        prompt_api=body.prompt_api,
        slots=[s.model_dump() for s in body.slots],
        model_refs=body.model_refs,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


@router.get("/workflows/{wf_id}", response_model=WorkflowSummary)
def get_workflow(
    wf_id: int,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Workflow:
    wf = db.get(Workflow, wf_id)
    # 越权访问统一回 404 而非 403，避免用状态码区分「不存在」和「存在但无权限」
    if wf is None or not (wf.is_official or (user is not None and wf.user_id == user.id)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="工作流不存在")
    return wf


@router.delete("/workflows/{wf_id}", status_code=204)
def delete_workflow(
    wf_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    wf = db.get(Workflow, wf_id)
    if wf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="工作流不存在")
    if wf.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="无权删除")
    db.delete(wf)
    db.commit()
