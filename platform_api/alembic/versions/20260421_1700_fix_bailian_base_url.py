"""fix bailian base_url from /api/v1 to /compatible-mode/v1

Revision ID: 20260421_1700
Revises: 20260421_1600_add_dedup_and_current_step
Create Date: 2026-04-21 17:00:00
"""
from alembic import op

revision = "20260421_1700"
down_revision = "20260421_1600"
branch_labels = None
depends_on = None


def upgrade():
    # Fix bailian LLM configs that have /api/v1 instead of /compatible-mode/v1
    op.execute("""
        UPDATE model_config
        SET base_url = REPLACE(base_url, '/api/v1', '/compatible-mode/v1')
        WHERE platform = 'bailian'
          AND model_type = 'llm'
          AND base_url LIKE '%/api/v1%'
    """)


def downgrade():
    op.execute("""
        UPDATE model_config
        SET base_url = REPLACE(base_url, '/compatible-mode/v1', '/api/v1')
        WHERE platform = 'bailian'
          AND model_type = 'llm'
          AND base_url LIKE '%/compatible-mode/v1%'
    """)
