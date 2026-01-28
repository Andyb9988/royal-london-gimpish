from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.enums import AssetKind, AssetStatus
from app.db.base import Base, sql_enum


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (Index("ix_assets_report_id_kind", "report_id", "kind"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("reports.id"),
        index=True,
        nullable=False,
    )
    kind: Mapped[AssetKind] = mapped_column(
        sql_enum(AssetKind, name="asset_kind"),
        nullable=False,
    )
    gcs_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[AssetStatus] = mapped_column(
        sql_enum(AssetStatus, name="asset_status"),
        nullable=False,
    )
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
