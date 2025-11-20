#!/usr/bin/env python3
"""
Comprehensive CRUD operation timing test with server-side timing breakdowns.
Reads timing metadata from response headers.
"""
import asyncio
import aiohttp
import time
import json
import statistics
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class ServerTiming:
    """Server-side timing breakdown."""
    connection_acquisition_ms: float = 0.0
    query_execution_ms: float = 0.0
    data_transformation_ms: float = 0.0
    repository_total_ms: float = 0.0
    endpoint_processing_ms: float = 0.0
    response_serialization_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class OperationResult:
    """Result of a single operation with timing."""
    operation: str
    client_total_ms: float
    server_timing: ServerTiming
    success: bool
    details: Dict = field(default_factory=dict)


@dataclass
class OperationStats:
    """Statistics for multiple operations."""
    operation: str
    count: int
    client_avg_ms: float
    client_min_ms: float
    client_max_ms: float
    server_avg_total_ms: float
    server_avg_conn_ms: float
    server_avg_query_ms: float
    server_avg_transform_ms: float
    server_avg_repo_ms: float
    server_avg_endpoint_ms: float
    server_avg_serialize_ms: float
    results: List[OperationResult] = field(default_factory=list)


class TimingCRUDTester:
    """Test CRUD operations with server-side timing."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/todo"
        self.created_todo_ids: List[int] = []
    
    def parse_timing_headers(self, headers) -> ServerTiming:
        """Parse timing information from response headers."""
        timing = ServerTiming()
        
        # aiohttp headers are case-insensitive, convert to dict and check all variations
        header_dict = dict(headers) if isinstance(headers, dict) else {k: v for k, v in headers.items()}
        
        # Try to get JSON timing header first (more reliable)
        timing_json = None
        for key in ["X-Timing-JSON", "x-timing-json"]:
            if key in header_dict:
                timing_json = header_dict[key]
                break
        
        if timing_json:
            try:
                timing_dict = json.loads(timing_json)
                timing.connection_acquisition_ms = timing_dict.get("connection_acquisition_ms", 0.0)
                timing.query_execution_ms = timing_dict.get("query_execution_ms", 0.0)
                timing.data_transformation_ms = timing_dict.get("data_transformation_ms", 0.0)
                timing.repository_total_ms = timing_dict.get("repository_total_ms", 0.0)
                timing.endpoint_processing_ms = timing_dict.get("endpoint_processing_ms", 0.0)
                timing.response_serialization_ms = timing_dict.get("response_serialization_ms", 0.0)
                timing.total_ms = timing_dict.get("total_ms", 0.0)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # Debug: print what we got
                print(f"  Warning: Could not parse timing header: {e}, value: {timing_json}")
        
        return timing
    
    async def test_create(self, session: aiohttp.ClientSession, 
                         title: str, description: str = None, 
                         priority: int = 2) -> OperationResult:
        """Test CREATE operation with timing."""
        client_start = time.time()
        
        data = {
            "title": title,
            "priority": priority
        }
        if description:
            data["description"] = description
        
        async with session.post(self.api_base, json=data) as resp:
            client_total = (time.time() - client_start) * 1000
            
            # Get headers - aiohttp returns CIMultiDict, convert to regular dict
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 201:
                todo = await resp.json()
                self.created_todo_ids.append(todo["id"])
                return OperationResult(
                    operation="CREATE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"todo_id": todo["id"], "status": resp.status}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="CREATE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    async def test_read(self, session: aiohttp.ClientSession, 
                       todo_id: int) -> OperationResult:
        """Test READ operation with timing."""
        client_start = time.time()
        
        async with session.get(f"{self.api_base}/{todo_id}") as resp:
            client_total = (time.time() - client_start) * 1000
            
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 200:
                todo = await resp.json()
                return OperationResult(
                    operation="READ",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"todo_id": todo_id, "status": resp.status}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="READ",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    async def test_update(self, session: aiohttp.ClientSession, 
                         todo_id: int, **kwargs) -> OperationResult:
        """Test UPDATE operation with timing."""
        client_start = time.time()
        
        async with session.put(f"{self.api_base}/{todo_id}", json=kwargs) as resp:
            client_total = (time.time() - client_start) * 1000
            
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 200:
                todo = await resp.json()
                return OperationResult(
                    operation="UPDATE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"todo_id": todo_id, "status": resp.status}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="UPDATE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    async def test_delete(self, session: aiohttp.ClientSession, 
                         todo_id: int) -> OperationResult:
        """Test DELETE operation with timing."""
        client_start = time.time()
        
        async with session.delete(f"{self.api_base}/{todo_id}") as resp:
            client_total = (time.time() - client_start) * 1000
            
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 204:
                return OperationResult(
                    operation="DELETE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"todo_id": todo_id, "status": resp.status}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="DELETE",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    async def test_list(self, session: aiohttp.ClientSession, 
                       completed: bool = None, priority: int = None) -> OperationResult:
        """Test LIST operation with timing."""
        client_start = time.time()
        
        params = {}
        if completed is not None:
            params["completed"] = str(completed).lower()
        if priority is not None:
            params["priority"] = str(priority)
        
        async with session.get(self.api_base, params=params) as resp:
            client_total = (time.time() - client_start) * 1000
            
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 200:
                todos = await resp.json()
                return OperationResult(
                    operation="LIST",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"count": len(todos), "status": resp.status, "filters": params}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="LIST",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    async def test_select_one(self, session: aiohttp.ClientSession) -> OperationResult:
        """Test SELECT 1 operation with timing - isolates network/connection overhead."""
        client_start = time.time()
        
        async with session.get(f"{self.base_url}/api/test/select-one") as resp:
            client_total = (time.time() - client_start) * 1000
            
            headers_dict = {k: v for k, v in resp.headers.items()}
            server_timing = self.parse_timing_headers(headers_dict)
            
            if resp.status == 200:
                result = await resp.json()
                return OperationResult(
                    operation="SELECT 1",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=True,
                    details={"result": result.get("result"), "status": resp.status}
                )
            else:
                error = await resp.text()
                return OperationResult(
                    operation="SELECT 1",
                    client_total_ms=client_total,
                    server_timing=server_timing,
                    success=False,
                    details={"status": resp.status, "error": error}
                )
    
    def calculate_stats(self, results: List[OperationResult]) -> OperationStats:
        """Calculate statistics from operation results."""
        if not results:
            return OperationStats(
                operation="UNKNOWN",
                count=0,
                client_avg_ms=0.0,
                client_min_ms=0.0,
                client_max_ms=0.0,
                server_avg_total_ms=0.0,
                server_avg_conn_ms=0.0,
                server_avg_query_ms=0.0,
                server_avg_transform_ms=0.0,
                server_avg_repo_ms=0.0,
                server_avg_endpoint_ms=0.0,
                server_avg_serialize_ms=0.0
            )
        
        client_times = [r.client_total_ms for r in results]
        server_totals = [r.server_timing.total_ms for r in results]
        server_conns = [r.server_timing.connection_acquisition_ms for r in results]
        server_queries = [r.server_timing.query_execution_ms for r in results]
        server_transforms = [r.server_timing.data_transformation_ms for r in results]
        server_repos = [r.server_timing.repository_total_ms for r in results]
        server_endpoints = [r.server_timing.endpoint_processing_ms for r in results]
        server_serializes = [r.server_timing.response_serialization_ms for r in results]
        
        return OperationStats(
            operation=results[0].operation,
            count=len(results),
            client_avg_ms=statistics.mean(client_times),
            client_min_ms=min(client_times),
            client_max_ms=max(client_times),
            server_avg_total_ms=statistics.mean(server_totals),
            server_avg_conn_ms=statistics.mean(server_conns),
            server_avg_query_ms=statistics.mean(server_queries),
            server_avg_transform_ms=statistics.mean(server_transforms),
            server_avg_repo_ms=statistics.mean(server_repos),
            server_avg_endpoint_ms=statistics.mean(server_endpoints),
            server_avg_serialize_ms=statistics.mean(server_serializes),
            results=results
        )
    
    def print_stats(self, stats: OperationStats):
        """Print detailed statistics."""
        print(f"\n{'='*80}")
        print(f"Operation: {stats.operation}")
        print(f"{'='*80}")
        print(f"Count: {stats.count}")
        
        print(f"\nClient-Side Timing:")
        print(f"  Avg: {stats.client_avg_ms:8.2f}ms")
        print(f"  Min: {stats.client_min_ms:8.2f}ms")
        print(f"  Max: {stats.client_max_ms:8.2f}ms")
        
        print(f"\nServer-Side Timing Breakdown:")
        if stats.server_avg_total_ms > 0:
            print(f"  Total:              {stats.server_avg_total_ms:8.2f}ms ({stats.server_avg_total_ms/stats.client_avg_ms*100:.1f}% of client time)")
            print(f"  ├─ Connection:      {stats.server_avg_conn_ms:8.2f}ms ({stats.server_avg_conn_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
            print(f"  ├─ Query Exec:      {stats.server_avg_query_ms:8.2f}ms ({stats.server_avg_query_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
            print(f"  ├─ Transform:       {stats.server_avg_transform_ms:8.2f}ms ({stats.server_avg_transform_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
            print(f"  ├─ Repository:      {stats.server_avg_repo_ms:8.2f}ms ({stats.server_avg_repo_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
            print(f"  ├─ Endpoint:        {stats.server_avg_endpoint_ms:8.2f}ms ({stats.server_avg_endpoint_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
            print(f"  └─ Serialization:   {stats.server_avg_serialize_ms:8.2f}ms ({stats.server_avg_serialize_ms/stats.server_avg_total_ms*100:.1f}% of server time)")
        else:
            print(f"  Total:              {stats.server_avg_total_ms:8.2f}ms ({stats.server_avg_total_ms/stats.client_avg_ms*100:.1f}% of client time)")
            print(f"  ⚠️  No server timing data available (headers may not be set)")
        
        # Calculate network overhead
        network_overhead = stats.client_avg_ms - stats.server_avg_total_ms
        print(f"\nNetwork Overhead (Client - Server):")
        print(f"  Estimated:          {network_overhead:8.2f}ms ({network_overhead/stats.client_avg_ms*100:.1f}% of client time)")
        
        # Show first few detailed results
        print(f"\nFirst 3 Detailed Results:")
        for i, result in enumerate(stats.results[:3], 1):
            print(f"  {i}. Client: {result.client_total_ms:6.2f}ms | "
                  f"Server: {result.server_timing.total_ms:6.2f}ms | "
                  f"Conn: {result.server_timing.connection_acquisition_ms:5.2f}ms | "
                  f"Query: {result.server_timing.query_execution_ms:5.2f}ms")
    
    async def run_comprehensive_test(self, iterations: int = 20):
        """Run comprehensive CRUD tests with server-side timing."""
        print("="*80)
        print("Comprehensive CRUD Operation Timing Test (with Server-Side Breakdown)")
        print("="*80)
        print(f"Iterations per operation: {iterations}")
        print()
        
        async with aiohttp.ClientSession() as session:
            # Test CREATE
            print("Testing CREATE operations...")
            create_results = []
            for i in range(iterations):
                result = await self.test_create(
                    session, 
                    f"Timing Test {i}", 
                    f"Description {i}",
                    priority=i % 5
                )
                create_results.append(result)
                if i % 5 == 0:
                    print(f"  Completed {i+1}/{iterations}...")
            
            create_stats = self.calculate_stats(create_results)
            self.print_stats(create_stats)
            
            # Test READ
            if self.created_todo_ids:
                print("\nTesting READ operations...")
                read_results = []
                test_ids = self.created_todo_ids[:iterations]
                for i, todo_id in enumerate(test_ids):
                    result = await self.test_read(session, todo_id)
                    read_results.append(result)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{len(test_ids)}...")
                
                read_stats = self.calculate_stats(read_results)
                self.print_stats(read_stats)
                
                # Test UPDATE
                print("\nTesting UPDATE operations...")
                update_results = []
                for i, todo_id in enumerate(test_ids[:iterations]):
                    result = await self.test_update(
                        session, 
                        todo_id,
                        title=f"Updated {i}",
                        completed=i % 2 == 0,
                        priority=(i + 1) % 5
                    )
                    update_results.append(result)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{min(iterations, len(test_ids))}...")
                
                update_stats = self.calculate_stats(update_results)
                self.print_stats(update_stats)
            
            # Test LIST
            print("\nTesting LIST operations...")
            list_results = []
            for i in range(min(iterations, 10)):
                if i % 3 == 0:
                    result = await self.test_list(session, completed=False)
                elif i % 3 == 1:
                    result = await self.test_list(session, priority=1)
                else:
                    result = await self.test_list(session)
                list_results.append(result)
                if i % 3 == 0:
                    print(f"  Completed {i+1}/{min(iterations, 10)}...")
            
            list_stats = self.calculate_stats(list_results)
            self.print_stats(list_stats)
            
            # Test DELETE
            if self.created_todo_ids:
                print("\nTesting DELETE operations...")
                delete_results = []
                ids_to_delete = self.created_todo_ids[:iterations]
                for i, todo_id in enumerate(ids_to_delete):
                    result = await self.test_delete(session, todo_id)
                    delete_results.append(result)
                    if i % 5 == 0:
                        print(f"  Completed {i+1}/{len(ids_to_delete)}...")
                
                delete_stats = self.calculate_stats(delete_results)
                self.print_stats(delete_stats)
            
            # Test SELECT 1 (to isolate network/connection overhead)
            print("\nTesting SELECT 1 operations (isolates network/connection overhead)...")
            select_one_results = []
            for i in range(iterations):
                result = await self.test_select_one(session)
                select_one_results.append(result)
                if i % 5 == 0:
                    print(f"  Completed {i+1}/{iterations}...")
            
            select_one_stats = self.calculate_stats(select_one_results)
            self.print_stats(select_one_stats)
            
            # Summary
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            all_stats = [create_stats, read_stats, update_stats, list_stats, delete_stats, select_one_stats]
            print(f"{'Operation':<12} {'Client Avg':>12} {'Server Total':>12} {'Conn':>8} {'Query':>8} {'Network':>10} {'DB Work':>10}")
            print("-" * 90)
            for stats in all_stats:
                if stats.count > 0:
                    network = stats.client_avg_ms - stats.server_avg_total_ms
                    # For SELECT 1, DB work is minimal (just returning constant)
                    # For other ops, DB work is the query execution time
                    db_work = stats.server_avg_query_ms if stats.operation != "SELECT 1" else "~0.01ms"
                    print(f"{stats.operation:<12} "
                          f"{stats.client_avg_ms:>12.2f}ms "
                          f"{stats.server_avg_total_ms:>12.2f}ms "
                          f"{stats.server_avg_conn_ms:>8.2f}ms "
                          f"{stats.server_avg_query_ms:>8.2f}ms "
                          f"{network:>10.2f}ms "
                          f"{str(db_work):>10}")
            
            # Comparison analysis
            if select_one_stats.count > 0:
                print("\n" + "="*80)
                print("NETWORK OVERHEAD ANALYSIS")
                print("="*80)
                print(f"SELECT 1 (minimal DB work):")
                print(f"  Total time: {select_one_stats.server_avg_total_ms:.2f}ms")
                print(f"  Connection: {select_one_stats.server_avg_conn_ms:.2f}ms")
                print(f"  Query:      {select_one_stats.server_avg_query_ms:.2f}ms")
                print(f"  Network:    {select_one_stats.client_avg_ms - select_one_stats.server_avg_total_ms:.2f}ms")
                print()
                print("CRUD Operations (with actual DB work):")
                for stats in [create_stats, read_stats, update_stats, delete_stats]:
                    if stats.count > 0:
                        network_overhead = stats.client_avg_ms - stats.server_avg_total_ms
                        db_work_time = stats.server_avg_query_ms - select_one_stats.server_avg_query_ms
                        print(f"  {stats.operation}:")
                        print(f"    Total:        {stats.server_avg_total_ms:.2f}ms")
                        print(f"    Network:      {network_overhead:.2f}ms")
                        print(f"    DB Work:      {db_work_time:.2f}ms (query - SELECT 1 query)")
                        print(f"    Overhead:     {stats.server_avg_total_ms - select_one_stats.server_avg_total_ms:.2f}ms (vs SELECT 1)")


async def main():
    tester = TimingCRUDTester("http://localhost:8000")
    await tester.run_comprehensive_test(iterations=20)


if __name__ == "__main__":
    asyncio.run(main())

