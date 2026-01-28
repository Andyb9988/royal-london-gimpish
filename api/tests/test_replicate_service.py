"""Tests for the ReplicateService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.replicate_service import (
    ReplicatePredictionError,
    ReplicateService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def replicate_service():
    """Create a ReplicateService with a test token."""
    return ReplicateService(api_token="test-token")


class TestCreatePrediction:
    """Tests for create_prediction method."""

    async def test_create_prediction_with_model_id(self, replicate_service):
        """Test creating a prediction with a model identifier."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "pred-123", "status": "starting"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(replicate_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_get_client.return_value = mock_client

            result = await replicate_service.create_prediction("owner/model", {"prompt": "test"})

            assert result["id"] == "pred-123"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/predictions"
            assert call_args[1]["json"]["model"] == "owner/model"
            assert call_args[1]["json"]["input"] == {"prompt": "test"}

    async def test_create_prediction_with_version_hash(self, replicate_service):
        """Test creating a prediction with a version hash."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "pred-456", "status": "starting"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(replicate_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_get_client.return_value = mock_client

            result = await replicate_service.create_prediction("abc123:version", {"prompt": "test"})

            assert result["id"] == "pred-456"
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["version"] == "abc123:version"


class TestWaitForPrediction:
    """Tests for wait_for_prediction method."""

    async def test_wait_returns_on_success(self, replicate_service):
        """Test that wait returns successfully completed prediction."""
        with patch.object(
            replicate_service,
            "get_prediction",
            new_callable=AsyncMock,
            return_value={
                "id": "pred-123",
                "status": "succeeded",
                "output": "result",
            },
        ):
            result = await replicate_service.wait_for_prediction(
                "pred-123", timeout_s=10, poll_s=0.1
            )

            assert result["status"] == "succeeded"
            assert result["output"] == "result"

    async def test_wait_raises_on_failure(self, replicate_service):
        """Test that wait raises error on failed prediction."""
        with patch.object(
            replicate_service,
            "get_prediction",
            new_callable=AsyncMock,
            return_value={
                "id": "pred-123",
                "status": "failed",
                "error": "Model error",
            },
        ):
            with pytest.raises(ReplicatePredictionError) as exc_info:
                await replicate_service.wait_for_prediction("pred-123", timeout_s=10, poll_s=0.1)

            assert exc_info.value.prediction_id == "pred-123"
            assert exc_info.value.status == "failed"
            assert "Model error" in str(exc_info.value)

    async def test_wait_raises_on_canceled(self, replicate_service):
        """Test that wait raises error on canceled prediction."""
        with patch.object(
            replicate_service,
            "get_prediction",
            new_callable=AsyncMock,
            return_value={
                "id": "pred-123",
                "status": "canceled",
            },
        ):
            with pytest.raises(ReplicatePredictionError) as exc_info:
                await replicate_service.wait_for_prediction("pred-123", timeout_s=10, poll_s=0.1)

            assert exc_info.value.status == "canceled"

    async def test_wait_times_out(self, replicate_service):
        """Test that wait raises TimeoutError when prediction doesn't complete."""
        with patch.object(
            replicate_service,
            "get_prediction",
            new_callable=AsyncMock,
            return_value={
                "id": "pred-123",
                "status": "processing",
            },
        ):
            with pytest.raises(TimeoutError) as exc_info:
                await replicate_service.wait_for_prediction("pred-123", timeout_s=0.2, poll_s=0.1)

            assert "pred-123" in str(exc_info.value)


class TestNormalizeFileOutputs:
    """Tests for normalize_file_outputs method."""

    async def test_none_returns_empty_list(self, replicate_service):
        """Test that None output returns empty list."""
        result = await replicate_service.normalize_file_outputs(None)
        assert result == []

    async def test_string_url_downloads(self, replicate_service):
        """Test that string URL is downloaded."""
        with patch.object(
            replicate_service,
            "download_output",
            new_callable=AsyncMock,
            return_value=b"file content",
        ):
            result = await replicate_service.normalize_file_outputs("https://example.com/file.jpg")

            assert result == [b"file content"]

    async def test_list_of_urls_downloads_all(self, replicate_service):
        """Test that list of URLs downloads all files."""
        with patch.object(
            replicate_service,
            "download_output",
            new_callable=AsyncMock,
            return_value=b"content",
        ):
            result = await replicate_service.normalize_file_outputs(
                ["https://example.com/1.jpg", "https://example.com/2.jpg"]
            )

            assert len(result) == 2
            assert all(r == b"content" for r in result)

    async def test_unsupported_type_raises(self, replicate_service):
        """Test that unsupported output type raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            await replicate_service.normalize_file_outputs(12345)

        assert "Unsupported Replicate output type" in str(exc_info.value)


class TestServiceConfiguration:
    """Tests for service configuration."""

    def test_raises_without_token(self):
        """Test that service raises if no token configured."""
        with patch("app.services.replicate_service.settings") as mock_settings:
            mock_settings.REPLICATE_API_TOKEN = None

            with pytest.raises(RuntimeError) as exc_info:
                ReplicateService()

            assert "REPLICATE_API_TOKEN" in str(exc_info.value)

    def test_accepts_explicit_token(self):
        """Test that service accepts explicit token."""
        service = ReplicateService(api_token="explicit-token")
        assert service.api_token == "explicit-token"
