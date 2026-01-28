from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_author_id
from app.api.errors import handle_service_error
from app.core.enums import JobStatus, ReportStatus
from app.db.session import get_db
from app.schemas.report import (
    ReportCreate,
    ReportDetail,
    ReportListItem,
    ReportResponse,
    ReportUpdate,
)
from app.services import report_service
from app.services.queue import enqueue_job

router = APIRouter(prefix="/v1/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.create_report(db, author_id, payload)
    except Exception as exc:
        handle_service_error(exc)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    payload: ReportUpdate,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.update_report(db, report_id, author_id, payload)
    except Exception as exc:
        handle_service_error(exc)


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await report_service.get_report(db, report_id, author_id)
        assets = await report_service.list_assets(db, report_id, author_id)
        jobs = await report_service.list_jobs(db, report_id, author_id)
        return ReportDetail(
            **ReportResponse.model_validate(report).model_dump(),
            assets=assets,
            jobs=jobs,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    status: ReportStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    opponent: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.list_reports(
            db,
            author_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            opponent=opponent,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.post("/{report_id}/submit", response_model=ReportResponse)
async def submit_report(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        report, jobs = await report_service.submit_report(db, report_id, author_id)
        await db.commit()
        try:
            for job in jobs:
                if job.status != JobStatus.SUCCEEDED:
                    await enqueue_job(job.id, job.type.value)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to enqueue jobs",
            ) from exc
        return report
    except Exception as exc:
        handle_service_error(exc)


@router.post("/{report_id}/publish", response_model=ReportResponse)
async def publish_report(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.publish_report(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)


@router.post("/{report_id}/unpublish", response_model=ReportResponse)
async def unpublish_report(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.unpublish_report(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)
