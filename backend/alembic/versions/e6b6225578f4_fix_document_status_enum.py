"""fix document status enum

Revision ID: e6b6225578f4
Revises: 56ed45e8b150
Create Date: 2026-08-11 12:45:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6b6225578f4"
down_revision: Union[str, Sequence[str], None] = "56ed45e8b150"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the PostgreSQL enum type and repair the documents table defaults."""
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documentstatus') THEN
                CREATE TYPE documentstatus AS ENUM (
                    'UPLOADED',
                    'PARSING',
                    'PARSED',
                    'CLARIFICATION',
                    'AWAITING_APPROVAL',
                    'APPROVED',
                    'APPLIED'
                );
            END IF;
        END
        $$;
        """)

    op.execute("""
        ALTER TABLE documents
        ALTER COLUMN status TYPE documentstatus
        USING status::text::documentstatus
        """)

    op.execute("""
        ALTER TABLE documents
        ALTER COLUMN created_at SET DEFAULT now()
        """)

    op.execute("""
        ALTER TABLE documents
        ALTER COLUMN updated_at SET DEFAULT now()
        """)

    op.execute("""
        ALTER TABLE document_versions
        ALTER COLUMN created_at SET DEFAULT now()
        """)

    op.execute("""
        ALTER TABLE document_versions
        ALTER COLUMN updated_at SET DEFAULT now()
        """)


def downgrade() -> None:
    """Restore the column to VARCHAR and drop the enum type if it is safe to do so."""
    op.execute("""
        ALTER TABLE documents
        ALTER COLUMN status TYPE VARCHAR
        USING status::text
        """)

    op.execute("DROP TYPE IF EXISTS documentstatus")
