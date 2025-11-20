"""add todo indexes

Revision ID: add_todo_indexes
Revises: b2be44556bf2
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'add_todo_indexes'
down_revision: Union[str, None] = 'b2be44556bf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if indexes already exist to avoid errors
    connection = op.get_bind()
    
    def index_exists(index_name: str) -> bool:
        """Check if an index already exists."""
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = :index_name
            )
        """), {"index_name": index_name})
        return result.scalar()
    
    # Index for filtering by completion status
    if not index_exists('idx_todos_completed'):
        op.create_index('idx_todos_completed', 'todos', ['completed'])
    
    # Index for filtering by priority
    if not index_exists('idx_todos_priority'):
        op.create_index('idx_todos_priority', 'todos', ['priority'])
    
    # Index for ordering by creation date (most common query pattern)
    if not index_exists('idx_todos_created_at'):
        op.create_index('idx_todos_created_at', 'todos', ['created_at'])
    
    # Composite index for common filter combinations (completed + priority)
    if not index_exists('idx_todos_completed_priority'):
        op.create_index('idx_todos_completed_priority', 'todos', ['completed', 'priority'])


def downgrade() -> None:
    op.drop_index('idx_todos_completed_priority', 'todos')
    op.drop_index('idx_todos_created_at', 'todos')
    op.drop_index('idx_todos_priority', 'todos')
    op.drop_index('idx_todos_completed', 'todos')

