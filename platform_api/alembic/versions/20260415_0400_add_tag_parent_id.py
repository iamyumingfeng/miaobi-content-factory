"""
Add tag parent_id for hierarchical tags

Revision ID: 20260415_0400
Revises: 20260415_0300
Create Date: 2025-04-15 14:40:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260415_0400'
down_revision = '20260415_0300'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_id column to material_tag table
    op.add_column(
        'material_tag',
        sa.Column(
            'parent_id',
            sa.BigInteger(),
            nullable=True,
            comment='父标签ID（NULL表示平台，非NULL表示平台下的标签）'
        )
    )
    
    # Create index on parent_id
    op.create_index(
        'ix_material_tag_parent_id',
        'material_tag',
        ['parent_id'],
        unique=False
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_material_tag_parent',
        'material_tag',
        'material_tag',
        ['parent_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_material_tag_parent', 'material_tag', type_='foreignkey')
    
    # Drop index
    op.drop_index('ix_material_tag_parent_id', table_name='material_tag')
    
    # Drop column
    op.drop_column('material_tag', 'parent_id')
