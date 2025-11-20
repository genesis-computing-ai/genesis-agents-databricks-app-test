#!/usr/bin/env python3
"""
Test with server-side timing headers to understand where time is spent.
"""
import asyncio
import aiohttp
import time
import json
from typing import Dict, List


async def test_with_timing(base_url: str = "http://localhost:8000"):
    """Test operations and analyze timing headers."""
    
    async with aiohttp.ClientSession() as session:
        print("="*80)
        print("Server-Side Timing Analysis")
        print("="*80)
        print()
        
        # CREATE
        print("Testing CREATE...")
        start = time.time()
        async with session.post(f"{base_url}/api/todo", json={
            "title": "Timing test",
            "priority": 1
        }) as resp:
            create_time = time.time() - start
            todo = await resp.json()
            todo_id = todo["id"]
            
            print(f"  Total time: {create_time*1000:.2f}ms")
            print(f"  Status: {resp.status}")
            print(f"  Headers: {dict(resp.headers)}")
            print()
        
        # READ
        print("Testing READ...")
        start = time.time()
        async with session.get(f"{base_url}/api/todo/{todo_id}") as resp:
            read_time = time.time() - start
            result = await resp.json()
            
            print(f"  Total time: {read_time*1000:.2f}ms")
            print(f"  Status: {resp.status}")
            print()
        
        # UPDATE
        print("Testing UPDATE...")
        start = time.time()
        async with session.put(f"{base_url}/api/todo/{todo_id}", json={
            "completed": True
        }) as resp:
            update_time = time.time() - start
            result = await resp.json()
            
            print(f"  Total time: {update_time*1000:.2f}ms")
            print(f"  Status: {resp.status}")
            print()
        
        # DELETE
        print("Testing DELETE...")
        start = time.time()
        async with session.delete(f"{base_url}/api/todo/{todo_id}") as resp:
            delete_time = time.time() - start
            
            print(f"  Total time: {delete_time*1000:.2f}ms")
            print(f"  Status: {resp.status}")
            print()
        
        print("="*80)
        print("Summary")
        print("="*80)
        print(f"CREATE: {create_time*1000:.2f}ms")
        print(f"READ:   {read_time*1000:.2f}ms")
        print(f"UPDATE: {update_time*1000:.2f}ms")
        print(f"DELETE: {delete_time*1000:.2f}ms")


if __name__ == "__main__":
    asyncio.run(test_with_timing())

