"""Job handler for generating videos using Replicate."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import AssetKind, JobStatus
from app.core.logging import get_logger
from app.jobs.utils import get_job_and_report
from app.services.asset_service import upsert_asset_ready
from app.services.gcs import upload_bytes
from app.services.replicate_service import ReplicatePredictionError, ReplicateService
from app.utils.storage_paths import gcs_object_key

logger = get_logger(__name__)


async def run(db: AsyncSession, job_id: str) -> None:
    """Run the video generation job."""
    job, report = await get_job_and_report(db, job_id)
    log = logger.bind(job_id=job_id, report_id=report.id)

    job.status = JobStatus.RUNNING
    job.attempts += 1
    await db.flush()

    # Build prompt from report content
    prompt = report.content or ""
    prompt = prompt.strip()
    if report.opponent:
        prompt = f"{prompt}\nOpponent: {report.opponent}".strip()
    if report.date:
        prompt = f"{prompt}\nDate: {report.date.isoformat()}".strip()

    if not prompt:
        job.status = JobStatus.FAILED
        job.last_error = "Report content is empty"
        log.warning("job_failed", error=job.last_error)
        return

    # Validate model configuration
    model_id = settings.replicate_video_identifier
    if not model_id:
        job.status = JobStatus.FAILED
        job.last_error = "REPLICATE_VIDEO_MODEL is not configured"
        log.warning("job_failed", error=job.last_error)
        return

    service = ReplicateService()

    try:
        # Create prediction
        prediction = await service.create_prediction(
            model_id,
            {"prompt": prompt},
        )
        prediction_id = prediction["id"]
        job.provider_job_id = prediction_id
        await db.flush()

        log.info("prediction_created", prediction_id=prediction_id)

        # Wait for completion (video generation can take longer)
        result_prediction = await service.wait_for_prediction(
            prediction_id, timeout_s=1800, poll_s=5.0
        )

        # Download output
        outputs = await service.normalize_file_outputs(result_prediction.get("output"))
        if not outputs:
            job.status = JobStatus.FAILED
            job.last_error = "Replicate output was empty"
            log.warning("job_failed", error=job.last_error)
            return

        output_bytes = outputs[0]

    except ReplicatePredictionError as exc:
        job.status = JobStatus.FAILED
        job.last_error = str(exc)
        log.warning("prediction_failed", error=str(exc))
        return

    except TimeoutError as exc:
        job.status = JobStatus.FAILED
        job.last_error = str(exc)
        log.warning("prediction_timeout", error=str(exc))
        return

    # Upload to GCS
    gcs_path = gcs_object_key(report.id, AssetKind.VIDEO, "mp4")
    await asyncio.to_thread(upload_bytes, gcs_path, output_bytes, content_type="video/mp4")

    # Create/update asset record
    await upsert_asset_ready(
        db,
        report_id=report.id,
        author_id=report.author_id,
        kind=AssetKind.VIDEO,
        gcs_path=gcs_path,
        mime_type="video/mp4",
    )

    job.status = JobStatus.SUCCEEDED
    job.last_error = None
    log.info("job_succeeded", gcs_path=gcs_path)
