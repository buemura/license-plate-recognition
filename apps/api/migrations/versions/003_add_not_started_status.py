"""Add NOT_STARTED status to recognition_requests

Revision ID: 003
Revises: 002
Create Date: 2026-02-19

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add NOT_STARTED to the status enum.
    # PostgreSQL requires new enum values to be committed before they can
    # be used in DML statements, so we commit the current transaction first.
    op.execute("COMMIT")
    op.execute("ALTER TYPE recognitionstatus ADD VALUE IF NOT EXISTS 'NOT_STARTED'")
    op.execute("BEGIN")

    # Update existing PENDING records to NOT_STARTED
    op.execute(
        "UPDATE recognition_requests SET status = 'NOT_STARTED' WHERE status = 'PENDING'"
    )

    # Update the default value for new records
    op.execute(
        "ALTER TABLE recognition_requests ALTER COLUMN status SET DEFAULT 'NOT_STARTED'"
    )


def downgrade() -> None:
    # Revert NOT_STARTED records back to PENDING
    op.execute(
        "UPDATE recognition_requests SET status = 'PENDING' WHERE status = 'NOT_STARTED'"
    )

    # Restore PENDING as the default
    op.execute(
        "ALTER TABLE recognition_requests ALTER COLUMN status SET DEFAULT 'PENDING'"
    )

    # Note: Cannot remove enum value in PostgreSQL, so NOT_STARTED will remain
