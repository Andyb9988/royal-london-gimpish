"""Job handler for gimpifying images using Replicate."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import AssetKind, AssetStatus, JobStatus
from app.core.logging import get_logger
from app.jobs.utils import get_job_and_report
from app.models.asset import Asset
from app.services.asset_service import upsert_asset_ready
from app.services.gcs import signed_get_url, upload_bytes
from app.services.replicate_service import ReplicatePredictionError, ReplicateService
from app.utils.storage_paths import gcs_object_key, mime_to_ext

logger = get_logger(__name__)


async def run(db: AsyncSession, job_id: str) -> None:
    """Run the gimpify image job."""
    job, report = await get_job_and_report(db, job_id)
    log = logger.bind(job_id=job_id, report_id=report.id)

    job.status = JobStatus.RUNNING
    job.attempts += 1
    await db.flush()

    # Find the original image asset
    result = await db.execute(
        select(Asset).where(
            Asset.report_id == report.id,
            Asset.kind == AssetKind.GIMP_ORIGINAL,
            Asset.status == AssetStatus.READY,
        )
    )
    original = result.scalar_one_or_none()
    if original is None:
        job.status = JobStatus.FAILED
        job.last_error = "Missing gimp_original asset"
        log.warning("job_failed", error=job.last_error)
        return

    # Generate signed URL for the original image
    signed_url = await asyncio.to_thread(signed_get_url, original.gcs_path, expires_s=3600)

    # Validate model configuration
    model_id = settings.replicate_gimp_identifier
    if not model_id:
        job.status = JobStatus.FAILED
        job.last_error = "REPLICATE_GIMP_MODEL is not configured"
        log.warning("job_failed", error=job.last_error)
        return

    prompt = (
        "Make this image gimpish, surreal, high-contrast, British football satire, "
        "keep subject identity, preserve key details."
    )

    service = ReplicateService()

    try:
        # Create prediction
        prediction = await service.create_prediction(
            model_id,
            {
                "prompt": prompt,
                "image_input": [signed_url],
                "output_format": "jpg",
            },
        )
        prediction_id = prediction["id"]
        job.provider_job_id = prediction_id
        await db.flush()

        log.info("prediction_created", prediction_id=prediction_id)

        # Wait for completion
        result_prediction = await service.wait_for_prediction(
            prediction_id, timeout_s=900, poll_s=2.0
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
    mime_type = "image/jpeg"
    ext = mime_to_ext(mime_type)
    gcs_path = gcs_object_key(report.id, AssetKind.GIMPIFIED_IMAGE, ext)

    await asyncio.to_thread(upload_bytes, gcs_path, output_bytes, content_type=mime_type)

    # Create/update asset record
    await upsert_asset_ready(
        db,
        report_id=report.id,
        author_id=report.author_id,
        kind=AssetKind.GIMPIFIED_IMAGE,
        gcs_path=gcs_path,
        mime_type=mime_type,
    )

    job.status = JobStatus.SUCCEEDED
    job.last_error = None
    log.info("job_succeeded", gcs_path=gcs_path)
