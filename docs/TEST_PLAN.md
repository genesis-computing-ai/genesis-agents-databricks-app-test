# TODO API Test Plan

## Overview

This test plan focuses on comprehensive testing of the TODO API application, with emphasis on:
- Basic functionality verification
- Multiple clients updating todos in parallel
- Speed and scale testing
- Concurrency testing

## Test Environment

- **Base URL**: http://localhost:8000
- **API Endpoint**: `/api/todo`
- **Database**: PostgreSQL (via SQLAlchemy)
- **Test Framework**: Python asyncio + aiohttp

## Test Cases

### 1. Basic CRUD Operations
**Objective**: Verify fundamental CRUD operations work correctly

**Steps**:
1. Create a TODO
2. Read the created TODO
3. Update the TODO (change completion status and priority)
4. List all TODOs (verify the TODO appears)
5. Delete the TODO
6. Verify deletion (attempt to read deleted TODO)

**Success Criteria**:
- All operations complete without errors
- Data integrity maintained throughout operations

**Expected Duration**: < 1 second

---

### 2. Bulk Create Test (Small Batch)
**Objective**: Test creating many TODOs quickly

**Steps**:
1. Create 50 TODOs concurrently
2. Measure creation rate and time per operation

**Success Criteria**:
- At least 95% of TODOs created successfully
- Creation rate > 10 TODOs/second

**Expected Duration**: < 5 seconds

---

### 3. Bulk Create Test (Large Batch)
**Objective**: Test creating larger batches of TODOs

**Steps**:
1. Create 200 TODOs concurrently
2. Measure creation rate and time per operation

**Success Criteria**:
- At least 95% of TODOs created successfully
- Creation rate > 20 TODOs/second

**Expected Duration**: < 10 seconds

---

### 4. Concurrent Updates
**Objective**: Test multiple clients updating different TODOs simultaneously

**Steps**:
1. Use 10 TODOs from previous tests
2. Launch 10 concurrent clients
3. Each client updates all 10 TODOs
4. Measure update rate and conflicts

**Success Criteria**:
- All updates complete successfully
- No data corruption
- Update rate > 5 updates/second

**Expected Duration**: < 20 seconds

---

### 5. Parallel Reads
**Objective**: Test many concurrent read operations

**Steps**:
1. Use 10 existing TODOs
2. Launch 20 concurrent readers
3. Each reader reads all 10 TODOs
4. Measure read rate

**Success Criteria**:
- All reads complete successfully
- Read rate > 50 reads/second
- No errors or timeouts

**Expected Duration**: < 5 seconds

---

### 6. Mixed Workload
**Objective**: Test concurrent reads and writes

**Steps**:
1. Use 15 existing TODOs
2. Launch 5 writers (updating first 10 TODOs)
3. Launch 15 readers (reading all TODOs)
4. Run concurrently
5. Measure operation rates

**Success Criteria**:
- Both reads and writes complete successfully
- No deadlocks or timeouts
- Combined rate > 30 ops/second

**Expected Duration**: < 10 seconds

---

### 7. Race Condition Test
**Objective**: Test concurrent updates to the same TODO

**Steps**:
1. Select one TODO
2. Launch 20 concurrent updaters
3. Each updater modifies the same TODO
4. Verify final state consistency

**Success Criteria**:
- Updates complete (race conditions are expected)
- Final state is consistent
- No errors or crashes

**Expected Duration**: < 5 seconds

---

### 8. Scale Limits Test
**Objective**: Determine maximum throughput and scale

**Steps**:
1. Create batches of increasing size: 500, 1000, 1500, 2000
2. Measure creation rate for each batch
3. Identify where performance degrades

**Success Criteria**:
- At least 90% success rate for each batch
- Identify maximum sustainable rate
- Document performance characteristics

**Expected Duration**: Variable (depends on system)

---

## Performance Metrics

### Key Metrics to Track:
1. **Operations per second**: Rate of successful operations
2. **Latency**: Average time per operation
3. **Error rate**: Percentage of failed operations
4. **Concurrency**: Number of simultaneous operations
5. **Throughput**: Total operations completed

### Expected Performance Targets:
- **Create**: > 20 TODOs/second
- **Read**: > 50 TODOs/second
- **Update**: > 10 TODOs/second
- **Delete**: > 10 TODOs/second
- **Concurrent clients**: Support 20+ simultaneous clients

---

## Concurrency Scenarios

### Scenario 1: Multiple Writers, Same TODO
- **Test**: 20 clients updating the same TODO
- **Expected**: Last write wins, no data corruption
- **Risk**: Race conditions (acceptable)

### Scenario 2: Multiple Writers, Different TODOs
- **Test**: 10 clients updating 10 different TODOs
- **Expected**: All updates succeed independently
- **Risk**: Low

### Scenario 3: Readers During Writes
- **Test**: 15 readers + 5 writers on same TODOs
- **Expected**: Readers see consistent state
- **Risk**: Stale reads (acceptable)

### Scenario 4: High Concurrency Mixed
- **Test**: 50 concurrent operations (mix of CRUD)
- **Expected**: All operations complete
- **Risk**: Database connection limits

---

## Test Execution

### Prerequisites:
1. Server running on http://localhost:8000
2. Database initialized and accessible
3. Python 3.8+ with asyncio support
4. Required packages: `aiohttp`

### Running Tests:
```bash
# Install dependencies
pip install aiohttp

# Run tests
python test_todo_api.py [base_url]

# Example with custom URL
python test_todo_api.py http://localhost:8000
```

### Expected Output:
- Test-by-test progress
- Success/failure status for each test
- Performance metrics
- Summary statistics

---

## Success Criteria

### Overall Test Suite Success:
- ✅ All basic CRUD tests pass
- ✅ Bulk operations achieve > 90% success rate
- ✅ Concurrent operations complete without errors
- ✅ No data corruption detected
- ✅ Performance meets or exceeds targets

### Failure Conditions:
- ❌ Basic CRUD operations fail
- ❌ > 10% error rate on bulk operations
- ❌ Deadlocks or timeouts in concurrent tests
- ❌ Data corruption or inconsistency
- ❌ Performance significantly below targets

---

## Notes

- Tests create TODOs that may remain in the database (cleanup optional)
- Race conditions in concurrent updates are expected and acceptable
- Performance metrics are environment-dependent
- Database connection pooling affects concurrent test results
- Network latency may impact local vs remote testing

