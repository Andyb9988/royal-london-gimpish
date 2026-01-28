from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_author_id
from app.api.errors import handle_service_error
from app.db.session import get_db
from app.schemas.job import JobResponse
from app.services import report_service

router = APIRouter(prefix="/v1/reports/{report_id}/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    report_id: str,
    author_id: str = Depends(get_author_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await report_service.list_jobs(db, report_id, author_id)
    except Exception as exc:
        handle_service_error(exc)
