#!/usr/bin/env python3
"""
Comprehensive test suite for TODO API focusing on:
- Basic functionality
- Multiple clients updating todos in parallel
- Speed and scale testing
- Concurrency testing
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass, field
from collections import defaultdict
import random
import string


@dataclass
class TestResult:
    """Store test execution results."""
    test_name: str
    success: bool
    duration: float
    operations: int = 0
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class TodoAPITester:
    """Test suite for TODO API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", cookie: Optional[str] = None):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/todo"
        self.cookie = cookie
        self.results: List[TestResult] = []
        self.created_todo_ids: List[int] = []
        self.lock = threading.Lock()
    
    def get_headers(self) -> Dict[str, str]:
        """Get default headers including cookie if provided."""
        headers = {
            'accept': '*/*',
            'content-type': 'application/json',
        }
        if self.cookie:
            headers['cookie'] = self.cookie
        return headers
    
    def generate_large_payload(self, min_size_kb: int = 3) -> Dict[str, Any]:
        """
        Generate a sizable JSON payload (at least a few pages long).
        Target size: at least min_size_kb KB of JSON data.
        """
        # Generate a payload with nested structures, arrays, and text content
        # to ensure it's at least a few pages long (roughly 2-4KB)
        payload = {
            "metadata": {
                "version": "1.0",
                "created_by": "performance_test",
                "timestamp": datetime.now().isoformat(),
                "test_id": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
            },
            "content": {
                "sections": []
            },
            "attachments": [],
            "tags": [],
            "notes": []
        }
        
        # Add multiple sections with substantial text content
        # Each section will have ~500-800 bytes of text
        for i in range(10):
            section_text = ''.join(random.choices(
                string.ascii_letters + string.digits + ' \n',
                k=random.randint(500, 800)
            ))
            payload["content"]["sections"].append({
                "id": i,
                "title": f"Section {i}",
                "content": section_text,
                "metadata": {
                    "order": i,
                    "type": random.choice(["text", "code", "markdown", "html"]),
                    "formatting": {
                        "bold": random.choice([True, False]),
                        "italic": random.choice([True, False]),
                        "color": random.choice(["black", "blue", "red", "green"]),
                    }
                }
            })
        
        # Add attachments metadata
        for i in range(5):
            payload["attachments"].append({
                "id": i,
                "filename": f"attachment_{i}.pdf",
                "size": random.randint(100000, 5000000),
                "mime_type": random.choice(["application/pdf", "image/png", "image/jpeg", "text/plain"]),
                "url": f"https://example.com/files/attachment_{i}",
                "uploaded_at": datetime.now().isoformat(),
            })
        
        # Add tags
        for i in range(15):
            payload["tags"].append({
                "name": f"tag_{i}",
                "color": f"#{''.join(random.choices('0123456789ABCDEF', k=6))}",
                "category": random.choice(["priority", "status", "project", "custom"]),
            })
        
        # Add notes with substantial content
        for i in range(8):
            note_text = ''.join(random.choices(
                string.ascii_letters + string.digits + ' \n\t',
                k=random.randint(300, 600)
            ))
            payload["notes"].append({
                "id": i,
                "content": note_text,
                "author": f"user_{i % 5}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            })
        
        # Add additional nested data
        payload["analytics"] = {
            "views": random.randint(0, 10000),
            "edits": random.randint(0, 5000),
            "shares": random.randint(0, 1000),
            "events": [
                {
                    "type": random.choice(["view", "edit", "share", "comment"]),
                    "timestamp": datetime.now().isoformat(),
                    "user": f"user_{random.randint(0, 10)}",
                }
                for _ in range(20)
            ]
        }
        
        # Verify the payload is at least the minimum size
        payload_json = json.dumps(payload)
        payload_size_kb = len(payload_json.encode('utf-8')) / 1024
        
        # If payload is too small, add more content
        if payload_size_kb < min_size_kb:
            additional_text = ''.join(random.choices(
                string.ascii_letters + string.digits + ' \n',
                k=int((min_size_kb - payload_size_kb) * 1024)
            ))
            payload["additional_content"] = additional_text
        
        return payload
        
    def log_result(self, result: TestResult):
        """Log test result."""
        self.results.append(result)
        status = "✓ PASS" if result.success else "✗ FAIL"
        print(f"{status} {result.test_name} ({result.duration:.2f}s)")
        if result.errors:
            for error in result.errors:
                print(f"  Error: {error}")
        if result.details:
            for key, value in result.details.items():
                print(f"  {key}: {value}")
    
    async def create_todo(self, session: aiohttp.ClientSession, 
                         title: str, description: str = None, 
                         priority: int = 2, payload: Optional[Dict] = None) -> Optional[Dict]:
        """Create a TODO via API."""
        try:
            data = {
                "title": title,
                "priority": priority
            }
            if description:
                data["description"] = description
            if payload is not None:
                data["payload"] = payload
                
            async with session.post(self.api_base, json=data, headers=self.get_headers()) as resp:
                if resp.status == 201:
                    todo = await resp.json()
                    with self.lock:
                        self.created_todo_ids.append(todo["id"])
                    return todo
                else:
                    error = await resp.text()
                    return None
        except Exception as e:
            return None
    
    async def get_todo(self, session: aiohttp.ClientSession, todo_id: int) -> Optional[Dict]:
        """Get a TODO by ID."""
        try:
            async with session.get(f"{self.api_base}/{todo_id}", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            return None
    
    async def update_todo(self, session: aiohttp.ClientSession, 
                         todo_id: int, **kwargs) -> Optional[Dict]:
        """Update a TODO."""
        try:
            async with session.put(f"{self.api_base}/{todo_id}", json=kwargs, headers=self.get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            return None
    
    async def list_todos(self, session: aiohttp.ClientSession, 
                       completed: bool = None, priority: int = None) -> List[Dict]:
        """List TODOs with optional filters."""
        try:
            params = {}
            if completed is not None:
                params["completed"] = str(completed).lower()
            if priority is not None:
                params["priority"] = str(priority)
                
            async with session.get(self.api_base, params=params, headers=self.get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            return []
    
    async def delete_todo(self, session: aiohttp.ClientSession, todo_id: int) -> bool:
        """Delete a TODO."""
        try:
            async with session.delete(f"{self.api_base}/{todo_id}", headers=self.get_headers()) as resp:
                return resp.status == 204
        except Exception as e:
            return False
    
    # ========================================================================
    # Test Cases
    # ========================================================================
    
    async def test_basic_crud(self) -> TestResult:
        """Test basic CRUD operations."""
        start_time = time.time()
        errors = []
        details = {}
        
        async with aiohttp.ClientSession() as session:
            # Create with payload
            payload = self.generate_large_payload(min_size_kb=3)
            todo = await self.create_todo(
                session, 
                "Test TODO", 
                "Basic CRUD test",
                priority=1,
                payload=payload
            )
            if not todo:
                errors.append("Failed to create TODO")
                return TestResult("Basic CRUD", False, time.time() - start_time, errors=errors)
            
            todo_id = todo["id"]
            details["created_id"] = todo_id
            
            # Verify payload was saved
            if not todo.get("payload"):
                errors.append("Payload not returned in created TODO")
            else:
                payload_size_kb = len(json.dumps(todo["payload"]).encode('utf-8')) / 1024
                details["payload_size_kb"] = f"{payload_size_kb:.2f}"
            
            # Read
            fetched = await self.get_todo(session, todo_id)
            if not fetched or fetched["id"] != todo_id:
                errors.append("Failed to fetch created TODO")
            elif not fetched.get("payload"):
                errors.append("Payload missing in fetched TODO")
            
            # Update with new payload
            updated_payload = self.generate_large_payload(min_size_kb=4)
            updated = await self.update_todo(
                session, 
                todo_id, 
                completed=True,
                priority=0,
                payload=updated_payload
            )
            if not updated or not updated["completed"] or updated["priority"] != 0:
                errors.append("Failed to update TODO")
            elif not updated.get("payload"):
                errors.append("Payload missing in updated TODO")
            
            # List (with filter to avoid fetching all TODOs - just verify our TODO exists)
            todos = await self.list_todos(session, priority=0)  # Filter by priority we just set
            if not todos or not any(t["id"] == todo_id for t in todos):
                errors.append("Failed to list TODOs")
            
            # Delete
            deleted = await self.delete_todo(session, todo_id)
            if not deleted:
                errors.append("Failed to delete TODO")
            
            # Verify deletion
            fetched_after = await self.get_todo(session, todo_id)
            if fetched_after:
                errors.append("TODO still exists after deletion")
        
        duration = time.time() - start_time
        success = len(errors) == 0
        details["operations"] = 5
        
        return TestResult("Basic CRUD", success, duration, errors=errors, details=details)
    
    async def test_bulk_create(self, count: int = 100) -> TestResult:
        """Test creating many TODOs quickly."""
        start_time = time.time()
        errors = []
        created_count = 0
        total_payload_size_kb = 0
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(count):
                # Generate a sizable payload for each TODO
                payload = self.generate_large_payload(min_size_kb=3)
                payload_size = len(json.dumps(payload).encode('utf-8')) / 1024
                total_payload_size_kb += payload_size
                
                tasks.append(
                    self.create_todo(
                        session,
                        f"Bulk TODO {i}",
                        f"Created in bulk test - {i}",
                        priority=i % 5,
                        payload=payload
                    )
                )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            created_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
            
            # Verify payloads were saved
            payload_verified = 0
            for r in results:
                if r is not None and not isinstance(r, Exception) and r.get("payload"):
                    payload_verified += 1
            
            if created_count < count * 0.95:  # Allow 5% failure rate
                errors.append(f"Only created {created_count}/{count} TODOs")
            
            if payload_verified < created_count * 0.95:
                errors.append(f"Only {payload_verified}/{created_count} TODOs have payloads")
        
        duration = time.time() - start_time
        rate = created_count / duration if duration > 0 else 0
        
        details = {
            "created": created_count,
            "requested": count,
            "rate_per_sec": f"{rate:.2f}",
            "avg_time_per_create": f"{duration/count*1000:.2f}ms" if count > 0 else "N/A",
            "total_payload_size_mb": f"{total_payload_size_kb/1024:.2f}",
            "avg_payload_size_kb": f"{total_payload_size_kb/count:.2f}" if count > 0 else "N/A"
        }
        
        return TestResult(
            f"Bulk Create ({count} TODOs)",
            len(errors) == 0,
            duration,
            operations=created_count,
            errors=errors,
            details=details
        )
    
    async def test_concurrent_updates(self, todo_ids: List[int], 
                                     clients: int = 10) -> TestResult:
        """Test multiple clients updating the same TODOs concurrently."""
        start_time = time.time()
        errors = []
        update_count = 0
        conflict_count = 0
        
        async def update_worker(session: aiohttp.ClientSession, worker_id: int):
            """Worker that updates TODOs."""
            local_updates = 0
            local_conflicts = 0
            
            for todo_id in todo_ids:
                # Each worker tries to update with its own data and payload
                payload = self.generate_large_payload(min_size_kb=3)
                result = await self.update_todo(
                    session,
                    todo_id,
                    title=f"Updated by worker {worker_id}",
                    priority=worker_id % 5,
                    payload=payload
                )
                if result:
                    local_updates += 1
                else:
                    local_conflicts += 1
            
            return local_updates, local_conflicts
        
        async with aiohttp.ClientSession() as session:
            # Create workers
            tasks = []
            for i in range(clients):
                tasks.append(update_worker(session, i))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(f"Worker exception: {result}")
                else:
                    updates, conflicts = result
                    update_count += updates
                    conflict_count += conflicts
        
        duration = time.time() - start_time
        
        details = {
            "clients": clients,
            "todos_per_client": len(todo_ids),
            "total_updates": update_count,
            "conflicts": conflict_count,
            "updates_per_sec": f"{update_count/duration:.2f}" if duration > 0 else "N/A"
        }
        
        # Success if at least some updates succeeded
        success = update_count > 0 and len(errors) == 0
        
        return TestResult(
            f"Concurrent Updates ({clients} clients)",
            success,
            duration,
            operations=update_count,
            errors=errors,
            details=details
        )
    
    async def test_parallel_reads(self, todo_ids: List[int], 
                                  readers: int = 20) -> TestResult:
        """Test many concurrent read operations."""
        start_time = time.time()
        errors = []
        read_count = 0
        
        async def read_worker(session: aiohttp.ClientSession):
            """Worker that reads TODOs."""
            local_reads = 0
            for todo_id in todo_ids:
                result = await self.get_todo(session, todo_id)
                if result:
                    local_reads += 1
            return local_reads
        
        async with aiohttp.ClientSession() as session:
            tasks = [read_worker(session) for _ in range(readers)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(f"Reader exception: {result}")
                else:
                    read_count += result
        
        duration = time.time() - start_time
        
        details = {
            "readers": readers,
            "todos_per_reader": len(todo_ids),
            "total_reads": read_count,
            "reads_per_sec": f"{read_count/duration:.2f}" if duration > 0 else "N/A"
        }
        
        return TestResult(
            f"Parallel Reads ({readers} readers)",
            len(errors) == 0,
            duration,
            operations=read_count,
            errors=errors,
            details=details
        )
    
    async def test_mixed_workload(self, todo_ids: List[int],
                                 writers: int = 5, readers: int = 15) -> TestResult:
        """Test mixed read/write workload."""
        start_time = time.time()
        errors = []
        stats = defaultdict(int)
        
        async def writer_worker(session: aiohttp.ClientSession, worker_id: int):
            """Worker that writes."""
            for todo_id in todo_ids[:10]:  # Update first 10 TODOs
                payload = self.generate_large_payload(min_size_kb=3)
                result = await self.update_todo(
                    session,
                    todo_id,
                    title=f"Mixed workload update {worker_id}",
                    completed=worker_id % 2 == 0,
                    payload=payload
                )
                if result:
                    stats["writes"] += 1
        
        async def reader_worker(session: aiohttp.ClientSession):
            """Worker that reads."""
            for todo_id in todo_ids:
                result = await self.get_todo(session, todo_id)
                if result:
                    stats["reads"] += 1
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            # Add writers
            for i in range(writers):
                tasks.append(writer_worker(session, i))
            # Add readers
            for _ in range(readers):
                tasks.append(reader_worker(session))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(f"Worker exception: {result}")
        
        duration = time.time() - start_time
        
        details = {
            "writers": writers,
            "readers": readers,
            "writes": stats["writes"],
            "reads": stats["reads"],
            "total_ops": stats["writes"] + stats["reads"],
            "ops_per_sec": f"{(stats['writes'] + stats['reads'])/duration:.2f}" if duration > 0 else "N/A"
        }
        
        return TestResult(
            f"Mixed Workload ({writers}W/{readers}R)",
            len(errors) == 0,
            duration,
            operations=stats["writes"] + stats["reads"],
            errors=errors,
            details=details
        )
    
    async def test_race_condition(self, todo_id: int, 
                                 updaters: int = 20) -> TestResult:
        """Test race condition by having many clients update the same TODO."""
        start_time = time.time()
        errors = []
        update_count = 0
        final_states = []
        
        async def updater_worker(session: aiohttp.ClientSession, worker_id: int):
            """Worker that updates the same TODO."""
            payload = self.generate_large_payload(min_size_kb=3)
            result = await self.update_todo(
                session,
                todo_id,
                title=f"Race condition test {worker_id}",
                priority=worker_id % 5,
                completed=worker_id % 2 == 0,
                payload=payload
            )
            if result:
                return result
            return None
        
        async with aiohttp.ClientSession() as session:
            tasks = [updater_worker(session, i) for i in range(updaters)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(f"Updater exception: {result}")
                elif result:
                    update_count += 1
                    final_states.append({
                        "title": result["title"],
                        "priority": result["priority"],
                        "completed": result["completed"]
                    })
        
        # Fetch final state
        async with aiohttp.ClientSession() as session:
            final_todo = await self.get_todo(session, todo_id)
            if final_todo:
                final_states.append({
                    "final_title": final_todo["title"],
                    "final_priority": final_todo["priority"],
                    "final_completed": final_todo["completed"]
                })
        
        duration = time.time() - start_time
        
        details = {
            "updaters": updaters,
            "successful_updates": update_count,
            "final_state": final_states[-1] if final_states else None,
            "unique_final_states": len(set(str(s) for s in final_states[:-1])) if len(final_states) > 1 else 0
        }
        
        # Success if updates happened (race conditions are expected)
        success = update_count > 0 and len(errors) == 0
        
        return TestResult(
            f"Race Condition Test ({updaters} updaters)",
            success,
            duration,
            operations=update_count,
            errors=errors,
            details=details
        )
    
    async def test_scale_limits(self, start_count: int = 1000, 
                               increment: int = 500) -> TestResult:
        """Test how many TODOs can be created and managed."""
        start_time = time.time()
        errors = []
        max_created = 0
        
        # Test creating increasingly large batches
        test_counts = [start_count]
        for i in range(3):
            test_counts.append(test_counts[-1] + increment)
        
        details = {}
        
        async with aiohttp.ClientSession() as session:
            for count in test_counts:
                batch_start = time.time()
                total_payload_size_kb = 0
                tasks = []
                for i in range(count):
                    # Generate sizable payload for each TODO
                    payload = self.generate_large_payload(min_size_kb=3)
                    payload_size = len(json.dumps(payload).encode('utf-8')) / 1024
                    total_payload_size_kb += payload_size
                    tasks.append(
                        self.create_todo(
                            session, 
                            f"Scale test {i}", 
                            priority=i % 5,
                            payload=payload
                        )
                    )
                results = await asyncio.gather(*tasks, return_exceptions=True)
                created = sum(1 for r in results if r is not None and not isinstance(r, Exception))
                batch_duration = time.time() - batch_start
                
                # Verify payloads
                payload_verified = sum(
                    1 for r in results 
                    if r is not None and not isinstance(r, Exception) and r.get("payload")
                )
                
                details[f"batch_{count}"] = {
                    "created": created,
                    "duration": f"{batch_duration:.2f}s",
                    "rate": f"{created/batch_duration:.2f}/s" if batch_duration > 0 else "N/A",
                    "payload_size_mb": f"{total_payload_size_kb/1024:.2f}",
                    "payloads_verified": payload_verified
                }
                
                max_created = max(max_created, created)
                
                if created < count * 0.9:  # Less than 90% success
                    errors.append(f"Batch {count}: Only {created}/{count} created")
                    break
        
        duration = time.time() - start_time
        
        details["max_created"] = max_created
        
        return TestResult(
            "Scale Limits Test",
            len(errors) == 0,
            duration,
            operations=max_created,
            errors=errors,
            details=details
        )
    
    async def cleanup(self):
        """Clean up created TODOs."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.delete_todo(session, todo_id) for todo_id in self.created_todo_ids]
            await asyncio.gather(*tasks, return_exceptions=True)
        self.created_todo_ids.clear()
    
    async def run_all_tests(self):
        """Run all test cases."""
        print("=" * 80)
        print("TODO API Comprehensive Test Suite")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print()
        
        # Test 1: Basic CRUD
        result = await self.test_basic_crud()
        self.log_result(result)
        print()
        
        # Test 2: Bulk create (small batch first)
        result = await self.test_bulk_create(count=50)
        self.log_result(result)
        print()
        
        # Test 3: Bulk create (larger batch)
        result = await self.test_bulk_create(count=200)
        self.log_result(result)
        print()
        
        # Get some TODO IDs for concurrent tests
        async with aiohttp.ClientSession() as session:
            todos = await self.list_todos(session)
            test_todo_ids = [t["id"] for t in todos[:20]]  # Use first 20 TODOs
        
        if not test_todo_ids:
            print("Warning: No TODOs available for concurrent tests. Creating some...")
            async with aiohttp.ClientSession() as session:
                for i in range(20):
                    payload = self.generate_large_payload(min_size_kb=3)
                    todo = await self.create_todo(
                        session, 
                        f"Test TODO {i}", 
                        priority=i % 5,
                        payload=payload
                    )
                    if todo:
                        test_todo_ids.append(todo["id"])
        
        # Test 4: Concurrent updates
        result = await self.test_concurrent_updates(test_todo_ids[:10], clients=10)
        self.log_result(result)
        print()
        
        # Test 5: Parallel reads
        result = await self.test_parallel_reads(test_todo_ids[:10], readers=20)
        self.log_result(result)
        print()
        
        # Test 6: Mixed workload
        result = await self.test_mixed_workload(test_todo_ids[:15], writers=5, readers=15)
        self.log_result(result)
        print()
        
        # Test 7: Race condition
        if test_todo_ids:
            result = await self.test_race_condition(test_todo_ids[0], updaters=20)
            self.log_result(result)
            print()
        
        # Test 8: Scale limits
        result = await self.test_scale_limits(start_count=500, increment=500)
        self.log_result(result)
        print()
        
        # Print summary
        print("=" * 80)
        print("Test Summary")
        print("=" * 80)
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print()
        
        if self.results:
            total_duration = sum(r.duration for r in self.results)
            total_operations = sum(r.operations for r in self.results)
            print(f"Total Duration: {total_duration:.2f}s")
            print(f"Total Operations: {total_operations}")
            if total_duration > 0:
                print(f"Overall Rate: {total_operations/total_duration:.2f} ops/sec")
        
        print()
        print("Detailed Results:")
        for result in self.results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.test_name}: {result.duration:.2f}s, {result.operations} ops")
            if result.details:
                for key, value in result.details.items():
                    print(f"    {key}: {value}")


async def main():
    """Main entry point."""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    cookie = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = TodoAPITester(base_url, cookie=cookie)
    
    try:
        await tester.run_all_tests()
    finally:
        # Optional: cleanup created TODOs
        # Uncomment if you want to clean up after tests
        # await tester.cleanup()
        pass


if __name__ == "__main__":
    asyncio.run(main())

