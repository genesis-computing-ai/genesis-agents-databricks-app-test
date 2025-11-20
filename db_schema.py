"""
Database schema definitions using SQLAlchemy Core.
"""
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    func,
)

# Create metadata object for schema management
metadata = MetaData()

# Define todos table using SQLAlchemy Core
todos_table = Table(
    "todos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(255), nullable=False),
    Column("description", Text, nullable=True),
    Column("completed", Boolean, default=False, nullable=False),
    Column("priority", Integer, nullable=False, default=2),  # 0=Critical, 1=High, 2=Medium, 3=Low, 4=Backlog
    Column("due_date", DateTime(timezone=True), nullable=True),
    Column("payload", JSON, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

