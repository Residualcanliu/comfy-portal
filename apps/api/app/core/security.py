"""密码哈希 + JWT。"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    # bcrypt 72 字节上限，超出截断
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_expire_days)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    # 拒绝把 SSE 票据当 access token 用。票据签名有效且 sub 就是 user_id，
    # 不挡的话一张 60 秒票据可以换取完整的接口访问权 —— 两种凭证必须互不通用。
    if payload.get("scope") == "sse":
        raise jwt.InvalidTokenError("sse ticket is not an access token")
    return payload


# SSE 票据有效期。浏览器 EventSource 不能自定义请求头，实时进度只能把凭证放进
# query string；直接塞 access token 会让这个 7 天有效的凭证落进访问日志和 CDN 日志。
# 换成 60 秒、单一用途的票据，泄漏窗口就从 7 天压到 1 分钟。
SSE_TICKET_TTL_SECONDS = 60


def create_sse_ticket(subject: str | int) -> str:
    expire = datetime.now(UTC) + timedelta(seconds=SSE_TICKET_TTL_SECONDS)
    payload = {"sub": str(subject), "scope": "sse", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_sse_ticket(ticket: str) -> dict[str, Any]:
    """校验 SSE 票据。

    带 scope 校验：access token 没有 scope 字段，因此不能用它冒充票据 ——
    两种凭证互不通用。
    """
    payload = jwt.decode(ticket, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("scope") != "sse":
        raise jwt.InvalidTokenError("not an sse ticket")
    return payload
