# Scale Optimization Recommendations

## Quick Reference: Identified Bottlenecks

| # | Bottleneck | Severity | Location | Current Value | Impact |
|---|------------|----------|----------|---------------|--------|
| 1 | Connection Pool Size | 🔴 CRITICAL | `db_connection.py:31` | 5 base + 10 overflow = 15 max | Limits all operations to ~2.28 ops/sec |
| 2 | Async/Sync Mismatch | 🔴 CRITICAL | `app.py` + `todo_repository.py` | Sync functions in async endpoints | Prevents FastAPI concurrency |
| 3 | Missing Indexes | 🟡 HIGH | `alembic/versions/b2be44556bf2_*.py` | No indexes on filters | Slow queries as data grows |
| 4 | No Bulk Operations | 🟡 MEDIUM | `todo_repository.py` | Individual inserts only | Inefficient for bulk creates |
| 5 | Connection Management | 🟢 MEDIUM | `db_connection.py` | Open/close per operation | Adds latency overhead |

---

## Immediate Actions (Do Today)

### 1. Increase Connection Pool Size

**File**: `db_connection.py`

**Current Code** (lines 28-39):
```python
_engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,        # ← CHANGE THIS
    max_overflow=10,     # ← CHANGE THIS
    ...
)
```

**Change To**:
```python
_engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,        # Increased from 5
    max_overflow=30,     # Increased from 10
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }
)
```

**Expected Impact**: 3-5x performance improvement (from 2.28 to ~7-11 ops/sec)

**Risk**: Low - Just increasing pool size

---

### 2. Add Database Indexes

**File**: Create new migration `alembic/versions/xxx_add_todo_indexes.py`

**Code**:
```python
"""add todo indexes

Revision ID: add_todo_indexes
Revises: b2be44556bf2
Create Date: 2025-01-27
"""
from alembic import op

revision = 'add_todo_indexes'
down_revision = 'b2be44556bf2'
branch_labels = None
depends_on = None

def upgrade():
    # Index for filtering by completion status
    op.create_index('idx_todos_completed', 'todos', ['completed'])
    
    # Index for filtering by priority
    op.create_index('idx_todos_priority', 'todos', ['priority'])
    
    # Index for ordering by creation date
    op.create_index('idx_todos_created_at', 'todos', ['created_at'])
    
    # Composite index for common filter combinations
    op.create_index('idx_todos_completed_priority', 'todos', ['completed', 'priority'])

def downgrade():
    op.drop_index('idx_todos_completed_priority', 'todos')
    op.drop_index('idx_todos_created_at', 'todos')
    op.drop_index('idx_todos_priority', 'todos')
    op.drop_index('idx_todos_completed', 'todos')
```

**Run Migration**:
```bash
source myenv311/bin/activate
alembic upgrade head
```

**Expected Impact**: 2-5x improvement for filtered queries

**Risk**: Low - Indexes are safe to add

---

## Short-Term Actions (This Week)

### 3. Convert to Async Database Operations

This is the **biggest performance win** but requires more work.

#### Step 1: Install asyncpg driver

```bash
pip install asyncpg
```

#### Step 2: Update `db_connection.py`

**Replace entire file with**:
```python
"""
Database connection management using SQLAlchemy Async.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from database_config import get_database_url

# Global engine instance (created lazily)
_async_engine = None
_async_session_factory = None

def get_async_engine():
    """Get or create async SQLAlchemy engine instance."""
    global _async_engine, _async_session_factory
    
    if _async_engine is None:
        database_url = get_database_url()
        # Convert postgresql:// to postgresql+asyncpg://
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        _async_engine = create_async_engine(
            async_database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={
                "command_timeout": 30,
            }
        )
        
        _async_session_factory = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    return _async_engine

def get_async_session() -> AsyncSession:
    """Get async session factory."""
    get_async_engine()
    return _async_session_factory()

async def close_async_engine():
    """Close the async database engine."""
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
```

#### Step 3: Update `todo_repository.py`

**Convert all functions to async**. Example for `create_todo`:

```python
async def create_todo(todo_data: TodoCreate) -> Dict[str, Any]:
    """Create a new TODO item (async)."""
    try:
        async with get_async_session() as session:
            stmt = insert(todos_table).values(
                title=todo_data.title,
                description=todo_data.description,
                priority=todo_data.priority,
                due_date=todo_data.due_date,
                completed=False,
            ).returning(todos_table)
            
            result = await session.execute(stmt)
            row = result.fetchone()
            await session.commit()
            
            return _row_to_dict(row)
    except SQLAlchemyError as e:
        logger.error(f"Error creating TODO: {e}")
        raise
```

**Apply same pattern to**:
- `get_todo()` → `async def get_todo()`
- `list_todos()` → `async def list_todos()`
- `update_todo()` → `async def update_todo()`
- `delete_todo()` → `async def delete_todo()`

#### Step 4: Update `app.py` endpoints

**Change from**:
```python
@app.post("/api/todo", response_model=TodoResponse, status_code=201)
async def create_todo_endpoint(todo_data: TodoCreate):
    todo = create_todo(todo_data)  # Sync call
    return todo
```

**To**:
```python
@app.post("/api/todo", response_model=TodoResponse, status_code=201)
async def create_todo_endpoint(todo_data: TodoCreate):
    todo = await create_todo(todo_data)  # Async call
    return todo
```

**Expected Impact**: 10-20x performance improvement (from 2.28 to ~20-45 ops/sec)

**Risk**: Medium - Requires thorough testing

---

## Medium-Term Actions (Next Sprint)

### 4. Add Bulk Operations Endpoint

**Add to `app.py`**:
```python
@app.post("/api/todo/bulk", response_model=List[TodoResponse], status_code=201)
async def create_todos_bulk(todos: List[TodoCreate]):
    """Create multiple TODOs in a single transaction."""
    try:
        created_todos = await create_todos_bulk(todos)
        return created_todos
    except SQLAlchemyError as e:
        logger.error(f"Database error creating bulk TODOs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

**Add to `todo_repository.py`**:
```python
async def create_todos_bulk(todos: List[TodoCreate]) -> List[Dict[str, Any]]:
    """Create multiple TODOs in a single transaction."""
    try:
        async with get_async_session() as session:
            values = [{
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "due_date": t.due_date,
                "completed": False,
            } for t in todos]
            
            stmt = insert(todos_table).values(values).returning(todos_table)
            result = await session.execute(stmt)
            rows = result.fetchall()
            await session.commit()
            
            return [_row_to_dict(row) for row in rows]
    except SQLAlchemyError as e:
        logger.error(f"Error creating bulk TODOs: {e}")
        raise
```

**Expected Impact**: 10-50x improvement for bulk operations

**Risk**: Low - New endpoint, doesn't affect existing code

---

## Performance Testing After Changes

After implementing changes, re-run the test suite:

```bash
python test_todo_api.py http://localhost:8000
```

**Expected Results After Phase 1 (Quick Wins)**:
- Bulk Create (200): 95%+ success rate
- Overall rate: 7-11 ops/sec (3-5x improvement)

**Expected Results After Phase 2 (Async)**:
- Bulk Create (200): 99%+ success rate
- Overall rate: 20-45 ops/sec (10-20x improvement)

**Expected Results After Phase 3 (Full)**:
- Bulk Create (200): 99.9%+ success rate
- Overall rate: 100-450 ops/sec (50-200x improvement)

---

## Monitoring Recommendations

Add connection pool monitoring to track improvements:

**Add to `app.py`**:
```python
@app.get("/api/debug/pool-status")
async def pool_status():
    """Get database connection pool status (for debugging)."""
    try:
        from db_connection import get_async_engine
        engine = get_async_engine()
        pool = engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool._max_overflow,
        }
    except Exception as e:
        return {"error": str(e)}
```

---

## Summary

**Do Immediately**:
1. ✅ Increase connection pool (5 minutes)
2. ✅ Add database indexes (30 minutes)

**Do This Week**:
3. ✅ Convert to async operations (2-4 hours)

**Do Next Sprint**:
4. ✅ Add bulk operations (1-2 hours)

**Total Expected Improvement**: 50-200x (from 2.28 to 100-450 ops/sec)

