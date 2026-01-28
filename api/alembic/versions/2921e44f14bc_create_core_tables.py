"""create core tables

Revision ID: 2921e44f14bc
Revises: 
Create Date: 2026-01-27 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2921e44f14bc"
down_revision = None
branch_labels = None
depends_on = None

report_status_enum = sa.Enum(
    "draft",
    "submitted",
    "published",
    "archived",
    name="report_status",
)
asset_kind_enum = sa.Enum(
    "gimp_original",
    "gimpified_image",
    "video",
    name="asset_kind",
)
asset_status_enum = sa.Enum(
    "pending",
    "ready",
    "failed",
    name="asset_status",
)
job_type_enum = sa.Enum(
    "extract",
    "gimpify",
    "video",
    name="job_type",
)
job_status_enum = sa.Enum(
    "queued",
    "running",
    "succeeded",
    "failed",
    name="job_status",
)


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("author_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("opponent", sa.String(length=255)),
        sa.Column("content", sa.Text()),
        sa.Column("status", report_status_enum, nullable=False),
        sa.Column("gimp_name", sa.String(length=255)),
        sa.Column("champagne_moment", sa.String(length=255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("report_id", sa.String(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("kind", asset_kind_enum, nullable=False),
        sa.Column("gcs_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=255)),
        sa.Column("status", asset_status_enum, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_assets_report_id", "assets", ["report_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("report_id", sa.String(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("type", job_type_enum, nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text()),
        sa.Column("idempotency_key", sa.String(length=255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("report_id", "type", name="uq_jobs_report_id_type"),
    )
    op.create_index("ix_jobs_report_id", "jobs", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_report_id", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("ix_assets_report_id", table_name="assets")
    op.drop_table("assets")

    op.drop_table("reports")

    bind = op.get_bind()
    job_status_enum.drop(bind, checkfirst=True)
    job_type_enum.drop(bind, checkfirst=True)
    asset_status_enum.drop(bind, checkfirst=True)
    asset_kind_enum.drop(bind, checkfirst=True)
    report_status_enum.drop(bind, checkfirst=True)
