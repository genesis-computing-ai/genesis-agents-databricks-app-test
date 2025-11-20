-- Quick Test Queries - Copy and paste these into your PostgreSQL client

-- 1. Simple READ (fastest)
SELECT * FROM todos WHERE id = 1;

-- 2. LIST all (slower with many records)
SELECT * FROM todos ORDER BY created_at DESC LIMIT 10;

-- 3. LIST with filter
SELECT * FROM todos WHERE completed = false ORDER BY created_at DESC LIMIT 10;

-- 4. LIST with priority filter
SELECT * FROM todos WHERE priority = 1 ORDER BY created_at DESC LIMIT 10;

-- 5. Count records
SELECT COUNT(*) FROM todos;

-- 6. Check indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'todos';

