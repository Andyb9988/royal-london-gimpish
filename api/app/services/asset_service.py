from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssetKind, AssetStatus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.asset import Asset
from app.models.report import Report


async def _get_report(db: AsyncSession, report_id: str) -> Report:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


def _require_author(report: Report, author_id: str) -> None:
    if report.author_id != author_id:
        raise ForbiddenError("Not allowed to access this report")


async def upsert_asset_ready(
    db: AsyncSession,
    report_id: str,
    author_id: str,
    kind: AssetKind,
    gcs_path: str,
    mime_type: str | None,
) -> Asset:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)

    existing = await db.execute(
        select(Asset).where(Asset.report_id == report_id, Asset.kind == kind)
    )
    asset = existing.scalar_one_or_none()
    if asset is None:
        asset = Asset(
            id=uuid4().hex,
            report_id=report_id,
            kind=kind,
            gcs_path=gcs_path,
            mime_type=mime_type,
            status=AssetStatus.READY,
        )
        db.add(asset)
    else:
        asset.gcs_path = gcs_path
        asset.mime_type = mime_type
        asset.status = AssetStatus.READY
    await db.flush()
    return asset


async def list_assets(db: AsyncSession, report_id: str, author_id: str) -> list[Asset]:
    report = await _get_report(db, report_id)
    _require_author(report, author_id)
    result = await db.execute(select(Asset).where(Asset.report_id == report_id))
    return list(result.scalars().all())
