from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import JobStatus, JobType


class JobResponse(BaseModel):
    id: str
    report_id: str
    type: JobType
    status: JobStatus
    attempts: int
    last_error: str | None
    idempotency_key: str | None
    provider_job_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ["JobResponse"]
