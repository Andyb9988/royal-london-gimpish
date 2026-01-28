"""add report failed status

Revision ID: 4c0a9fbf8a7d
Revises: 6b9e2b5e1b6a
Create Date: 2026-01-27 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "4c0a9fbf8a7d"
down_revision = "6b9e2b5e1b6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE report_status ADD VALUE IF NOT EXISTS 'failed'")


def downgrade() -> None:
    op.execute("UPDATE reports SET status='archived' WHERE status='failed'")
    op.execute("ALTER TYPE report_status RENAME TO report_status_old")
    op.execute(
        "CREATE TYPE report_status AS ENUM ('draft','processing','published','archived')"
    )
    op.execute(
        "ALTER TABLE reports ALTER COLUMN status TYPE report_status "
        "USING status::text::report_status"
    )
    op.execute("DROP TYPE report_status_old")
