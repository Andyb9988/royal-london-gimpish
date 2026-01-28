from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import JobStatus, JobType
from app.models.job import Job


async def ensure_job(
    db: AsyncSession, report_id: str, job_type: JobType, idempotency_key: str | None = None
) -> Job:
    stmt = (
        insert(Job)
        .values(
            id=uuid4().hex,
            report_id=report_id,
            type=job_type,
            status=JobStatus.QUEUED,
            attempts=0,
            idempotency_key=idempotency_key,
        )
        .on_conflict_do_nothing(index_elements=["report_id", "type"])
        .returning(Job.id)
    )
    result = await db.execute(stmt)
    job_id = result.scalar_one_or_none()
    if job_id is None:
        existing = await db.execute(
            select(Job).where(Job.report_id == report_id, Job.type == job_type)
        )
        return existing.scalar_one()

    created = await db.execute(select(Job).where(Job.id == job_id))
    return created.scalar_one()


async def list_jobs(db: AsyncSession, report_id: str) -> list[Job]:
    result = await db.execute(select(Job).where(Job.report_id == report_id))
    return list(result.scalars().all())
