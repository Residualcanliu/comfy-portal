"""认证边界：确认各入口在「未带凭证」时一律被拦，且 SSE 走票据而非裸奔。

这些断言全部在访问数据库之前就会得到结果（依赖校验 / 参数校验先行），
所以不依赖本地数据，CI 里也能跑。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_is_public() -> None:
    assert client.get("/healthz").status_code == 200


def test_security_headers_present() -> None:
    resp = client.get("/healthz")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_tasks_require_auth() -> None:
    """router 级依赖：整个 tasks 路由下的端点默认就要登录。"""
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"workflow_id": 1, "params": {}}).status_code == 401


def test_ticket_endpoint_requires_auth() -> None:
    assert client.post("/api/tasks/1/ticket").status_code == 401


def test_sse_requires_ticket_param() -> None:
    """漏传 ticket 应被参数校验拦下，而不是放行成匿名订阅。"""
    assert client.get("/api/tasks/1/events").status_code == 422


def test_sse_rejects_bad_ticket() -> None:
    assert client.get("/api/tasks/1/events", params={"ticket": "not-a-jwt"}).status_code == 401


def test_access_token_cannot_be_used_as_sse_ticket() -> None:
    """access token 没有 scope=sse，不能拿来冒充票据 —— 两种凭证互不通用。"""
    from app.core.security import create_access_token, create_sse_ticket

    access = create_access_token(1)
    resp = client.get("/api/tasks/1/events", params={"ticket": access})
    assert resp.status_code == 401

    # 反向：票据也不该被当成 access token 用
    ticket = create_sse_ticket(1)
    resp = client.get("/api/tasks", headers={"Authorization": f"Bearer {ticket}"})
    assert resp.status_code == 401
