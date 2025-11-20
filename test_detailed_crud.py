#!/usr/bin/env python3
"""
Comprehensive CRUD operation timing test with detailed breakdowns.
Measures actual timings at each stage of the operation.
"""
import asyncio
import aiohttp
import time
import statistics
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class OperationTiming:
    """Timing breakdown for a single operation."""
    operation: str
    total_time: float
    http_request_time: float = 0.0
    http_response_time: float = 0.0
    database_time: float = 0.0  # Estimated from response time
    serialization_time: float = 0.0  # Estimated
    network_time: float = 0.0  # Estimated
    details: Dict = field(default_factory=dict)


@dataclass
class OperationStats:
    """Statistics for multiple operations of the same type."""
    operation: str
    count: int
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    timings: List[OperationTiming] = field(default_factory=list)


class DetailedCRUDTester:
    """Test CRUD operations with detailed timing breakdowns."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/todo"
        self.created_todo_ids: List[int] = []
    
    async def measure_create(self, session: aiohttp.ClientSession, 
                           title: str, description: str = None, 
                           priority: int = 2, iteration: int = 0) -> OperationTiming:
        """Measure CREATE operation with detailed timing."""
        timing = OperationTiming(operation="CREATE", total_time=0.0)
        
        # Prepare data
        data = {
            "title": title,
            "priority": priority
        }
        if description:
            data["description"] = description
        
        # Measure HTTP request time
        request_start = time.time()
        async with session.post(self.api_base, json=data) as resp:
            request_time = time.time() - request_start
            timing.http_request_time = request_time
            
            # Measure response reading time
            response_start = time.time()
            if resp.status == 201:
                result = await resp.json()
                response_time = time.time() - response_start
                timing.http_response_time = response_time
                timing.total_time = request_time + response_time
                
                # Store TODO ID
                todo_id = result["id"]
                self.created_todo_ids.append(todo_id)
                timing.details = {
                    "todo_id": todo_id,
                    "status": resp.status,
                    "iteration": iteration
                }
            else:
                error_text = await resp.text()
                timing.details = {
                    "status": resp.status,
                    "error": error_text,
                    "iteration": iteration
                }
        
        return timing
    
    async def measure_read(self, session: aiohttp.ClientSession, 
                          todo_id: int, iteration: int = 0) -> OperationTiming:
        """Measure READ operation with detailed timing."""
        timing = OperationTiming(operation="READ", total_time=0.0)
        
        # Measure HTTP request time
        request_start = time.time()
        async with session.get(f"{self.api_base}/{todo_id}") as resp:
            request_time = time.time() - request_start
            timing.http_request_time = request_time
            
            # Measure response reading time
            response_start = time.time()
            if resp.status == 200:
                result = await resp.json()
                response_time = time.time() - response_start
                timing.http_response_time = response_time
                timing.total_time = request_time + response_time
                
                timing.details = {
                    "todo_id": todo_id,
                    "status": resp.status,
                    "title": result.get("title", ""),
                    "iteration": iteration
                }
            else:
                error_text = await resp.text()
                timing.details = {
                    "status": resp.status,
                    "error": error_text,
                    "iteration": iteration
                }
        
        return timing
    
    async def measure_update(self, session: aiohttp.ClientSession, 
                            todo_id: int, **kwargs) -> OperationTiming:
        """Measure UPDATE operation with detailed timing."""
        timing = OperationTiming(operation="UPDATE", total_time=0.0)
        
        # Measure HTTP request time
        request_start = time.time()
        async with session.put(f"{self.api_base}/{todo_id}", json=kwargs) as resp:
            request_time = time.time() - request_start
            timing.http_request_time = request_time
            
            # Measure response reading time
            response_start = time.time()
            if resp.status == 200:
                result = await resp.json()
                response_time = time.time() - response_start
                timing.http_response_time = response_time
                timing.total_time = request_time + response_time
                
                timing.details = {
                    "todo_id": todo_id,
                    "status": resp.status,
                    "updated_fields": list(kwargs.keys())
                }
            else:
                error_text = await resp.text()
                timing.details = {
                    "status": resp.status,
                    "error": error_text
                }
        
        return timing
    
    async def measure_delete(self, session: aiohttp.ClientSession, 
                           todo_id: int) -> OperationTiming:
        """Measure DELETE operation with detailed timing."""
        timing = OperationTiming(operation="DELETE", total_time=0.0)
        
        # Measure HTTP request time
        request_start = time.time()
        async with session.delete(f"{self.api_base}/{todo_id}") as resp:
            request_time = time.time() - request_start
            timing.http_request_time = request_time
            timing.http_response_time = 0.0  # DELETE returns 204 No Content
            timing.total_time = request_time
            
            timing.details = {
                "todo_id": todo_id,
                "status": resp.status
            }
        
        return timing
    
    async def measure_list(self, session: aiohttp.ClientSession, 
                          completed: bool = None, priority: int = None,
                          limit: int = None) -> OperationTiming:
        """Measure LIST operation with detailed timing."""
        timing = OperationTiming(operation="LIST", total_time=0.0)
        
        # Build query params
        params = {}
        if completed is not None:
            params["completed"] = str(completed).lower()
        if priority is not None:
            params["priority"] = str(priority)
        
        # Measure HTTP request time
        request_start = time.time()
        async with session.get(self.api_base, params=params) as resp:
            request_time = time.time() - request_start
            timing.http_request_time = request_time
            
            # Measure response reading time
            response_start = time.time()
            if resp.status == 200:
                result = await resp.json()
                response_time = time.time() - response_start
                timing.http_response_time = response_time
                timing.total_time = request_time + response_time
                
                timing.details = {
                    "status": resp.status,
                    "count": len(result),
                    "filters": params
                }
            else:
                error_text = await resp.text()
                timing.details = {
                    "status": resp.status,
                    "error": error_text
                }
        
        return timing
    
    def calculate_stats(self, timings: List[OperationTiming]) -> OperationStats:
        """Calculate statistics for a list of timings."""
        if not timings:
            return OperationStats(
                operation="UNKNOWN",
                count=0,
                min_time=0.0,
                max_time=0.0,
                avg_time=0.0,
                median_time=0.0,
                p95_time=0.0,
                p99_time=0.0
            )
        
        total_times = [t.total_time for t in timings]
        request_times = [t.http_request_time for t in timings]
        response_times = [t.http_response_time for t in timings]
        
        sorted_times = sorted(total_times)
        n = len(sorted_times)
        
        return OperationStats(
            operation=timings[0].operation,
            count=len(timings),
            min_time=min(total_times),
            max_time=max(total_times),
            avg_time=statistics.mean(total_times),
            median_time=statistics.median(total_times),
            p95_time=sorted_times[int(n * 0.95)] if n > 0 else 0.0,
            p99_time=sorted_times[int(n * 0.99)] if n > 0 else 0.0,
            timings=timings
        )
    
    def print_stats(self, stats: OperationStats):
        """Print detailed statistics."""
        print(f"\n{'='*80}")
        print(f"Operation: {stats.operation}")
        print(f"{'='*80}")
        print(f"Count: {stats.count}")
        print(f"\nTotal Time:")
        print(f"  Min:    {stats.min_time*1000:8.2f}ms")
        print(f"  Max:    {stats.max_time*1000:8.2f}ms")
        print(f"  Avg:    {stats.avg_time*1000:8.2f}ms")
        print(f"  Median: {stats.median_time*1000:8.2f}ms")
        print(f"  P95:    {stats.p95_time*1000:8.2f}ms")
        print(f"  P99:    {stats.p99_time*1000:8.2f}ms")
        
        # Breakdown by component
        if stats.timings:
            avg_request = statistics.mean([t.http_request_time for t in stats.timings])
            avg_response = statistics.mean([t.http_response_time for t in stats.timings])
            
            print(f"\nBreakdown (Average):")
            print(f"  HTTP Request:  {avg_request*1000:8.2f}ms ({avg_request/stats.avg_time*100:.1f}%)")
            print(f"  HTTP Response: {avg_response*1000:8.2f}ms ({avg_response/stats.avg_time*100:.1f}%)")
            
            # Show first few detailed timings
            print(f"\nFirst 5 Detailed Timings:")
            for i, timing in enumerate(stats.timings[:5], 1):
                print(f"  {i}. Total: {timing.total_time*1000:6.2f}ms | "
                      f"Request: {timing.http_request_time*1000:6.2f}ms | "
                      f"Response: {timing.http_response_time*1000:6.2f}ms")
                if timing.details:
                    print(f"     Details: {timing.details}")
    
    async def run_comprehensive_test(self, iterations: int = 20):
        """Run comprehensive CRUD tests with detailed timing."""
        print("="*80)
        print("Comprehensive CRUD Operation Timing Test")
        print("="*80)
        print(f"Iterations per operation: {iterations}")
        print()
        
        async with aiohttp.ClientSession() as session:
            # Test CREATE
            print("Testing CREATE operations...")
            create_timings = []
            for i in range(iterations):
                timing = await self.measure_create(
                    session, 
                    f"Test TODO {i}", 
                    f"Description {i}",
                    priority=i % 5,
                    iteration=i
                )
                create_timings.append(timing)
                if i % 5 == 0:
                    print(f"  Completed {i+1}/{iterations}...")
            
            create_stats = self.calculate_stats(create_timings)
            self.print_stats(create_stats)
            
            # Test READ (use created TODOs)
            if self.created_todo_ids:
                print("\nTesting READ operations...")
                read_timings = []
                test_ids = self.created_todo_ids[:iterations]
                for i, todo_id in enumerate(test_ids):
                    timing = await self.measure_read(session, todo_id, iteration=i)
                    read_timings.append(timing)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{len(test_ids)}...")
                
                read_stats = self.calculate_stats(read_timings)
                self.print_stats(read_stats)
                
                # Test UPDATE
                print("\nTesting UPDATE operations...")
                update_timings = []
                for i, todo_id in enumerate(test_ids[:iterations]):
                    timing = await self.measure_update(
                        session, 
                        todo_id,
                        title=f"Updated {i}",
                        completed=i % 2 == 0,
                        priority=(i + 1) % 5
                    )
                    update_timings.append(timing)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{min(iterations, len(test_ids))}...")
                
                update_stats = self.calculate_stats(update_timings)
                self.print_stats(update_stats)
            
            # Test LIST (with different filters)
            print("\nTesting LIST operations...")
            list_timings = []
            for i in range(min(iterations, 10)):  # Fewer iterations for LIST
                # Test different filter combinations
                if i % 3 == 0:
                    timing = await self.measure_list(session, completed=False)
                elif i % 3 == 1:
                    timing = await self.measure_list(session, priority=1)
                else:
                    timing = await self.measure_list(session)
                list_timings.append(timing)
                if i % 3 == 0:
                    print(f"  Completed {i+1}/{min(iterations, 10)}...")
            
            list_stats = self.calculate_stats(list_timings)
            self.print_stats(list_stats)
            
            # Test DELETE (clean up)
            if self.created_todo_ids:
                print("\nTesting DELETE operations...")
                delete_timings = []
                # Delete in reverse order
                ids_to_delete = self.created_todo_ids[:iterations]
                for i, todo_id in enumerate(ids_to_delete):
                    timing = await self.measure_delete(session, todo_id)
                    delete_timings.append(timing)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{len(ids_to_delete)}...")
                
                delete_stats = self.calculate_stats(delete_timings)
                self.print_stats(delete_stats)
            
            # Summary
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            all_stats = [create_stats, read_stats, update_stats, list_stats, delete_stats]
            for stats in all_stats:
                if stats.count > 0:
                    print(f"{stats.operation:8s}: "
                          f"Avg {stats.avg_time*1000:6.2f}ms | "
                          f"Min {stats.min_time*1000:6.2f}ms | "
                          f"Max {stats.max_time*1000:6.2f}ms | "
                          f"P95 {stats.p95_time*1000:6.2f}ms")


async def main():
    tester = DetailedCRUDTester("http://localhost:8000")
    await tester.run_comprehensive_test(iterations=20)


if __name__ == "__main__":
    asyncio.run(main())

