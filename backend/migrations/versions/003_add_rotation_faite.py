"""add_rotation_faite_et_taux_reference

Revision ID: 003
Revises: 002
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tassements', sa.Column('rotation_faite', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('tassements', sa.Column('rotation_faite_at', sa.TIMESTAMP(), nullable=True))
    op.add_column('tassements', sa.Column('taux_reference', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('tassements', 'taux_reference')
    op.drop_column('tassements', 'rotation_faite_at')
    op.drop_column('tassements', 'rotation_faite')
