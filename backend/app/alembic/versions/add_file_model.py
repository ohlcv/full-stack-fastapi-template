"""Add file model

Revision ID: add_file_model
Revises: add_is_verified
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = 'add_file_model'
down_revision = 'add_is_verified'  # Based on add_is_verified migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create file table
    op.create_table(
        'file',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_owner_id'), 'file', ['owner_id'], unique=False)


def downgrade() -> None:
    # Drop file table
    op.drop_index(op.f('ix_file_owner_id'), table_name='file')
    op.drop_table('file')
