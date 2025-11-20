"""
TODO repository with CRUD operations using SQLAlchemy Async.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from utils.db_connection import get_async_session
from db_schema import todos_table
from todo_models import TodoCreate, TodoUpdate, TodoResponse
from utils.timing_utils import TimingInfo, TimingContext
import logging
import time

logger = logging.getLogger(__name__)


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "completed": row.completed,
        "priority": row.priority,
        "due_date": row.due_date,
        "payload": row.payload,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def create_todo(todo_data: TodoCreate, timing_info: Optional[TimingInfo] = None) -> Tuple[Dict[str, Any], Optional[TimingInfo]]:
    """
    Create a new TODO item.
    
    Args:
        todo_data: TodoCreate model with TODO data
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (dictionary containing the created TODO, timing_info)
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build INSERT statement using SQLAlchemy Core
            stmt = insert(todos_table).values(
                title=todo_data.title,
                description=todo_data.description,
                priority=todo_data.priority,
                due_date=todo_data.due_date,
                payload=todo_data.payload,
                completed=False,
            ).returning(todos_table)
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            row = result.fetchone()
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            # Commit is handled by the context manager
            
            # Measure data transformation
            transform_start = time.time()
            result_dict = _row_to_dict(row)
            timing_info.data_transformation_ms = (time.time() - transform_start) * 1000
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            return result_dict, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error creating TODO: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise


async def get_todo(todo_id: int, timing_info: Optional[TimingInfo] = None) -> Tuple[Optional[Dict[str, Any]], Optional[TimingInfo]]:
    """
    Get a TODO item by ID.
    
    Args:
        todo_id: TODO item ID
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (dictionary containing the TODO or None, timing_info)
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build SELECT statement with WHERE clause
            stmt = select(todos_table).where(todos_table.c.id == todo_id)
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            row = result.fetchone()
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            
            if row is None:
                timing_info.repository_total_ms = (time.time() - repo_start) * 1000
                return None, timing_info
            
            # Measure data transformation
            transform_start = time.time()
            result_dict = _row_to_dict(row)
            timing_info.data_transformation_ms = (time.time() - transform_start) * 1000
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            return result_dict, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error getting TODO {todo_id}: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise


async def list_todos(completed: Optional[bool] = None, priority: Optional[int] = None, timing_info: Optional[TimingInfo] = None) -> Tuple[List[Dict[str, Any]], Optional[TimingInfo]]:
    """
    List all TODO items with optional filtering.
    
    Args:
        completed: Filter by completion status (None = all)
        priority: Filter by priority (None = all)
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (list of dictionaries containing TODO items, timing_info)
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build SELECT statement
            stmt = select(todos_table)
            
            # Add WHERE conditions if filters provided
            if completed is not None:
                stmt = stmt.where(todos_table.c.completed == completed)
            
            if priority is not None:
                stmt = stmt.where(todos_table.c.priority == priority)
            
            # Order by created_at descending (newest first)
            stmt = stmt.order_by(todos_table.c.created_at.desc())
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            rows = result.fetchall()
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            
            # Measure data transformation
            transform_start = time.time()
            result_list = [_row_to_dict(row) for row in rows]
            timing_info.data_transformation_ms = (time.time() - transform_start) * 1000
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            return result_list, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error listing TODOs: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise


async def update_todo(todo_id: int, todo_data: TodoUpdate, timing_info: Optional[TimingInfo] = None) -> Tuple[Optional[Dict[str, Any]], Optional[TimingInfo]]:
    """
    Update an existing TODO item.
    
    Args:
        todo_id: TODO item ID
        todo_data: TodoUpdate model with fields to update
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (dictionary containing the updated TODO or None, timing_info)
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build update values dict (only include provided fields)
            update_values = {}
            if todo_data.title is not None:
                update_values["title"] = todo_data.title
            if todo_data.description is not None:
                update_values["description"] = todo_data.description
            if todo_data.completed is not None:
                update_values["completed"] = todo_data.completed
            if todo_data.priority is not None:
                update_values["priority"] = todo_data.priority
            if todo_data.due_date is not None:
                update_values["due_date"] = todo_data.due_date
            if todo_data.payload is not None:
                update_values["payload"] = todo_data.payload
            
            # Always update updated_at timestamp
            update_values["updated_at"] = datetime.now(timezone.utc)
            
            if not update_values:
                # No fields to update, just return the existing TODO
                result_dict, nested_timing = await get_todo(todo_id, timing_info)
                timing_info.repository_total_ms = (time.time() - repo_start) * 1000
                return result_dict, timing_info
            
            # Build UPDATE statement
            stmt = (
                update(todos_table)
                .where(todos_table.c.id == todo_id)
                .values(**update_values)
                .returning(todos_table)
            )
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            row = result.fetchone()
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            # Commit is handled by the context manager
            
            if row is None:
                timing_info.repository_total_ms = (time.time() - repo_start) * 1000
                return None, timing_info
            
            # Measure data transformation
            transform_start = time.time()
            result_dict = _row_to_dict(row)
            timing_info.data_transformation_ms = (time.time() - transform_start) * 1000
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            return result_dict, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error updating TODO {todo_id}: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise


async def delete_todo(todo_id: int, timing_info: Optional[TimingInfo] = None) -> Tuple[bool, Optional[TimingInfo]]:
    """
    Delete a TODO item.
    
    Args:
        todo_id: TODO item ID
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (True if deleted False if not found, timing_info)
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build DELETE statement
            stmt = delete(todos_table).where(todos_table.c.id == todo_id)
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            # Commit is handled by the context manager
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            # Return True if any row was deleted
            return result.rowcount > 0, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error deleting TODO {todo_id}: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise


async def test_select_one(timing_info: Optional[TimingInfo] = None) -> Tuple[int, Optional[TimingInfo]]:
    """
    Test SELECT 1 query - minimal database operation to isolate network/connection overhead.
    
    Args:
        timing_info: Optional timing info object to populate
        
    Returns:
        Tuple of (result (always 1), timing_info)
    """
    if timing_info is None:
        timing_info = TimingInfo()
    
    repo_start = time.time()
    
    try:
        # Measure connection acquisition
        conn_start = time.time()
        async with get_async_session() as session:
            timing_info.connection_acquisition_ms = (time.time() - conn_start) * 1000
            
            # Build SELECT 1 statement (minimal database work)
            from sqlalchemy import text
            stmt = text("SELECT 1")
            
            # Measure query execution
            query_start = time.time()
            result = await session.execute(stmt)
            row = result.scalar()
            timing_info.query_execution_ms = (time.time() - query_start) * 1000
            
            # Measure data transformation (minimal - just getting scalar)
            transform_start = time.time()
            result_value = int(row) if row is not None else 1
            timing_info.data_transformation_ms = (time.time() - transform_start) * 1000
            
            timing_info.repository_total_ms = (time.time() - repo_start) * 1000
            
            return result_value, timing_info
    except SQLAlchemyError as e:
        logger.error(f"Error executing SELECT 1: {e}")
        timing_info.repository_total_ms = (time.time() - repo_start) * 1000
        raise
