"""add_rotation_prevue

Revision ID: 002
Revises: 001
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tassements', sa.Column('rotation_prevue_at', sa.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('tassements', 'rotation_prevue_at')
