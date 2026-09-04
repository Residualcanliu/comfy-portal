"""FastAPI 入口（规格书 §5）。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # M1 dev：启动时建表（后续以 alembic 迁移替代）
    import app.models  # noqa: F401  # 注册模型
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(bind=engine)

    # GPU 离线陈旧恢复后台线程（规格书 §1）
    from app.core.stale_recovery import start_stale_recovery

    start_stale_recovery()
    yield


app = FastAPI(title="ComfyPortal API", version="0.1.0", lifespan=lifespan)

# CORS：M1 放开所有源；M4 部署时收紧为前端源（规格书 §9）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, gallery, internal, status, tasks, workflows

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
