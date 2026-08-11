"""add guardian role

Revision ID: e5f2d719c79d
Revises: 0d2f21fa61cb
Create Date: 2026-08-11 10:30:00.000000

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f2d719c79d"
down_revision: Union[str, Sequence[str], None] = "0d2f21fa61cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    guardian_role_id = str(uuid.uuid4())
    op.execute(
        sa.text("""
            INSERT INTO roles (id, name, description, created_at, updated_at)
            SELECT :id, :name, :description, NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = :name)
            """).bindparams(
            id=guardian_role_id,
            name="GUARDIAN",
            description="Guardian role",
        )
    )


def downgrade() -> None:
    op.execute(sa.text("""
            DELETE FROM user_roles
            WHERE role_id = (
                SELECT id FROM roles WHERE name = :name
            )
            """).bindparams(name="GUARDIAN"))
    op.execute(
        sa.text("DELETE FROM roles WHERE name = :name").bindparams(name="GUARDIAN")
    )
