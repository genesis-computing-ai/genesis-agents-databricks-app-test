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
    # Create indexes using PostgreSQL's IF NOT EXISTS to avoid errors
    # This avoids the need to check for existence separately, which can cause connection issues
    print("DEBUG: Starting upgrade in add_todo_indexes")
    connection = op.get_bind()
    
    # Use raw SQL with IF NOT EXISTS to create indexes safely
    # This avoids connection management issues with op.get_bind()
    indexes = [
        ('idx_todos_completed', ['completed']),
        ('idx_todos_priority', ['priority']),
        ('idx_todos_created_at', ['created_at']),
        ('idx_todos_completed_priority', ['completed', 'priority']),
    ]
    
    for index_name, columns in indexes:
        print(f"DEBUG: Creating index {index_name}")
        columns_str = ', '.join(columns)
        connection.execute(text(f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON todos ({columns_str})
        """))
        print(f"DEBUG: Created index {index_name}")
    
    print("DEBUG: Finished upgrade in add_todo_indexes")


def downgrade() -> None:
    op.drop_index('idx_todos_completed_priority', 'todos')
    op.drop_index('idx_todos_created_at', 'todos')
    op.drop_index('idx_todos_priority', 'todos')
    op.drop_index('idx_todos_completed', 'todos')

