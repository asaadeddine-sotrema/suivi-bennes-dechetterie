"""add_tassement_prevu

Revision ID: 001
Revises:
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tassements', sa.Column('tassement_prevu_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('tassements', 'tassement_prevu_at')
