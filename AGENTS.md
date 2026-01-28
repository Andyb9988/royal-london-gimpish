## Quick commands (run these first, from repo root)

### Web (Next.js)

```bash
# install deps
cd apps/web
npm ci

# dev server (http://localhost:3000)
npm run dev

# production build + run
npm run build
npm run start

# lint / typecheck / tests (if configured)
npm run lint
npm run typecheck
npm test -- --runInBand

```

### API (FastAPI)

```bash
# create venv + install (uv is preferred)
cd api
uv sync

# run API (http://localhost:8000)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# run tests
uv run pytest -v

# DB migrations (alembic)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

```

### Worker (Redis-backed)

```bash
# start Redis locally
docker run --rm -p 6379:6379 redis:7

# run worker process
cd api
uv run python -m app.workers.runner

```

### One-shot sanity checks

```bash
# API health
curl -sS http://localhost:8000/health

# Web reachable
curl -I http://localhost:3000

```

---

## What we are building (system overview)

We are building a **match-report “mini CMS”** with an asynchronous content generation pipeline. Users submit a report, and the system handles the heavy lifting of extraction and media generation.

### Core User Flow

1. **Create Report:** Content (text), date, opponent, and a "gimp of the day" source image.
2. **Async Generation:**
* **LLM Extraction:** Gets `gimp_name` and `champagne_moment`.
* **Image Derivative:** Creates a "gimpified" version.
* **Video Generation:** Generates video from content via external provider.


3. **Storage:** All media stored in **GCS** and linked via the `assets` table.
4. **Publication:** Stable URL for reading/watching the final report.

---

## Core architectural rules

* **Source of Truth:** Postgres (Neon) stores all state (reports, assets, jobs).
* **Async Work:** Heavy lifting belongs in workers (Redis queue), never in the request/response cycle.
* **Resilience:** Jobs must be **idempotent** and **retry-safe**.
* **Media Delivery:** Serve directly from GCS. **Do not proxy** large media files through FastAPI.

---

## Stack

* **Frontend:** Next.js (React 18), TypeScript, Tailwind CSS.
* **Backend:** FastAPI (Python), SQLAlchemy + Alembic.
* **Infrastructure:** Postgres (Neon), Redis (Queue), GCS (Storage).
* **Providers:** Gemini/LLM (Extraction), Grok/Equivalent (Video).

---

## Repository structure

### Top-level

* `apps/web/` — Next.js frontend
* `api/` — FastAPI backend + migrations + worker
* `infra/` — Deployment (Terraform/Cloud Run)
* `packages/` — Shared types or clients
* `scripts/` — Dev utilities

### Backend (api/) Layout

* `app/core/` — Config, logging, constants
* `app/db/` — Engine, session, repositories
* `app/models/` — SQLAlchemy tables
* `app/schemas/` — Pydantic models (I/O)
* `app/services/` — External integrations (GCS, LLM)
* `app/jobs/` — Logic for specific tasks
* `app/workers/` — Entrypoints/dispatch
* `alembic/` — Migrations

---

## Database schema

| Table | Key Fields | Rules |
| --- | --- | --- |
| **reports** | `id`, `status`, `gimp_name`, `opponent` | Status: `draft` |
| **assets** | `report_id`, `kind`, `gcs_path` | Kind: `gimp_original` |
| **jobs** | `report_id`, `type`, `status`, `attempts` | **Hard Rule:** Unique constraint on `(report_id, type)` |

---

## Deterministic GCS paths (hard rule)

All objects follow this pattern: `reports/{report_id}/{kind}.{ext}`

* `reports/123/gimp_original.jpg`
* `reports/123/video.mp4`

---

## Code style examples

### 1. Deterministic Paths (`api/app/utils/storage_paths.py`)

```python
def gcs_object_key(report_id: str, kind: str, ext: str) -> str:
    ext = ext.lstrip(".").lower()
    return f"reports/{report_id}/{kind}.{ext}"

```

### 2. Job Model (`api/app/models/job.py`)

```python
class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(String, ForeignKey("reports.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    __table_args__ = (UniqueConstraint("report_id", "type", name="uq_jobs_report_id_type"),)

```

### 3. Frontend Video (`apps/web/components/Video.tsx`)

```tsx
export function ReportVideo({ src }: { src: string }) {
  return <video controls preload="metadata" src={src} />;
}
// Note: Ensure GCS headers support Range requests (bytes) for seeking.

```

---

## Testing & Git Workflow

* **Backend:** Mock all external providers. Verify DB writes and job enqueuing.
* **Git:** Use `feat/`, `fix/`, or `chore/` prefixes. Keep migrations in the same PR as model changes.
* **Boundaries:** * **No secrets** in `.env` files should ever be committed.
* **No squashing** existing Alembic history.
* **No destructive** prod DB changes without explicit approval.



---

## Operational rule

External calls must use **timeouts and retries**. Workers must be safe to run twice (Idempotency).

---

Would you like me to generate the boilerplate for the `api/app/services/gcs.py` file to handle those deterministic paths?