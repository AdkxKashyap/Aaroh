"""add normalized name to school classes

Revision ID: f9d3c3c5b6a1
Revises: 1b3c4d5e6f70
Create Date: 2026-08-14 00:00:00.000000

"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9d3c3c5b6a1"
down_revision: Union[str, Sequence[str], None] = "1b3c4d5e6f70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def normalize_class_name(name):
    if name is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def upgrade() -> None:
    op.add_column(
        "school_classes",
        sa.Column("normalized_name", sa.String(length=100), nullable=True),
    )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, name FROM school_classes")).fetchall()
    for class_id, class_name in rows:
        bind.execute(
            sa.text(
                "UPDATE school_classes SET normalized_name = :normalized WHERE id = :id"
            ),
            {"normalized": normalize_class_name(class_name), "id": class_id},
        )

    op.alter_column("school_classes", "normalized_name", nullable=False)
    op.create_index(
        op.f("ix_school_classes_normalized_name"),
        "school_classes",
        ["normalized_name"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_school_classes_normalized_name"), table_name="school_classes"
    )
    op.drop_column("school_classes", "normalized_name")
