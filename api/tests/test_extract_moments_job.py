import pytest

from app.core.enums import JobStatus, JobType, ReportStatus
from app.jobs import extract_moments as job_module
from app.models.job import Job
from app.schemas.extract_moments import ExtractMomentsOut
from app.schemas.report import ReportCreate
from app.services import report_service

pytestmark = pytest.mark.asyncio


async def test_extract_moments_job_updates_report(db, monkeypatch):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Great match."),
    )
    report.status = ReportStatus.PROCESSING
    job = Job(
        id="job-1",
        report_id=report.id,
        type=JobType.EXTRACT_MOMENTS,
        status=JobStatus.QUEUED,
        attempts=0,
    )
    db.add(job)
    await db.flush()

    def fake_extract(_: str) -> ExtractMomentsOut:
        return ExtractMomentsOut(gimp_name="MVP", champagne_moment="Last-second goal")

    monkeypatch.setattr(job_module, "extract_moments", fake_extract)

    await job_module.run(db, job.id)

    assert job.status == JobStatus.SUCCEEDED
    assert report.gimp_name == "MVP"
    assert report.champagne_moment == "Last-second goal"
