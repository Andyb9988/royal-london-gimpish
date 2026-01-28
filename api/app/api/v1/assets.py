from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_author_id
from app.api.errors import handle_service_error
from app.db.session import get_db
from app.schemas.asset import (
    AssetAttachRequest,
    AssetReadUrlRequest,
    AssetReadUrlResponse,
    AssetResponse,
    AssetUploadUrlRequest,
    AssetUploadUrlResponse,
)
from app.services import asset_service, report_service
from app.utils.storage_paths import gcs_object_key, mime_to_ext

router = APIRouter(prefix="/v1/reports/{report_id}/assets", tags=["assets"])


@router.post("/upload-url", response_model=AssetUploadUrlResponse)
async def create_upload_url(
    report_id: str,
    payload: AssetUploadUrlRequest,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        await report_service.get_report(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)

    ext = mime_to_ext(payload.mime_type)
    gcs_path = gcs_object_key(report_id, payload.kind, ext)
    return AssetUploadUrlResponse(gcs_path=gcs_path, upload_url=None)


@router.post("/attach", response_model=AssetResponse)
async def attach_asset(
    report_id: str,
    payload: AssetAttachRequest,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await asset_service.upsert_asset_ready(
            db,
            report_id=report_id,
            author_id=author_id,
            kind=payload.kind,
            gcs_path=payload.gcs_path,
            mime_type=payload.mime_type,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await asset_service.list_assets(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)


@router.post("/read-url", response_model=AssetReadUrlResponse)
async def read_asset_url(
    report_id: str,
    payload: AssetReadUrlRequest,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        assets = await asset_service.list_assets(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)

    asset = next((item for item in assets if item.kind == payload.kind), None)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return AssetReadUrlResponse(gcs_path=asset.gcs_path, url=None)


@router.post("/delete", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def delete_asset(report_id: str, _: str = Depends(get_author_id)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
