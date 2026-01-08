"""Add is_verified field for fastapi-users

Revision ID: add_is_verified
Revises: e2412789c190
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_verified'
down_revision = '1a31ce608336'  # Based on cascade delete relationships migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_verified column to user table
    op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_verified column
    op.drop_column('user', 'is_verified')
