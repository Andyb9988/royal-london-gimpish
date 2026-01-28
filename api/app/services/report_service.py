from datetime import date
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssetKind, AssetStatus, JobType, ReportStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.asset import Asset
from app.models.job import Job
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate
from app.services.job_service import ensure_job


async def _get_report(db: AsyncSession, report_id: str) -> Report:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


def _require_author(report: Report, author_id: str) -> None:
    if report.author_id != author_id:
        raise ForbiddenError("Not allowed to access this report")


async def create_report(db: AsyncSession, author_id: str, data: ReportCreate) -> Report:
    report = Report(
        id=uuid4().hex,
        author_id=author_id,
        date=data.date,
        opponent=data.opponent,
        content=data.content,
        status=ReportStatus.DRAFT,
    )
    db.add(report)
    await db.flush()
    return report


async def update_report(
    db: AsyncSession, report_id: str, author_id: str, patch: ReportUpdate
) -> Report:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    if report.status not in {ReportStatus.DRAFT, ReportStatus.FAILED}:
        raise ConflictError("Only draft or failed reports can be edited")

    updates = patch.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(report, field, value)
    await db.flush()
    return report


async def list_reports(
    db: AsyncSession,
    author_id: str,
    status: ReportStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    opponent: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Report]:
    stmt: Select[tuple[Report]] = select(Report).where(Report.author_id == author_id)
    if status is not None:
        stmt = stmt.where(Report.status == status)
    if date_from is not None:
        stmt = stmt.where(Report.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Report.date <= date_to)
    if opponent:
        stmt = stmt.where(Report.opponent.ilike(f"%{opponent}%"))
    stmt = stmt.order_by(Report.date.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_report(db: AsyncSession, report_id: str, author_id: str) -> Report:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    return report


async def submit_report(
    db: AsyncSession, report_id: str, author_id: str
) -> tuple[Report, list[Job]]:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)

    if report.status in {ReportStatus.PUBLISHED, ReportStatus.ARCHIVED}:
        raise ConflictError("Cannot submit a published or archived report")

    asset_result = await db.execute(
        select(Asset).where(
            Asset.report_id == report_id,
            Asset.kind == AssetKind.GIMP_ORIGINAL,
            Asset.status == AssetStatus.READY,
        )
    )
    if asset_result.scalar_one_or_none() is None:
        raise BadRequestError("gimp_original asset must be uploaded before submit")

    if report.status in {ReportStatus.DRAFT, ReportStatus.FAILED}:
        report.status = ReportStatus.PROCESSING

    job_extract = await ensure_job(db, report_id, JobType.EXTRACT_MOMENTS)
    job_gimpify = await ensure_job(db, report_id, JobType.GIMPIFY_IMAGE)
    job_video = await ensure_job(db, report_id, JobType.GENERATE_VIDEO)
    await db.flush()
    return report, [job_extract, job_gimpify, job_video]


async def list_jobs(db: AsyncSession, report_id: str, author_id: str) -> list[Job]:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    result = await db.execute(select(Job).where(Job.report_id == report_id))
    return list(result.scalars().all())


async def list_assets(db: AsyncSession, report_id: str, author_id: str) -> list[Asset]:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    result = await db.execute(select(Asset).where(Asset.report_id == report_id))
    return list(result.scalars().all())


async def publish_report(db: AsyncSession, report_id: str, author_id: str) -> Report:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    if report.status == ReportStatus.PUBLISHED:
        return report
    if report.status == ReportStatus.ARCHIVED:
        raise ConflictError("Cannot publish an archived report")

    required_kinds = {AssetKind.GIMPIFIED_IMAGE, AssetKind.VIDEO}
    result = await db.execute(
        select(Asset.kind).where(
            Asset.report_id == report_id,
            Asset.status == AssetStatus.READY,
            Asset.kind.in_(required_kinds),
        )
    )
    ready_kinds = set(result.scalars().all())
    missing = required_kinds.difference(ready_kinds)
    if missing:
        raise ConflictError("Required assets are not ready")

    report.status = ReportStatus.PUBLISHED
    await db.flush()
    return report


async def unpublish_report(db: AsyncSession, report_id: str, author_id: str) -> Report:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    if report.status != ReportStatus.PUBLISHED:
        raise ConflictError("Report is not published")
    report.status = ReportStatus.DRAFT
    await db.flush()
    return report
