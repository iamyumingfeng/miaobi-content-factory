"""merge multiple heads for scheduled_task feature

Revision ID: a566112d7917
Revises: 51308309a53a, 20260515_1100, 20260515_1200
Create Date: 2026-05-15 12:27:11.545553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a566112d7917'
down_revision: Union[str, None] = ('51308309a53a', '20260515_1100', '20260515_1200')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
