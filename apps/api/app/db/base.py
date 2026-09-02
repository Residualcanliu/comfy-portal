"""SQLAlchemy 2.0 Declarative Base。"""

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

# 跨方言主键类型：Postgres → BIGINT（BIGSERIAL），SQLite → INTEGER（SQLite 仅 INTEGER 主键会自增）
BigIntPk = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    pass
