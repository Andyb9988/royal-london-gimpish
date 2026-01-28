from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AssetKind, AssetStatus


class AssetUploadUrlRequest(BaseModel):
    kind: AssetKind
    mime_type: str = Field(..., min_length=1, max_length=255)


class AssetUploadUrlResponse(BaseModel):
    gcs_path: str
    upload_url: str | None = None


class AssetAttachRequest(BaseModel):
    kind: AssetKind
    gcs_path: str = Field(..., min_length=1)
    mime_type: str | None = Field(None, max_length=255)
    size_bytes: int | None = Field(None, ge=0)


class AssetReadUrlRequest(BaseModel):
    kind: AssetKind


class AssetReadUrlResponse(BaseModel):
    gcs_path: str
    url: str | None = None


class AssetResponse(BaseModel):
    id: str
    report_id: str
    kind: AssetKind
    gcs_path: str
    mime_type: str | None
    status: AssetStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "AssetUploadUrlRequest",
    "AssetUploadUrlResponse",
    "AssetAttachRequest",
    "AssetReadUrlRequest",
    "AssetReadUrlResponse",
    "AssetResponse",
]
