from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.enums import JobStatus, JobType
from app.db.base import Base, sql_enum


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("report_id", "type", name="uq_jobs_report_id_type"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("reports.id"),
        index=True,
        nullable=False,
    )
    type: Mapped[JobType] = mapped_column(
        sql_enum(JobType, name="job_type"),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        sql_enum(JobStatus, name="job_status"),
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    last_error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    provider_job_id: Mapped[str | None] = mapped_column(String(255))
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
