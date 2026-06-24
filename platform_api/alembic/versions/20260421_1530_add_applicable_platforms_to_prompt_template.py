"""add applicable_platforms to prompt_template

Revision ID: 20260421_1530
Revises: 20260421_1400
Create Date: 2026-04-21 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260421_1530'
down_revision: Union[str, None] = '20260421_1400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column already exists (idempotent migration)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT COUNT(*) as cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = 'prompt_template'
            AND column_name = 'applicable_platforms'
        """)
    )
    exists = result.fetchone()[0] > 0

    if not exists:
        op.add_column(
            'prompt_template',
            sa.Column(
                'applicable_platforms',
                sa.JSON(),
                nullable=True,
                comment="适用平台列表",
            ),
        )


def downgrade() -> None:
    op.drop_column('prompt_template', 'applicable_platforms')
