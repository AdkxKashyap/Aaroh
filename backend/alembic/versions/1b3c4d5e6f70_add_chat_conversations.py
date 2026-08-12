"""add chat conversations

Revision ID: 1b3c4d5e6f70
Revises: e6b6225578f4
Create Date: 2026-08-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1b3c4d5e6f70"
down_revision: Union[str, Sequence[str], None] = "e6b6225578f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CHAT_STATUS_ENUM = sa.Enum(
    "NEW",
    "PROCESSING",
    "CLARIFICATION_REQUIRED",
    "AWAITING_APPROVAL",
    "APPROVED",
    "EXECUTING",
    "COMPLETED",
    "REJECTED",
    "FAILED",
    name="chatconversationstatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    CHAT_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("status", CHAT_STATUS_ENUM, nullable=False),
        sa.Column("current_intent", sa.String(), nullable=True),
        sa.Column("last_user_message", sa.Text(), nullable=True),
        sa.Column("last_assistant_message", sa.Text(), nullable=True),
        sa.Column(
            "workflow_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("chat_conversations"):
        op.drop_table("chat_conversations")

    CHAT_STATUS_ENUM.drop(bind, checkfirst=True)
