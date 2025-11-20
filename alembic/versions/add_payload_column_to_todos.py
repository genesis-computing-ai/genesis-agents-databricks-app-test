"""add payload column to todos

Revision ID: add_payload_column
Revises: add_todo_indexes
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_payload_column'
down_revision: Union[str, None] = 'add_todo_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add payload JSON column to todos table
    # Use dialect-aware JSON column type
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # PostgreSQL supports native JSON type
        op.add_column('todos', sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    else:
        # SQLite and other databases use SQLAlchemy's generic JSON type
        op.add_column('todos', sa.Column('payload', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('todos', 'payload')

