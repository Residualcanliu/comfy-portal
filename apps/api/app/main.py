"""FastAPI 入口。M1 阶段逐步挂载 /api/* 与 /internal/* 路由（规格书 §5）。"""

from fastapi import FastAPI

from .core.config import settings

app = FastAPI(title="ComfyPortal API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


# 后续：
# from .api import auth, workflows, tasks, gallery, internal
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# ...
