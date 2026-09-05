"""工作流模型（规格书 §4 workflows + §2 slots）。

prompt_api / slots / model_refs 用 SQLAlchemy 通用 JSON 类型（Postgres 上即 JSON，
用途为「整体存取、不在 JSON 内查询」，等价于规格书的 JSONB）。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPk


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    # NULL = 官方预置工作流
    user_id: Mapped[int | None] = mapped_column(
        BigIntPk, ForeignKey("users.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_api: Mapped[dict[str, Any]] = mapped_column(JSON)
    slots: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    model_refs: Mapped[list[str]] = mapped_column(JSON)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @property
    def available(self) -> bool:
        # M1：模型缺失校验前恒为 True；W2 由 worker model_refs 校验驱动（前端置灰）
        return True
