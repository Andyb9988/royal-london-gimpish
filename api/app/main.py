from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.assets import router as assets_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.reports import router as reports_router
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app)
    yield
    await close_db(app)


app = FastAPI(title="Royal London Gimpish API", lifespan=lifespan)

app.include_router(reports_router)
app.include_router(assets_router)
app.include_router(jobs_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
