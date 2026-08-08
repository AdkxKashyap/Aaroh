"""add uuid defaults to id columns

Revision ID: 8c12d9aef5b2
Revises: 4f16e4d45fd1
Create Date: 2026-08-08 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "8c12d9aef5b2"
down_revision: Union[str, Sequence[str], None] = "4f16e4d45fd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.alter_column(
        "roles",
        "id",
        server_default=sa.text("gen_random_uuid()"),
        existing_type=UUID(),
    )
    op.alter_column(
        "users",
        "id",
        server_default=sa.text("gen_random_uuid()"),
        existing_type=UUID(),
    )
    op.alter_column(
        "user_roles",
        "id",
        server_default=sa.text("gen_random_uuid()"),
        existing_type=UUID(),
    )
    op.alter_column(
        "schools",
        "id",
        server_default=sa.text("gen_random_uuid()"),
        existing_type=UUID(),
    )
    op.alter_column(
        "school_classes",
        "id",
        server_default=sa.text("gen_random_uuid()"),
        existing_type=UUID(),
    )


def downgrade() -> None:
    op.alter_column(
        "roles",
        "id",
        server_default=None,
        existing_type=UUID(),
    )
    op.alter_column(
        "users",
        "id",
        server_default=None,
        existing_type=UUID(),
    )
    op.alter_column(
        "user_roles",
        "id",
        server_default=None,
        existing_type=UUID(),
    )
    op.alter_column(
        "schools",
        "id",
        server_default=None,
        existing_type=UUID(),
    )
    op.alter_column(
        "school_classes",
        "id",
        server_default=None,
        existing_type=UUID(),
    )
