"""Tests for job state transitions in the worker."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.enums import JobStatus, JobType, ReportStatus
from app.models.job import Job
from app.models.report import Report
from app.workers.runner import handle_message

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    job = Job(
        id="job-123",
        report_id="report-456",
        type=JobType.EXTRACT_MOMENTS,
        status=JobStatus.QUEUED,
        attempts=0,
    )
    return job


@pytest.fixture
def sample_report():
    """Create a sample report for testing."""
    report = Report(
        id="report-456",
        author_id="author-1",
        date="2025-01-01",
        opponent="Test FC",
        content="Test content",
        status=ReportStatus.PROCESSING,
    )
    return report


class TestHandleMessage:
    """Tests for the handle_message function."""

    async def test_skips_invalid_payload_missing_job_id(self):
        """Test that messages without job_id are skipped."""
        await handle_message({"job_type": "extract_moments"})
        # Should not raise, just skip

    async def test_skips_invalid_payload_missing_job_type(self):
        """Test that messages without job_type are skipped."""
        await handle_message({"job_id": "job-123"})
        # Should not raise, just skip

    async def test_skips_unknown_job_type(self):
        """Test that unknown job types are skipped."""
        await handle_message({"job_id": "job-123", "job_type": "unknown_type"})
        # Should not raise, just skip

    async def test_skips_already_succeeded_job(self, sample_job):
        """Test that already succeeded jobs are skipped."""
        sample_job.status = JobStatus.SUCCEEDED

        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            await handle_message(
                {
                    "job_id": sample_job.id,
                    "job_type": sample_job.type.value,
                }
            )

            # Commit should not be called for skipped jobs (no handler invoked)
            mock_db.commit.assert_not_called()

    async def test_marks_job_failed_on_exception(self, sample_job):
        """Test that jobs are marked failed when handler raises."""
        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch("app.workers.runner._JOB_HANDLERS") as mock_handlers:

                async def failing_handler(db, job_id):
                    raise ValueError("Test error")

                mock_handlers.get.return_value = failing_handler

                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": sample_job.type.value,
                    }
                )

                assert sample_job.status == JobStatus.FAILED
                assert sample_job.last_error == "Test error"
                mock_db.commit.assert_called()

    async def test_marks_job_failed_on_timeout(self, sample_job):
        """Test that jobs are marked failed on timeout errors."""
        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch("app.workers.runner._JOB_HANDLERS") as mock_handlers:

                async def timeout_handler(db, job_id):
                    raise TimeoutError("Connection timed out")

                mock_handlers.get.return_value = timeout_handler

                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": sample_job.type.value,
                    }
                )

                assert sample_job.status == JobStatus.FAILED
                assert "Timeout" in sample_job.last_error

    async def test_marks_job_failed_on_connection_error(self, sample_job):
        """Test that jobs are marked failed on connection errors."""
        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch("app.workers.runner._JOB_HANDLERS") as mock_handlers:

                async def connection_handler(db, job_id):
                    raise ConnectionError("Failed to connect")

                mock_handlers.get.return_value = connection_handler

                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": sample_job.type.value,
                    }
                )

                assert sample_job.status == JobStatus.FAILED
                assert "Connection error" in sample_job.last_error

    async def test_commits_on_successful_handler(self, sample_job):
        """Test that successful handler execution commits the transaction."""
        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch("app.workers.runner._JOB_HANDLERS") as mock_handlers:

                async def success_handler(db, job_id):
                    pass  # Success

                mock_handlers.get.return_value = success_handler

                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": sample_job.type.value,
                    }
                )

                mock_db.commit.assert_called_once()

    async def test_skips_job_not_found(self):
        """Test that non-existent jobs are skipped."""
        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = None  # Job not found
            mock_session.return_value.__aenter__.return_value = mock_db

            await handle_message(
                {
                    "job_id": "nonexistent",
                    "job_type": "extract_moments",
                }
            )

            # Should not commit anything
            mock_db.commit.assert_not_called()


class TestJobTypeRouting:
    """Tests for routing jobs to correct handlers."""

    async def test_routes_extract_moments(self, sample_job):
        """Test that extract_moments jobs are routed correctly."""
        sample_job.type = JobType.EXTRACT_MOMENTS
        mock_handler = AsyncMock()

        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch.dict(
                "app.workers.runner._JOB_HANDLERS",
                {JobType.EXTRACT_MOMENTS: mock_handler},
            ):
                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": "extract_moments",
                    }
                )

                mock_handler.assert_called_once_with(mock_db, sample_job.id)

    async def test_routes_gimpify_image(self, sample_job):
        """Test that gimpify_image jobs are routed correctly."""
        sample_job.type = JobType.GIMPIFY_IMAGE
        mock_handler = AsyncMock()

        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch.dict(
                "app.workers.runner._JOB_HANDLERS",
                {JobType.GIMPIFY_IMAGE: mock_handler},
            ):
                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": "gimpify_image",
                    }
                )

                mock_handler.assert_called_once_with(mock_db, sample_job.id)

    async def test_routes_generate_video(self, sample_job):
        """Test that generate_video jobs are routed correctly."""
        sample_job.type = JobType.GENERATE_VIDEO
        mock_handler = AsyncMock()

        with patch("app.workers.runner.SessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get.return_value = sample_job
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch.dict(
                "app.workers.runner._JOB_HANDLERS",
                {JobType.GENERATE_VIDEO: mock_handler},
            ):
                await handle_message(
                    {
                        "job_id": sample_job.id,
                        "job_type": "generate_video",
                    }
                )

                mock_handler.assert_called_once_with(mock_db, sample_job.id)
