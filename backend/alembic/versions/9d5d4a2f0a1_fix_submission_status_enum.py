"""fix submission status enum

Revision ID: 9d5d4a2f0a1
Revises: 1f60a205ee2d
Create Date: 2026-08-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9d5d4a2f0a1"
down_revision: Union[str, Sequence[str], None] = "1f60a205ee2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE submissionstatus RENAME TO submissionstatus_old")

    op.execute(
        "CREATE TYPE submissionstatus AS ENUM ('NOT_SUBMITTED', 'SUBMITTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', 'RESUBMITTED', 'COMPLETED')"
    )

    op.execute(
        "ALTER TABLE submissions ALTER COLUMN status TYPE submissionstatus USING status::text::submissionstatus"
    )

    op.execute("DROP TYPE submissionstatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE submissionstatus RENAME TO submissionstatus_new")

    op.execute(
        "CREATE TYPE submissionstatus AS ENUM ('NOT_SUBMITTED', 'SUBMITTED', 'UNDER_REVIEW', 'RETURNED', 'COMPLETED')"
    )

    op.execute(
        "ALTER TABLE submissions ALTER COLUMN status TYPE submissionstatus USING status::text::submissionstatus"
    )

    op.execute("DROP TYPE submissionstatus_new")
