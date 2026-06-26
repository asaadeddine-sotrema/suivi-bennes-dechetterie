"""add_tassement_demande

Revision ID: 004
Revises: 003
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tassements', sa.Column('tassement_demande', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('tassements', sa.Column('tassement_demande_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('tassements', 'tassement_demande_at')
    op.drop_column('tassements', 'tassement_demande')
