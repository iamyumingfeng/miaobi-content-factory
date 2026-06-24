"""update prompt_template_type_enum to use new type names

Revision ID: 20260423_1710
Revises: 20260423_1600
Create Date: 2026-04-23 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260423_1710'
down_revision: Union[str, None] = '20260423_1600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For MySQL, we need to:
    # 1. Rename old enum type (if exists)
    # 2. Alter column to use new enum with old values first
    # 3. Update data values to new values
    # 4. Alter column again to final enum with new values

    # Step 1: First, change column to string temporarily
    op.alter_column(
        'prompt_template',
        'template_type',
        existing_type=sa.Enum('text_system', 'image_system', 'aigc_prompt_generator', name='prompt_template_type_enum'),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # Step 2: Update existing data
    op.execute("UPDATE prompt_template SET template_type = 'aigc_text_prompt_generator' WHERE template_type = 'aigc_prompt_generator'")
    op.execute("UPDATE prompt_template SET template_type = 'aigc_image_prompt_generator' WHERE template_type = 'image_system'")
    op.execute("DELETE FROM prompt_template WHERE template_type = 'text_system'")

    # Step 3: Create new enum and alter column back
    op.alter_column(
        'prompt_template',
        'template_type',
        existing_type=sa.String(50),
        type_=sa.Enum('aigc_text_prompt_generator', 'aigc_image_prompt_generator', name='prompt_template_type_enum'),
        existing_nullable=False,
        existing_server_default=None,
    )


def downgrade() -> None:
    # Revert the changes
    # Step 1: Change column to string temporarily
    op.alter_column(
        'prompt_template',
        'template_type',
        existing_type=sa.Enum('aigc_text_prompt_generator', 'aigc_image_prompt_generator', name='prompt_template_type_enum'),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # Step 2: Update existing data back
    op.execute("UPDATE prompt_template SET template_type = 'aigc_prompt_generator' WHERE template_type = 'aigc_text_prompt_generator'")
    op.execute("UPDATE prompt_template SET template_type = 'image_system' WHERE template_type = 'aigc_image_prompt_generator'")

    # Step 3: Create old enum and alter column back
    op.alter_column(
        'prompt_template',
        'template_type',
        existing_type=sa.String(50),
        type_=sa.Enum('text_system', 'image_system', 'aigc_prompt_generator', name='prompt_template_type_enum'),
        existing_nullable=False,
        existing_server_default=None,
    )
