"""画廊（规格书 §5 GET /api/gallery 公开；DELETE 仅管理员）。"""

import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.models.artifact import Artifact
from app.models.user import User

router = APIRouter()


@router.get("/gallery")
def gallery(
    db: Session = Depends(get_db),
    limit: int = Query(24, le=100),
    offset: int = 0,
) -> list[dict]:
    arts = (
        db.query(Artifact)
        .order_by(Artifact.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "task_id": a.task_id,
            "kind": a.kind,
            "url": f"/files/{a.filename}",
            "width": a.width,
            "height": a.height,
        }
        for a in arts
    ]


@router.delete("/gallery/{artifact_id}", status_code=204)
def delete_artifact(
    artifact_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    art = db.get(Artifact, artifact_id)
    if art is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="作品不存在")
    path = os.path.join(settings.artifacts_dir, art.filename)
    if os.path.exists(path):
        os.remove(path)
    db.delete(art)
    db.commit()
