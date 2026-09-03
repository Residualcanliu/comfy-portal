"""工作流 CRUD（规格书 §5）。响应复用 shared 的 WorkflowSummary。"""

from comfyportal_shared.dto import WorkflowSummary
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate

router = APIRouter()


@router.get("/workflows", response_model=list[WorkflowSummary])
def list_workflows(official: int = 0, db: Session = Depends(get_db)) -> list[Workflow]:
    q = db.query(Workflow)
    if official:
        q = q.filter(Workflow.is_official.is_(True))
    # M1：无鉴权返回全部；M2 增加「本人 + 官方」过滤
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
def get_workflow(wf_id: int, db: Session = Depends(get_db)) -> Workflow:
    wf = db.get(Workflow, wf_id)
    if wf is None:
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
