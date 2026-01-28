from __future__ import annotations

from datetime import date as Date
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ReportStatus
from app.schemas.asset import AssetResponse
from app.schemas.job import JobResponse


class ReportCreate(BaseModel):
    date: Date
    opponent: str | None = Field(None, max_length=255)
    content: str | None = None


class ReportUpdate(BaseModel):
    date: Date | None = None
    opponent: str | None = Field(None, max_length=255)
    content: str | None = None


class ReportResponse(BaseModel):
    id: str
    author_id: str
    date: Date
    opponent: str | None
    content: str | None
    status: ReportStatus
    gimp_name: str | None
    champagne_moment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportListItem(ReportResponse):
    pass


class ReportDetail(ReportResponse):
    assets: list[AssetResponse]
    jobs: list[JobResponse]


__all__ = [
    "ReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "ReportListItem",
    "ReportDetail",
]
