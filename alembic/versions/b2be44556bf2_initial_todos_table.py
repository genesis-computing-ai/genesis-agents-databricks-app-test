"""initial todos table

Revision ID: b2be44556bf2
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2be44556bf2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create todos table
    # Detect database dialect for timestamp defaults
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    if is_sqlite:
        # SQLite uses datetime('now') for timestamps
        # Note: SQLite doesn't support onupdate in column definition
        created_at_default = sa.text("(datetime('now'))")
        updated_at_default = sa.text("(datetime('now'))")
        # For SQLite, we'll handle updated_at in application code
        updated_at_col = sa.Column('updated_at', sa.DateTime(timezone=True), server_default=updated_at_default, nullable=False)
    else:
        # PostgreSQL and other databases use now()
        created_at_default = sa.text('now()')
        updated_at_default = sa.text('now()')
        # PostgreSQL supports onupdate
        updated_at_col = sa.Column('updated_at', sa.DateTime(timezone=True), server_default=updated_at_default, onupdate=updated_at_default, nullable=False)
    
    op.create_table(
        'todos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=created_at_default, nullable=False),
        updated_at_col,
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('todos')

