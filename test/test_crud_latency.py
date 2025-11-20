#!/usr/bin/env python3
"""
Test individual CRUD operation latencies to understand performance.
"""
import asyncio
import aiohttp
import time
from typing import Dict, List

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/todo"


async def test_create_latency(session: aiohttp.ClientSession, count: int = 10) -> List[float]:
    """Test create operation latency."""
    latencies = []
    for i in range(count):
        start = time.time()
        async with session.post(API_BASE, json={
            "title": f"Latency test {i}",
            "priority": 1
        }) as resp:
            if resp.status == 201:
                await resp.json()
                latencies.append(time.time() - start)
            else:
                error = await resp.text()
                print(f"Create failed: {error}")
    return latencies


async def test_read_latency(session: aiohttp.ClientSession, todo_id: int, count: int = 10) -> List[float]:
    """Test read operation latency."""
    latencies = []
    for i in range(count):
        start = time.time()
        async with session.get(f"{API_BASE}/{todo_id}") as resp:
            if resp.status == 200:
                await resp.json()
                latencies.append(time.time() - start)
            else:
                print(f"Read failed: {resp.status}")
    return latencies


async def test_update_latency(session: aiohttp.ClientSession, todo_id: int, count: int = 10) -> List[float]:
    """Test update operation latency."""
    latencies = []
    for i in range(count):
        start = time.time()
        async with session.put(f"{API_BASE}/{todo_id}", json={
            "title": f"Updated {i}",
            "priority": i % 5
        }) as resp:
            if resp.status == 200:
                await resp.json()
                latencies.append(time.time() - start)
            else:
                print(f"Update failed: {resp.status}")
    return latencies


async def test_list_latency(session: aiohttp.ClientSession, count: int = 10) -> List[float]:
    """Test list operation latency."""
    latencies = []
    for i in range(count):
        start = time.time()
        async with session.get(API_BASE) as resp:
            if resp.status == 200:
                await resp.json()
                latencies.append(time.time() - start)
            else:
                print(f"List failed: {resp.status}")
    return latencies


async def test_delete_latency(session: aiohttp.ClientSession, todo_id: int) -> float:
    """Test delete operation latency."""
    start = time.time()
    async with session.delete(f"{API_BASE}/{todo_id}") as resp:
        if resp.status == 204:
            return time.time() - start
        else:
            print(f"Delete failed: {resp.status}")
            return None


async def main():
    print("=" * 80)
    print("Individual CRUD Operation Latency Test")
    print("=" * 80)
    print()
    
    async with aiohttp.ClientSession() as session:
        # Test CREATE
        print("Testing CREATE operations (10 iterations)...")
        create_latencies = await test_create_latency(session, count=10)
        if create_latencies:
            print(f"  Min: {min(create_latencies)*1000:.2f}ms")
            print(f"  Max: {max(create_latencies)*1000:.2f}ms")
            print(f"  Avg: {sum(create_latencies)/len(create_latencies)*1000:.2f}ms")
            print(f"  Total: {sum(create_latencies):.3f}s")
            print()
        
        # Get a TODO ID for read/update/delete tests
        if create_latencies:
            # Get the last created TODO
            async with session.get(API_BASE) as resp:
                todos = await resp.json()
                if todos:
                    test_todo_id = todos[0]["id"]
                    
                    # Test READ
                    print("Testing READ operations (10 iterations)...")
                    read_latencies = await test_read_latency(session, test_todo_id, count=10)
                    if read_latencies:
                        print(f"  Min: {min(read_latencies)*1000:.2f}ms")
                        print(f"  Max: {max(read_latencies)*1000:.2f}ms")
                        print(f"  Avg: {sum(read_latencies)/len(read_latencies)*1000:.2f}ms")
                        print(f"  Total: {sum(read_latencies):.3f}s")
                        print()
                    
                    # Test UPDATE
                    print("Testing UPDATE operations (10 iterations)...")
                    update_latencies = await test_update_latency(session, test_todo_id, count=10)
                    if update_latencies:
                        print(f"  Min: {min(update_latencies)*1000:.2f}ms")
                        print(f"  Max: {max(update_latencies)*1000:.2f}ms")
                        print(f"  Avg: {sum(update_latencies)/len(update_latencies)*1000:.2f}ms")
                        print(f"  Total: {sum(update_latencies):.3f}s")
                        print()
                    
                    # Test LIST
                    print("Testing LIST operations (10 iterations)...")
                    list_latencies = await test_list_latency(session, count=10)
                    if list_latencies:
                        print(f"  Min: {min(list_latencies)*1000:.2f}ms")
                        print(f"  Max: {max(list_latencies)*1000:.2f}ms")
                        print(f"  Avg: {sum(list_latencies)/len(list_latencies)*1000:.2f}ms")
                        print(f"  Total: {sum(list_latencies):.3f}s")
                        print()
                    
                    # Test DELETE
                    print("Testing DELETE operation...")
                    delete_latency = await test_delete_latency(session, test_todo_id)
                    if delete_latency:
                        print(f"  Latency: {delete_latency*1000:.2f}ms")
                        print()
        
        # Summary
        print("=" * 80)
        print("Summary")
        print("=" * 80)
        if create_latencies:
            print(f"CREATE: {sum(create_latencies)/len(create_latencies)*1000:.2f}ms avg")
        if read_latencies:
            print(f"READ:   {sum(read_latencies)/len(read_latencies)*1000:.2f}ms avg")
        if update_latencies:
            print(f"UPDATE: {sum(update_latencies)/len(update_latencies)*1000:.2f}ms avg")
        if list_latencies:
            print(f"LIST:   {sum(list_latencies)/len(list_latencies)*1000:.2f}ms avg")
        if delete_latency:
            print(f"DELETE: {delete_latency*1000:.2f}ms")
        
        total_ops = len(create_latencies) + len(read_latencies) + len(update_latencies) + len(list_latencies) + 1
        total_time = sum(create_latencies) + sum(read_latencies) + sum(update_latencies) + sum(list_latencies) + (delete_latency or 0)
        print()
        print(f"Total operations: {total_ops}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average per operation: {total_time/total_ops*1000:.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())

