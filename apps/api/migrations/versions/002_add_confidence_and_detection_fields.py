"""Add confidence and detection fields to recognition_requests

Revision ID: 002
Revises: 001
Create Date: 2025-01-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add confidence score fields
    op.add_column(
        "recognition_requests",
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "recognition_requests",
        sa.Column("detection_confidence", sa.Float(), nullable=True),
    )
    op.add_column(
        "recognition_requests",
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
    )

    # Add review flag
    op.add_column(
        "recognition_requests",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Add plate detection metadata
    op.add_column(
        "recognition_requests",
        sa.Column("bounding_box", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "recognition_requests",
        sa.Column("plate_region", sa.String(length=50), nullable=True),
    )

    # Add NEEDS_REVIEW to the status enum
    op.execute("ALTER TYPE recognitionstatus ADD VALUE IF NOT EXISTS 'NEEDS_REVIEW'")

    # Create index on needs_review for efficient filtering
    op.create_index(
        "ix_recognition_requests_needs_review",
        "recognition_requests",
        ["needs_review"],
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("ix_recognition_requests_needs_review", table_name="recognition_requests")

    # Drop columns
    op.drop_column("recognition_requests", "plate_region")
    op.drop_column("recognition_requests", "bounding_box")
    op.drop_column("recognition_requests", "needs_review")
    op.drop_column("recognition_requests", "ocr_confidence")
    op.drop_column("recognition_requests", "detection_confidence")
    op.drop_column("recognition_requests", "confidence_score")

    # Note: Cannot remove enum value in PostgreSQL, so NEEDS_REVIEW will remain
