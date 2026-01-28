from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.job import Job
from app.models.report import Report


async def get_job_and_report(db: AsyncSession, job_id: str) -> tuple[Job, Report]:
    result = await db.execute(
        select(Job, Report).join(Report, Job.report_id == Report.id).where(Job.id == job_id)
    )
    row = result.first()
    if row is None:
        raise NotFoundError("Job not found")
    job, report = row
    return job, report


__all__ = ["get_job_and_report"]
