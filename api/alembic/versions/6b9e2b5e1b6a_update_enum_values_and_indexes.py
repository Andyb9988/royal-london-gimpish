"""update enum values and indexes

Revision ID: 6b9e2b5e1b6a
Revises: 2921e44f14bc
Create Date: 2026-01-27 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6b9e2b5e1b6a"
down_revision = "2921e44f14bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE report_status RENAME VALUE 'submitted' TO 'processing'")
    op.execute("ALTER TYPE job_type RENAME VALUE 'extract' TO 'extract_moments'")
    op.execute("ALTER TYPE job_type RENAME VALUE 'gimpify' TO 'gimpify_image'")
    op.execute("ALTER TYPE job_type RENAME VALUE 'video' TO 'generate_video'")

    op.add_column("jobs", sa.Column("provider_job_id", sa.String(length=255)))

    op.create_index("ix_assets_report_id_kind", "assets", ["report_id", "kind"])
    op.create_index("ix_reports_status_date", "reports", ["status", "date"])


def downgrade() -> None:
    op.drop_index("ix_reports_status_date", table_name="reports")
    op.drop_index("ix_assets_report_id_kind", table_name="assets")

    op.drop_column("jobs", "provider_job_id")

    op.execute("ALTER TYPE job_type RENAME VALUE 'generate_video' TO 'video'")
    op.execute("ALTER TYPE job_type RENAME VALUE 'gimpify_image' TO 'gimpify'")
    op.execute("ALTER TYPE job_type RENAME VALUE 'extract_moments' TO 'extract'")
    op.execute("ALTER TYPE report_status RENAME VALUE 'processing' TO 'submitted'")
