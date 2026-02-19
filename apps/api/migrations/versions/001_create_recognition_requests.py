"""Create recognition_requests table

Revision ID: 001
Revises:
Create Date: 2024-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recognition_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("plate_number", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "FAILED", name="recognitionstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on status for faster filtering
    op.create_index(
        "ix_recognition_requests_status",
        "recognition_requests",
        ["status"],
    )

    # Create index on created_at for sorting
    op.create_index(
        "ix_recognition_requests_created_at",
        "recognition_requests",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recognition_requests_created_at", table_name="recognition_requests")
    op.drop_index("ix_recognition_requests_status", table_name="recognition_requests")
    op.drop_table("recognition_requests")
    op.execute("DROP TYPE IF EXISTS recognitionstatus")
