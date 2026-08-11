"""add guardian links

Revision ID: 0d2f21fa61cb
Revises: 9d5d4a2f0a1
Create Date: 2026-08-11 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d2f21fa61cb"
down_revision: Union[str, Sequence[str], None] = "9d5d4a2f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guardian_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("guardian_user_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["guardian_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "guardian_user_id",
            "student_id",
            name="uq_guardian_student",
        ),
    )


def downgrade() -> None:
    op.drop_table("guardian_links")
