"""merge heads

Revision ID: 3fb3dee13d1a
Revises: 20548f2db591, 8c12d9aef5b2
Create Date: 2026-08-08 13:13:04.946336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fb3dee13d1a'
down_revision: Union[str, Sequence[str], None] = ('20548f2db591', '8c12d9aef5b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
