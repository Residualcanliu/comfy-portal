"""FastAPI 入口（规格书 §5）。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

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


_docs_enabled = settings.docs_enabled

app = FastAPI(
    title="ComfyPortal API",
    version="0.1.0",
    lifespan=lifespan,
    # 生产建议设 DOCS_ENABLED=false：/docs、/redoc、/openapi.json 会暴露
    # 全部路由结构（含 /internal/*），降低攻击者踩点成本。
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

# CORS：默认放开（本地开发方便），生产用 CORS_ORIGINS 指定前端源（规格书 §9）。
# allow_credentials 保持 False —— 认证走 Authorization: Bearer 而非 Cookie，
# 只要不开 credentials，`*` 就不构成凭证窃取面。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    """安全响应头。

    nosniff 尤其重要：/files 直接托管用户可影响的图片产物，没有它浏览器会
    按内容猜测类型，一张伪装成图片的 HTML 就能在 API 源上执行脚本。
    CSP 只加在 /files 上 —— 全局加 default-src 'none' 会把 /docs 的页面打坏。
    """
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/files"):
        resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        # 这里刻意不加 Content-Disposition: attachment —— 画廊用 <img src> 直接展示，
        # 加了可能被浏览器当附件而不渲染。挡 XSS 靠的是「扩展名白名单 + nosniff + CSP」
        # 这三条，不需要再动 Content-Disposition。
    return resp

from app.api import auth, gallery, internal, status, tasks, workflows

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(workflows.router, prefix="/api", tags=["workflows"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
# SSE 与票据走独立 router（EventSource 无法带 Authorization 头，见 tasks.py 说明）
app.include_router(tasks.events_router, prefix="/api", tags=["tasks"])
app.include_router(gallery.router, prefix="/api", tags=["gallery"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])

os.makedirs(settings.artifacts_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.artifacts_dir), name="files")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
