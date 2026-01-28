"""Replicate API service for running ML model predictions."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

TERMINAL_STATES = {"succeeded", "failed", "canceled"}
REPLICATE_API_BASE = "https://api.replicate.com/v1"

logger = get_logger(__name__)


class ReplicateError(Exception):
    """Base exception for Replicate API errors."""

    pass


class ReplicatePredictionError(ReplicateError):
    """Raised when a prediction fails."""

    def __init__(self, prediction_id: str, status: str, error: str | None = None) -> None:
        self.prediction_id = prediction_id
        self.status = status
        self.error = error
        super().__init__(f"Prediction {prediction_id} {status}: {error or 'unknown error'}")


class ReplicateService:
    """Async-native service for interacting with the Replicate API."""

    def __init__(self, *, api_token: str | None = None) -> None:
        self.api_token = api_token or settings.REPLICATE_API_TOKEN
        if not self.api_token:
            raise RuntimeError("REPLICATE_API_TOKEN is not configured")

        self._headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _get_client(self, timeout: float = 30.0) -> httpx.AsyncClient:
        """Create an async HTTP client with appropriate settings."""
        return httpx.AsyncClient(
            base_url=REPLICATE_API_BASE,
            headers=self._headers,
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

    async def create_prediction(self, model_id: str, inp: dict[str, Any]) -> dict[str, Any]:
        """Create a new prediction on Replicate.

        Args:
            model_id: Either a model identifier (owner/name) or version hash.
            inp: Input parameters for the model.

        Returns:
            The prediction response from the API.
        """
        async with self._get_client() as client:
            if ":" in model_id:
                # It's a version hash
                payload = {"version": model_id, "input": inp}
            else:
                # It's a model identifier
                payload = {"model": model_id, "input": inp}

            response = await client.post("/predictions", json=payload)
            response.raise_for_status()
            return response.json()

    async def get_prediction(self, prediction_id: str) -> dict[str, Any]:
        """Get the current status of a prediction."""
        async with self._get_client() as client:
            response = await client.get(f"/predictions/{prediction_id}")
            response.raise_for_status()
            return response.json()

    async def wait_for_prediction(
        self,
        prediction_id: str,
        *,
        timeout_s: int,
        poll_s: float = 2.0,
    ) -> dict[str, Any]:
        """Wait for a prediction to complete.

        Args:
            prediction_id: The prediction ID to wait for.
            timeout_s: Maximum time to wait in seconds.
            poll_s: Time between polling requests in seconds.

        Returns:
            The final prediction state.

        Raises:
            TimeoutError: If the prediction doesn't complete within the timeout.
            ReplicatePredictionError: If the prediction fails.
        """
        deadline = asyncio.get_event_loop().time() + timeout_s

        while True:
            prediction = await self.get_prediction(prediction_id)
            status = prediction.get("status", "unknown")

            if status in TERMINAL_STATES:
                if status != "succeeded":
                    raise ReplicatePredictionError(
                        prediction_id,
                        status,
                        prediction.get("error"),
                    )
                return prediction

            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError(f"Replicate prediction timed out: {prediction_id}")

            await asyncio.sleep(poll_s)

    async def download_output(self, url: str, *, timeout: float = 60.0) -> bytes:
        """Download file content from a URL (typically Replicate output URLs)."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Replicate output URLs may require auth
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content

    async def normalize_file_outputs(self, output: Any) -> list[bytes]:
        """Normalize prediction output to a list of file bytes.

        Handles various output formats from Replicate models:
        - None -> []
        - str (URL) -> [bytes]
        - list of URLs -> [bytes, ...]
        - file-like object -> [bytes]
        """
        if output is None:
            return []

        if isinstance(output, str):
            return [await self.download_output(output)]

        if isinstance(output, list):
            results: list[bytes] = []
            for item in output:
                results.extend(await self.normalize_file_outputs(item))
            return results

        if hasattr(output, "read"):
            content = output.read()
            if asyncio.iscoroutine(content):
                content = await content
            return [content]

        raise TypeError(f"Unsupported Replicate output type: {type(output)}")


__all__ = ["ReplicateService", "ReplicateError", "ReplicatePredictionError"]
