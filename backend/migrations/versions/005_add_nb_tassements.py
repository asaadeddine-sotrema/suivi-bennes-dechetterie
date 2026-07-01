"""add_nb_tassements

Revision ID: 005
Revises: 004
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tassements', sa.Column('nb_tassements', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tassements', 'nb_tassements')
