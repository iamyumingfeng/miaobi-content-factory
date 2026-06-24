"""merge dashboard and template heads

Revision ID: 5d7b4ddc4bb6
Revises: 20260420_0100, 20260420_1500
Create Date: 2026-04-20 15:47:03.014771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d7b4ddc4bb6'
down_revision: Union[str, None] = ('20260420_0100', '20260420_1500')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
