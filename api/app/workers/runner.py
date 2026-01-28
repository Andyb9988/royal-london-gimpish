"""Worker runner for processing background jobs from Redis queue."""

from __future__ import annotations

import asyncio
import json
import os
import signal
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import JobStatus, JobType
from app.core.logging import configure_logging, get_logger
from app.db.session import create_engine_and_sessionmaker
from app.jobs.extract_moments import run as run_extract
from app.jobs.generate_video import run as run_video
from app.jobs.gimpify_image import run as run_gimpify
from app.models.job import Job

JobHandler = Callable[[AsyncSession, str], Awaitable[None]]

_JOB_HANDLERS: dict[JobType, JobHandler] = {
    JobType.EXTRACT_MOMENTS: run_extract,
    JobType.GIMPIFY_IMAGE: run_gimpify,
    JobType.GENERATE_VIDEO: run_video,
}

logger = get_logger(__name__)

_ENGINE, SessionLocal = create_engine_and_sessionmaker(settings.DATABASE_URL)


class GracefulShutdown:
    """Manages graceful shutdown on SIGTERM/SIGINT signals."""

    def __init__(self) -> None:
        self._shutdown_requested = False
        self._current_job_id: str | None = None

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def request_shutdown(self) -> None:
        self._shutdown_requested = True
        logger.info(
            "shutdown_requested",
            current_job_id=self._current_job_id,
            message="Will exit after current job completes" if self._current_job_id else "Exiting",
        )

    def set_current_job(self, job_id: str | None) -> None:
        self._current_job_id = job_id


async def _load_job(db: AsyncSession, job_id: str) -> Job | None:
    return await db.get(Job, job_id)


async def _mark_failed(db: AsyncSession, job: Job, error: str) -> None:
    job.status = JobStatus.FAILED
    job.last_error = error
    await db.flush()


class JobProcessingError(Exception):
    """Raised when job processing fails with a known error type."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


async def handle_message(payload: dict) -> None:
    """Process a single job message from the queue."""
    job_id = payload.get("job_id")
    job_type = payload.get("job_type")

    if not job_id or not job_type:
        logger.warning("invalid_message", payload=payload, reason="missing job_id or job_type")
        return

    log = logger.bind(job_id=job_id, job_type=job_type)

    try:
        job_type_enum = JobType(job_type)
    except ValueError:
        log.warning("unknown_job_type")
        return

    handler = _JOB_HANDLERS.get(job_type_enum)
    if handler is None:
        log.warning("no_handler_for_job_type")
        return

    async with SessionLocal() as db:
        job = await _load_job(db, job_id)
        if job is None:
            log.warning("job_not_found")
            return

        if job.status == JobStatus.SUCCEEDED:
            log.info("job_already_succeeded", skipping=True)
            return

        log.info("job_started", attempt=job.attempts + 1)

        try:
            await handler(db, job_id)
            await db.commit()
            log.info("job_completed", status=job.status.value)

        except TimeoutError as exc:
            log.warning("job_timeout", error=str(exc))
            await _mark_failed(db, job, f"Timeout: {exc}")
            await db.commit()

        except ConnectionError as exc:
            log.error("job_connection_error", error=str(exc))
            await _mark_failed(db, job, f"Connection error: {exc}")
            await db.commit()

        except Exception as exc:
            log.exception("job_failed", error=str(exc))
            await _mark_failed(db, job, str(exc))
            await db.commit()


async def run_worker(queue: str = "jobs") -> None:
    """Main worker loop that processes jobs from the Redis queue."""
    shutdown = GracefulShutdown()

    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        shutdown.request_shutdown()

    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda _s, _f: signal_handler())

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    logger.info("worker_started", queue=queue, pid=os.getpid())

    try:
        while not shutdown.shutdown_requested:
            # Use timeout so we can check shutdown flag periodically
            result = await redis.blpop(queue, timeout=1)
            if result is None:
                continue

            _, raw = result
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("invalid_json_message", raw=raw[:100])
                continue

            job_id = payload.get("job_id")
            shutdown.set_current_job(job_id)

            try:
                await handle_message(payload)
            finally:
                shutdown.set_current_job(None)

    finally:
        await redis.aclose()
        await _ENGINE.dispose()
        logger.info("worker_stopped")


def main() -> None:
    """Entry point for the worker process."""
    # Configure logging (use JSON in production)
    json_output = os.getenv("LOG_FORMAT", "").lower() == "json"
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(json_output=json_output, log_level=log_level)

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
