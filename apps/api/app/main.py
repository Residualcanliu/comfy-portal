"""FastAPI 入口（规格书 §5）。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # M1 dev：启动时建表（后续以 alembic 迁移替代）
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa: F401  # 注册模型

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ComfyPortal API", version="0.1.0", lifespan=lifespan)

from app.api import auth, gallery, internal, status, tasks, workflows  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(workflows.router, prefix="/api", tags=["workflows"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(gallery.router, prefix="/api", tags=["gallery"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])

os.makedirs(settings.artifacts_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.artifacts_dir), name="files")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
