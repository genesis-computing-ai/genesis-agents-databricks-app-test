-- Sample SQL Queries for Direct Database Performance Testing
-- Run these queries directly against your PostgreSQL database to test query performance

-- ============================================================================
-- 1. READ Operation (Get single TODO by ID)
-- ============================================================================
-- This matches: GET /api/todo/{todo_id}
-- Expected time: ~550ms

EXPLAIN ANALYZE
SELECT id, title, description, completed, priority, due_date, created_at, updated_at
FROM todos
WHERE id = 1;

-- ============================================================================
-- 2. LIST Operation (Get all TODOs, ordered by created_at DESC)
-- ============================================================================
-- This matches: GET /api/todo
-- Expected time: ~650ms (with 5,828+ records)

EXPLAIN ANALYZE
SELECT id, title, description, completed, priority, due_date, created_at, updated_at
FROM todos
ORDER BY created_at DESC;

-- ============================================================================
-- 3. LIST with Filter (Get incomplete TODOs)
-- ============================================================================
-- This matches: GET /api/todo?completed=false
-- Expected time: ~650ms

EXPLAIN ANALYZE
SELECT id, title, description, completed, priority, due_date, created_at, updated_at
FROM todos
WHERE completed = false
ORDER BY created_at DESC;

-- ============================================================================
-- 4. LIST with Priority Filter
-- ============================================================================
-- This matches: GET /api/todo?priority=1
-- Expected time: ~650ms

EXPLAIN ANALYZE
SELECT id, title, description, completed, priority, due_date, created_at, updated_at
FROM todos
WHERE priority = 1
ORDER BY created_at DESC;

-- ============================================================================
-- 5. CREATE Operation (INSERT)
-- ============================================================================
-- This matches: POST /api/todo
-- Expected time: ~665ms

EXPLAIN ANALYZE
INSERT INTO todos (title, description, priority, completed, due_date)
VALUES ('Test TODO', 'Test description', 2, false, NULL)
RETURNING id, title, description, completed, priority, due_date, created_at, updated_at;

-- ============================================================================
-- 6. UPDATE Operation
-- ============================================================================
-- This matches: PUT /api/todo/{todo_id}
-- Expected time: ~553ms

EXPLAIN ANALYZE
UPDATE todos
SET title = 'Updated title',
    completed = true,
    priority = 0,
    updated_at = NOW()
WHERE id = 1
RETURNING id, title, description, completed, priority, due_date, created_at, updated_at;

-- ============================================================================
-- 7. DELETE Operation
-- ============================================================================
-- This matches: DELETE /api/todo/{todo_id}
-- Expected time: ~555ms

EXPLAIN ANALYZE
DELETE FROM todos
WHERE id = 1;

-- ============================================================================
-- 8. Performance Analysis Queries
-- ============================================================================

-- Check table size
SELECT 
    pg_size_pretty(pg_total_relation_size('todos')) as total_size,
    pg_size_pretty(pg_relation_size('todos')) as table_size,
    pg_size_pretty(pg_indexes_size('todos')) as indexes_size,
    (SELECT COUNT(*) FROM todos) as row_count;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'todos'
ORDER BY idx_scan DESC;

-- Check table statistics
SELECT 
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    seq_tup_read as sequential_tuples_read,
    idx_scan as index_scans,
    idx_tup_fetch as index_tuples_fetched,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE tablename = 'todos';

-- Check for slow queries (if pg_stat_statements is enabled)
-- SELECT 
--     query,
--     calls,
--     total_exec_time,
--     mean_exec_time,
--     max_exec_time
-- FROM pg_stat_statements
-- WHERE query LIKE '%todos%'
-- ORDER BY mean_exec_time DESC
-- LIMIT 10;

-- ============================================================================
-- 9. Test Query Performance with Timing
-- ============================================================================

-- Enable timing
\timing on

-- Test READ
SELECT * FROM todos WHERE id = 1;

-- Test LIST (all)
SELECT * FROM todos ORDER BY created_at DESC LIMIT 100;

-- Test LIST with filter
SELECT * FROM todos WHERE completed = false ORDER BY created_at DESC LIMIT 100;

-- Disable timing
\timing off

-- ============================================================================
-- 10. Connection Pool Status (if accessible)
-- ============================================================================

-- Check active connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE datname = current_database()
  AND state = 'active'
ORDER BY query_start;

-- Check connection pool usage
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections,
    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity
WHERE datname = current_database();

