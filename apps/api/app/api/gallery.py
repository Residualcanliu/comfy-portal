"""画廊（规格书 §5 GET /api/gallery，公开）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.artifact import Artifact

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
