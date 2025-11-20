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
    """
    Create indexes for the todos table to improve query performance.
    
    FIXED: Connection Management Issue
    ===================================
    Previous behavior (BROKEN):
    - Used op.get_bind() to get a connection, then called connection.execute() 
      multiple times to check if indexes exist before creating them
    - Each index_exists() call created a new query that needed to consume results
    - The migration would complete (all indexes created successfully), but then
      Alembic's command.upgrade() would hang indefinitely, never returning control
    
    Why it was stuck:
    - When using op.get_bind() and connection.execute() directly, the connection
      and result sets weren't being properly released back to Alembic's transaction
      context
    - Alembic manages its own transaction lifecycle, and mixing direct connection
      access with Alembic's op methods can cause the transaction to not commit
      properly, leaving the migration in a waiting state
    - The migration function would finish, but Alembic couldn't finalize the
      transaction and update the alembic_version table, causing an indefinite hang
    
    Current solution (FIXED):
    - Use raw SQL with PostgreSQL's "IF NOT EXISTS" clause directly
    - Get the connection once with op.get_bind() and reuse it for all operations
    - Execute DDL statements directly without checking existence first
    - This keeps all operations within Alembic's transaction context properly
    - The transaction commits cleanly and Alembic can update the version table
    """
    print("DEBUG: Starting upgrade in add_todo_indexes")
    connection = op.get_bind()
    
    # Use raw SQL with IF NOT EXISTS to create indexes safely
    # This approach avoids connection management issues by:
    # 1. Not creating separate existence-check queries that need result consumption
    # 2. Using PostgreSQL's native IF NOT EXISTS which handles idempotency
    # 3. Keeping all operations in a single connection context that Alembic manages
    indexes = [
        ('idx_todos_completed', ['completed']),
        ('idx_todos_priority', ['priority']),
        ('idx_todos_created_at', ['created_at']),
        ('idx_todos_completed_priority', ['completed', 'priority']),
    ]
    
    for index_name, columns in indexes:
        print(f"DEBUG: Creating index {index_name}")
        columns_str = ', '.join(columns)
        # Execute DDL directly - no result set to consume, cleaner transaction handling
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

