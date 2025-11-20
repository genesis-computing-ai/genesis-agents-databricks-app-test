# SQLite Support Analysis

## Executive Summary

This document analyzes what would be required to make the application work with SQLite in addition to PostgreSQL. The application currently uses PostgreSQL-specific features in several areas, requiring modifications to support SQLite as an alternative database backend.

**Overall Assessment**: **MODERATE COMPLEXITY** - Requires changes across multiple layers but is feasible with careful implementation.

---

## 1. Database Connection & Driver Changes

### Current Implementation

**Files Affected:**
- `utils/database_config.py` - Hardcoded PostgreSQL URL format
- `utils/db_connection.py` - Uses `postgresql+asyncpg://` driver
- `utils/db_migrations.py` - Uses sync PostgreSQL driver (`psycopg2`)

**Current Code:**
```python
# database_config.py line 102
return f"postgresql://{user}:{password}@{host}:{port}/{database}"

# db_connection.py line 27
async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
```

### Required Changes

1. **Add database type detection** in `database_config.py`:
   - Detect SQLite vs PostgreSQL based on connection string or config flag
   - SQLite URLs: `sqlite:///path/to/database.db` or `sqlite+aiosqlite:///path/to/database.db`
   - PostgreSQL URLs: `postgresql://...` (current format)

2. **Update `get_database_url()`** to support both formats:
   ```python
   def get_database_url() -> str:
       db_config = get_database_config()
       db_type = db_config.get("type", "postgresql")  # or detect from config
       
       if db_type == "sqlite":
           # SQLite uses file path, not host/port/user/password
           db_path = db_config.get("database", ":memory:")
           return f"sqlite:///{db_path}"
       else:
           # PostgreSQL format (existing code)
           return f"postgresql://{user}:{password}@{host}:{port}/{database}"
   ```

3. **Update `db_connection.py`** to handle both drivers:
   ```python
   async_database_url = database_url
   if database_url.startswith("postgresql://"):
       async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
   elif database_url.startswith("sqlite:///"):
       async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
   ```

4. **Update `db_migrations.py`** sync engine for SQLite:
   - SQLite uses `sqlite:///` (no separate async driver needed for sync operations)
   - No changes needed for sync engine creation (SQLAlchemy handles it)

**Dependencies to Add:**
- `aiosqlite>=0.19.0` - Async SQLite driver (add to `requirements.txt`)

### Why `aiosqlite` Instead of `sqlite3`?

**Question:** Can we use the standard library `sqlite3` instead of `aiosqlite`?

**Answer:** **No, for application code. Yes, for migrations.**

**Why `aiosqlite` is Required for Application Code:**

1. **The application is fully async:**
   - All FastAPI endpoints use `async def`
   - All repository functions (`todo_repository.py`) use `async def` and `await`
   - Database sessions use `async with get_async_session()` and `await session.execute()`

2. **SQLAlchemy's async engine requires an async driver:**
   - `create_async_engine()` from `sqlalchemy.ext.asyncio` needs an async-compatible driver
   - The standard `sqlite3` module is **synchronous** and would block the event loop
   - Using `sqlite3` with async code would cause blocking, defeating the purpose of async

3. **What `aiosqlite` does:**
   - Wraps `sqlite3` and runs operations in a background thread
   - Provides async/await interface compatible with `asyncio`
   - Allows non-blocking database operations

**When `sqlite3` CAN Be Used:**

- **Migrations (Alembic):** Already use a **synchronous** engine (`get_sync_engine()` in `db_migrations.py`)
- For migrations, `sqlite3` works fine because migrations run synchronously
- No changes needed for migration code - it already uses sync SQLAlchemy engine

**Alternative Approaches (Not Recommended):**

1. **Use sync SQLite with thread pool executor:**
   - SQLAlchemy CAN use sync drivers with async engines via `create_async_engine(..., poolclass=NullPool)`
   - But this runs sync operations in a thread pool, adding overhead
   - Defeats the performance benefits of async

2. **Rewrite everything to sync:**
   - Would require changing all `async def` to `def` and removing `await`
   - Would lose async benefits (concurrent request handling)
   - Massive code changes required

**Conclusion:**
- **Application code:** Must use `aiosqlite` (async driver)
- **Migrations:** Can use `sqlite3` (already sync, no change needed)
- **Best practice:** Use `aiosqlite` for consistency and proper async support

---

## 2. Schema & Data Type Differences

### Critical Differences

#### 2.1 JSON Column Type

**Current Implementation:**
- `db_schema.py` line 30: Uses `JSON` type (SQLAlchemy generic)
- Migration `add_payload_column_to_todos.py` line 23: Uses `postgresql.JSON()`

**PostgreSQL:**
- Native JSON/JSONB type with rich query operators
- Supports JSON indexing and queries

**SQLite:**
- No native JSON type (until SQLite 3.38.0+)
- Uses TEXT with JSON validation
- JSON functions available but less efficient

**Required Changes:**

1. **Update `db_schema.py`** to use dialect-aware JSON:
   ```python
   from sqlalchemy import JSON
   from sqlalchemy.dialects import postgresql, sqlite
   
   # In table definition, use conditional type
   Column("payload", JSON, nullable=True)  # SQLAlchemy handles dialect differences
   ```

2. **Update migration `add_payload_column_to_todos.py`**:
   ```python
   from alembic import op
   import sqlalchemy as sa
   from sqlalchemy.dialects import postgresql
   
   def upgrade() -> None:
       # Detect database dialect
       bind = op.get_bind()
       if bind.dialect.name == 'postgresql':
           op.add_column('todos', sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=True))
       else:  # SQLite
           op.add_column('todos', sa.Column('payload', sa.JSON(), nullable=True))
   ```

**Note:** SQLAlchemy's `JSON` type automatically maps to:
- PostgreSQL: `JSON` or `JSONB`
- SQLite: `TEXT` (with JSON validation)

#### 2.2 DateTime with Timezone

**Current Implementation:**
- `db_schema.py` lines 29, 31-32: `DateTime(timezone=True)`
- Uses `func.now()` for server defaults

**PostgreSQL:**
- Native `TIMESTAMP WITH TIME ZONE`
- `now()` returns timezone-aware timestamp

**SQLite:**
- No timezone support in datetime storage
- Stores as TEXT (ISO8601) or REAL (Julian day)
- `datetime('now')` returns UTC string

**Required Changes:**

1. **Update `db_schema.py`**:
   ```python
   # SQLAlchemy handles timezone differences automatically
   # But we should ensure consistent behavior
   Column("due_date", DateTime(timezone=True), nullable=True)  # Works for both
   Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
   ```

2. **Application code** (`todo_repository.py` line 236):
   - Already uses `datetime.now(timezone.utc)` - ✅ Good
   - SQLAlchemy will handle conversion

**Impact:** Minimal - SQLAlchemy abstracts timezone handling, but SQLite will store as TEXT

#### 2.3 Boolean Type

**Current Implementation:**
- `db_schema.py` line 27: `Boolean, default=False`

**PostgreSQL:**
- Native `BOOLEAN` type

**SQLite:**
- No native boolean (uses INTEGER: 0/1)
- SQLAlchemy handles conversion automatically

**Required Changes:** None - SQLAlchemy handles this automatically

#### 2.4 String Length Limits

**Current Implementation:**
- `db_schema.py` line 25: `String(255)`

**PostgreSQL:**
- Enforces VARCHAR(255) limit

**SQLite:**
- No length limit enforcement (VARCHAR is same as TEXT)
- Application-level validation still applies

**Required Changes:** None - Works as-is, but SQLite won't enforce length at DB level

---

## 3. SQL Dialect Differences

### 3.1 Index Creation

**Current Implementation:**
- `add_todo_indexes.py` line 71: Uses PostgreSQL `CREATE INDEX IF NOT EXISTS`

**PostgreSQL:**
- Supports `IF NOT EXISTS` clause

**SQLite:**
- Supports `IF NOT EXISTS` (since SQLite 3.3.0)

**Required Changes:** None - Already compatible ✅

### 3.2 Server Defaults

**Current Implementation:**
- `db_schema.py` lines 31-32: `server_default=func.now()`

**PostgreSQL:**
- `now()` function available

**SQLite:**
- Uses `datetime('now')` or `CURRENT_TIMESTAMP`

**Required Changes:**

1. **Update `db_schema.py`** to use dialect-aware defaults:
   ```python
   from sqlalchemy import text
   
   # Use SQLAlchemy's func for cross-dialect compatibility
   Column("created_at", DateTime(timezone=True), 
          server_default=func.now(), nullable=False)  # SQLAlchemy translates
   ```

   **OR** use raw SQL with dialect detection:
   ```python
   from sqlalchemy import event
   from sqlalchemy.engine import Engine
   
   @event.listens_for(Engine, "connect")
   def set_sqlite_pragma(dbapi_conn, connection_record):
       if dbapi_conn.dialect.name == 'sqlite':
           # Enable foreign keys, etc.
           pass
   ```

**Impact:** SQLAlchemy's `func.now()` should work, but may need testing

### 3.3 RETURNING Clause

**Current Implementation:**
- `todo_repository.py` lines 66, 249: Uses `.returning(todos_table)`

**PostgreSQL:**
- Supports `RETURNING` clause in INSERT/UPDATE

**SQLite:**
- Supports `RETURNING` clause (since SQLite 3.35.0)

**Required Changes:** None if using SQLite 3.35.0+ ✅

**Fallback for older SQLite:**
- Would need to execute separate SELECT after INSERT/UPDATE
- Add version check or feature detection

---

## 4. Connection Pooling & Configuration

### Current Implementation

**PostgreSQL:**
- `db_connection.py` lines 31-40: Connection pool with `pool_size=50`, `max_overflow=20`
- Uses `pool_pre_ping=True` for connection health checks
- `pool_recycle=3600` for connection recycling

**SQLite:**
- Different pooling behavior:
  - SQLite connections are file-based, not network-based
  - Pooling still useful for concurrent access
  - No network latency, but file locking considerations

**Required Changes:**

1. **Update `db_connection.py`** to adjust pool settings for SQLite:
   ```python
   def get_async_engine() -> AsyncEngine:
       database_url = get_database_url()
       
       # Configure pool based on database type
       if database_url.startswith("sqlite"):
           # SQLite-specific settings
           pool_kwargs = {
               "pool_size": 1,  # SQLite doesn't benefit from large pools
               "max_overflow": 0,  # No overflow needed
               "pool_pre_ping": False,  # Not needed for file-based
               "connect_args": {
                   "check_same_thread": False,  # Required for async SQLite
                   "timeout": 20.0,  # Lock timeout
               }
           }
       else:
           # PostgreSQL settings (existing)
           pool_kwargs = {
               "pool_size": 50,
               "max_overflow": 20,
               "pool_pre_ping": True,
               "pool_recycle": 3600,
               "connect_args": {
                   "command_timeout": 30,
               }
           }
       
       async_database_url = convert_to_async_url(database_url)
       _async_engine = create_async_engine(async_database_url, **pool_kwargs)
   ```

2. **SQLite-specific considerations:**
   - Enable WAL mode for better concurrency: `PRAGMA journal_mode=WAL`
   - Set busy timeout: `PRAGMA busy_timeout=20000`
   - Consider foreign key constraints: `PRAGMA foreign_keys=ON`

---

## 5. Migration System (Alembic)

### Current Implementation

- `alembic/env.py` - Uses sync engine for migrations
- Migrations use PostgreSQL-specific features

**Required Changes:**

1. **Update `alembic/env.py`** to detect dialect:
   ```python
   def run_migrations_online() -> None:
       connectable = get_sync_engine()
       
       with connectable.connect() as connection:
           # Set SQLite pragmas if needed
           if connection.dialect.name == 'sqlite':
               connection.execute(text("PRAGMA foreign_keys=ON"))
               connection.execute(text("PRAGMA journal_mode=WAL"))
           
           context.configure(
               connection=connection, 
               target_metadata=target_metadata,
               render_as_batch=True  # For SQLite ALTER TABLE compatibility
           )
           
           with context.begin_transaction():
               context.run_migrations()
   ```

2. **Update migrations** to be dialect-aware:
   - `add_payload_column_to_todos.py` - Already identified above
   - `add_todo_indexes.py` - Already uses `IF NOT EXISTS` ✅
   - `b2be44556bf2_initial_todos_table.py` - May need `render_as_batch=True` for SQLite

3. **SQLite ALTER TABLE limitations:**
   - SQLite has limited ALTER TABLE support
   - Adding columns works, but renaming/dropping columns requires table recreation
   - Alembic's `render_as_batch=True` handles this automatically

---

## 6. Configuration Changes

### app.yaml Updates

**Current:**
```yaml
database_databricks:
  host: "..."
  port: 5432
  database: "..."
  user: "..."
  password: "..."
```

**Required:**
```yaml
# Option 1: Add SQLite config
database_sqlite:
  type: sqlite
  database: "/path/to/todos.db"  # File path

# Option 2: Detect from database path
database_local:
  type: sqlite  # or "postgresql"
  database: "./todos.db"  # SQLite file path
  # OR for PostgreSQL:
  # host: "localhost"
  # port: 5432
  # database: "todos"
  # user: "user"
  # password: "pass"
```

**Update `database_config.py`:**
- Add `type` field detection
- Handle SQLite file path vs PostgreSQL connection params
- Update validation logic

---

## 7. Testing & Compatibility

### Areas Requiring Testing

1. **JSON Operations:**
   - Create TODO with payload
   - Update TODO payload
   - Query filtering by JSON fields (if implemented)

2. **DateTime Operations:**
   - Timezone handling
   - Server defaults (`created_at`, `updated_at`)
   - Manual timestamp updates

3. **Concurrency:**
   - Multiple concurrent writes (SQLite file locking)
   - Connection pool behavior

4. **Migrations:**
   - Fresh database initialization
   - Migration upgrades
   - Migration rollbacks

5. **Performance:**
   - SQLite is single-file, no network overhead
   - But file locking can be a bottleneck
   - WAL mode improves concurrency

---

## 8. Code Changes Summary

### Files Requiring Modifications

1. **`utils/database_config.py`**
   - Add database type detection
   - Support SQLite file path configuration
   - Update URL generation logic

2. **`utils/db_connection.py`**
   - Add SQLite async driver support (`sqlite+aiosqlite://`)
   - Adjust connection pool settings based on database type
   - Add SQLite-specific connection arguments (WAL mode, etc.)

3. **`utils/db_migrations.py`**
   - Add SQLite pragma setup
   - Ensure dialect-aware migration execution

4. **`db_schema.py`**
   - Verify JSON type compatibility (should work as-is)
   - Verify DateTime timezone handling

5. **`alembic/env.py`**
   - Add SQLite pragma setup
   - Enable `render_as_batch=True` for SQLite

6. **`alembic/versions/add_payload_column_to_todos.py`**
   - Make JSON column creation dialect-aware

7. **`alembic/versions/b2be44556bf2_initial_todos_table.py`**
   - Verify compatibility (likely works as-is)

8. **`app.yaml`**
   - Add SQLite configuration example
   - Document database type selection

9. **`requirements.txt`**
   - Add `aiosqlite>=0.19.0`

### Files That Should Work As-Is

- `todo_repository.py` - Uses SQLAlchemy Core, should be dialect-agnostic
- `todo_models.py` - Pydantic models, database-agnostic
- `app.py` - Application logic, database-agnostic

---

## 9. Implementation Strategy

### Phase 1: Foundation
1. Add database type detection to `database_config.py`
2. Update `db_connection.py` to support SQLite async driver
3. Add `aiosqlite` dependency
4. Test basic connection

### Phase 2: Schema Compatibility
1. Update migrations to be dialect-aware
2. Test migration execution on SQLite
3. Verify JSON and DateTime handling

### Phase 3: Configuration
1. Update `app.yaml` with SQLite config example
2. Add environment variable for database type selection
3. Document configuration options

### Phase 4: Testing
1. Run full test suite against SQLite
2. Test concurrency scenarios
3. Performance comparison (SQLite vs PostgreSQL)

### Phase 5: Documentation
1. Update README with SQLite setup instructions
2. Document limitations and differences
3. Add troubleshooting guide

---

## 10. Known Limitations & Considerations

### SQLite Limitations

1. **Concurrency:**
   - Single writer at a time (WAL mode helps)
   - Not suitable for high-write concurrency
   - Better for read-heavy workloads

2. **No Network Access:**
   - File-based, must be accessible from application
   - Not suitable for distributed deployments
   - Good for local development and single-instance deployments

3. **Limited ALTER TABLE:**
   - Some schema changes require table recreation
   - Alembic handles this with `render_as_batch=True`

4. **No Advanced Features:**
   - No full-text search (without extensions)
   - No advanced JSON querying
   - No array types
   - No custom functions

5. **File Management:**
   - Database file must be managed (backups, permissions)
   - File size can grow (no automatic cleanup)

### When to Use SQLite vs PostgreSQL

**Use SQLite when:**
- Local development
- Single-instance deployment
- Low to moderate write concurrency
- Simple data model
- File-based storage is acceptable

**Use PostgreSQL when:**
- Production multi-instance deployment
- High write concurrency required
- Need advanced features (JSON queries, full-text search, etc.)
- Network-accessible database required
- Complex queries and performance optimization needed

---

## 11. Estimated Effort

**Total Estimated Time:** 8-12 hours

**Breakdown:**
- Database connection & driver changes: 2-3 hours
- Schema & migration updates: 2-3 hours
- Configuration updates: 1 hour
- Testing & debugging: 2-3 hours
- Documentation: 1-2 hours

**Complexity:** Moderate
- Most changes are straightforward
- SQLAlchemy provides good abstraction
- Main challenges: JSON handling, migration compatibility, testing

---

## 12. Recommendations

1. **Start with SQLite for local development:**
   - Easier setup (no database server needed)
   - Faster iteration
   - Good for testing

2. **Use PostgreSQL for production:**
   - Better concurrency
   - More features
   - Better for distributed systems

3. **Make database selection configurable:**
   - Environment variable or config file
   - Easy switching between backends
   - Same codebase, different databases

4. **Test both backends:**
   - CI/CD should test against both
   - Ensure compatibility
   - Catch dialect-specific issues early

5. **Document differences:**
   - Clear documentation of limitations
   - When to use which database
   - Migration considerations

---

## Conclusion

Adding SQLite support is **feasible and moderately complex**. The main challenges are:

1. **JSON column handling** - Requires dialect-aware migrations
2. **Connection pooling** - Different settings for SQLite
3. **Migration compatibility** - Need to handle SQLite's ALTER TABLE limitations
4. **Configuration** - Support both file-based and connection-string configs

However, SQLAlchemy provides good abstraction, and most application code should work without changes. The main work is in:
- Connection/driver setup
- Migration compatibility
- Configuration management

The effort is justified for local development convenience, but SQLite should not replace PostgreSQL for production use cases requiring high concurrency or advanced features.

