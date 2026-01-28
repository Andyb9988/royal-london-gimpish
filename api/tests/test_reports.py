"""Tests for report service operations."""

import pytest

from app.core.enums import AssetKind, JobType, ReportStatus
from app.core.exceptions import BadRequestError
from app.schemas.report import ReportCreate
from app.services import asset_service, report_service

pytestmark = pytest.mark.asyncio


async def test_create_report_sets_draft(db):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Test"),
    )
    assert report.status == ReportStatus.DRAFT


async def test_attach_gimp_original_creates_asset(db):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Test"),
    )
    asset = await asset_service.upsert_asset_ready(
        db,
        report_id=report.id,
        author_id="author-1",
        kind=AssetKind.GIMP_ORIGINAL,
        gcs_path="reports/1/gimp_original.jpg",
        mime_type="image/jpeg",
    )
    assert asset.report_id == report.id
    assert asset.kind == AssetKind.GIMP_ORIGINAL


async def test_submit_requires_gimp_original(db):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Test"),
    )
    with pytest.raises(BadRequestError):
        await report_service.submit_report(db, report.id, author_id="author-1")


async def test_submit_is_idempotent(db):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Test"),
    )
    await asset_service.upsert_asset_ready(
        db,
        report_id=report.id,
        author_id="author-1",
        kind=AssetKind.GIMP_ORIGINAL,
        gcs_path="reports/1/gimp_original.jpg",
        mime_type="image/jpeg",
    )
    await report_service.submit_report(db, report.id, author_id="author-1")
    await report_service.submit_report(db, report.id, author_id="author-1")

    jobs = await report_service.list_jobs(db, report.id, author_id="author-1")
    assert len(jobs) == 3
    assert {job.type for job in jobs} == {
        JobType.EXTRACT_MOMENTS,
        JobType.GIMPIFY_IMAGE,
        JobType.GENERATE_VIDEO,
    }


async def test_submit_transitions_to_processing(db):
    report = await report_service.create_report(
        db,
        author_id="author-1",
        data=ReportCreate(date="2025-01-01", opponent="Rivals", content="Test"),
    )
    await asset_service.upsert_asset_ready(
        db,
        report_id=report.id,
        author_id="author-1",
        kind=AssetKind.GIMP_ORIGINAL,
        gcs_path="reports/1/gimp_original.jpg",
        mime_type="image/jpeg",
    )
    report, _ = await report_service.submit_report(db, report.id, author_id="author-1")
    assert report.status == ReportStatus.PROCESSING
