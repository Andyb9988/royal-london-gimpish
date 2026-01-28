from enum import Enum as PyEnum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase


def sql_enum(enum_cls: type[PyEnum], name: str) -> SqlEnum:
    return SqlEnum(
        enum_cls,
        name=name,
        values_callable=lambda values: [value.value for value in values],
    )


class Base(DeclarativeBase):
    pass


__all__ = ["Base", "sql_enum"]
