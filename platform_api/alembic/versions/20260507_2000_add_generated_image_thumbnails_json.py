"""
Add generated_image_thumbnails_json to generation_item table

Revision ID: 20260507_2000
Revises: 20260507_1910
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260507_2000'
down_revision = '20260507_1910'
branch_labels = None
depends_on = None


def upgrade():
    """
    使用 Python 检查列是否存在，然后安全地添加
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('generation_item')]

    if 'generated_image_thumbnails_json' not in existing_columns:
        op.add_column(
            'generation_item',
            sa.Column('generated_image_thumbnails_json', sa.JSON(), nullable=True, comment='生成的图片缩略图URL列表JSON')
        )


def downgrade():
    pass
