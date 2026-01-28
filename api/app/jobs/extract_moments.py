import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import JobStatus, ReportStatus
from app.jobs.utils import get_job_and_report
from app.services.genai_extractor import extract_moments
from app.services.queue import enqueue_job


async def _retry_or_fail(
    job_id: str,
    job_type: str,
    job,
    report,
    error: str,
) -> None:
    job.last_error = error
    if job.attempts < settings.EXTRACT_MOMENTS_MAX_ATTEMPTS:
        job.status = JobStatus.QUEUED
        await enqueue_job(job_id, job_type)
        return
    job.status = JobStatus.FAILED
    report.status = ReportStatus.FAILED


async def run(db: AsyncSession, job_id: str) -> None:
    job, report = await get_job_and_report(db, job_id)
    if job.attempts >= settings.EXTRACT_MOMENTS_MAX_ATTEMPTS:
        job.status = JobStatus.FAILED
        job.last_error = "Max attempts exceeded"
        report.status = ReportStatus.FAILED
        return

    job.status = JobStatus.RUNNING
    job.attempts += 1
    await db.flush()

    content = (report.content or "").strip()
    if not content:
        job.status = JobStatus.FAILED
        job.last_error = "Report content is empty"
        report.status = ReportStatus.FAILED
        return

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(extract_moments, content),
            timeout=settings.GEMINI_REQUEST_TIMEOUT_S,
        )
    except TimeoutError:
        await _retry_or_fail(job.id, job.type.value, job, report, "Gemini request timed out")
        return
    except Exception as exc:
        await _retry_or_fail(job.id, job.type.value, job, report, str(exc))
        return

    report.gimp_name = result.gimp_name
    report.champagne_moment = result.champagne_moment

    job.status = JobStatus.SUCCEEDED
    job.last_error = None
