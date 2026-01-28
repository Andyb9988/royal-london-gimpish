from datetime import timedelta
from typing import BinaryIO

from google.cloud import storage

from app.core.config import settings

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def _get_bucket() -> storage.Bucket:
    if not settings.GCS_BUCKET:
        raise RuntimeError("GCS_BUCKET is not configured")
    client = _get_client()
    return client.bucket(settings.GCS_BUCKET)


def upload_bytes(
    gcs_path: str,
    data: bytes,
    *,
    content_type: str | None = None,
) -> None:
    bucket = _get_bucket()
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(data, content_type=content_type)


def upload_fileobj(
    gcs_path: str,
    fileobj: BinaryIO,
    *,
    content_type: str | None = None,
) -> None:
    bucket = _get_bucket()
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(fileobj, content_type=content_type)


def signed_get_url(gcs_path: str, *, expires_s: int = 3600) -> str:
    bucket = _get_bucket()
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(expiration=timedelta(seconds=expires_s), method="GET")


__all__ = ["upload_bytes", "upload_fileobj", "signed_get_url"]
