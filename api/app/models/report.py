from __future__ import annotations

from datetime import date as PyDate
from datetime import datetime

from sqlalchemy import Date, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.enums import ReportStatus
from app.db.base import Base, sql_enum


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_status_date", "status", "date"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    author_id: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[PyDate] = mapped_column(Date, nullable=False)
    opponent: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(
        sql_enum(ReportStatus, name="report_status"),
        nullable=False,
    )
    gimp_name: Mapped[str | None] = mapped_column(String(255))
    champagne_moment: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
