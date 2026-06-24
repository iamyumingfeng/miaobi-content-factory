"""add_profile_fields_to_sub_user

Revision ID: 20260421_1045
Revises: 79c638819ac6
Create Date: 2026-04-21 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '20260421_1045'
down_revision: Union[str, None] = '79c638819ac6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('sub_user')]

    if 'fan_profile' not in columns:
        op.add_column('sub_user', sa.Column('fan_profile', sa.Text(), nullable=True, comment='粉丝画像描述'))
    if 'user_positioning' not in columns:
        op.add_column('sub_user', sa.Column('user_positioning', sa.String(500), nullable=True, comment='账号定位'))
    if 'content_style' not in columns:
        op.add_column('sub_user', sa.Column('content_style', sa.String(500), nullable=True, comment='内容风格'))


def downgrade() -> None:
    op.drop_column('sub_user', 'content_style')
    op.drop_column('sub_user', 'user_positioning')
    op.drop_column('sub_user', 'fan_profile')
