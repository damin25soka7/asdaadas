#!/usr/bin/env python3
"""
MCP Server Test Script

This script tests the MCP server functionality by:
1. Checking server health
2. Testing tool listing
3. Testing each plugin with sample data
"""

import asyncio
import json
import httpx
import sys

SERVER_URL = "http://localhost:32769"

class MCPTester:
    def __init__(self, server_url):
        self.server_url = server_url
        self.message_id = 1
        self.passed = 0
        self.failed = 0

    async def test(self, name, test_func):
        """Run a test and track results"""
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {name}")
        print('='*60)
        try:
            result = await test_func()
            print(f"✅ PASSED")
            self.passed += 1
            return result
        except Exception as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            return None

    async def check_health(self):
        """Test health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.server_url}/health")
            response.raise_for_status()
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Plugins: {data['plugins']}")
            print(f"Tools: {', '.join(data['available_tools'])}")
            return data

    async def call_mcp_method(self, method, params=None):
        """Call an MCP method"""
        request = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        self.message_id += 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.server_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()

    async def test_tools_list(self):
        """Test listing tools"""
        result = await self.call_mcp_method("tools/list")
        tools = result.get("result", {}).get("tools", [])
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        return tools

    async def test_search(self):
        """Test search plugin"""
        result = await self.call_mcp_method("tools/call", {
            "name": "search",
            "arguments": {
                "query": "python programming",
                "limit": 3
            }
        })
        
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(content)
        
        print(f"Query: {data.get('query')}")
        print(f"Results count: {data.get('results_count')}")
        if data.get('results'):
            print(f"First result: {data['results'][0].get('title', 'N/A')}")
        return data

    async def test_datetime(self):
        """Test datetime plugin"""
        result = await self.call_mcp_method("tools/call", {
            "name": "get_current_datetime",
            "arguments": {
                "timezone": "Asia/Seoul"
            }
        })
        
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(content)
        
        print(f"Timezone: {data.get('timezone')}")
        print(f"DateTime: {data.get('datetime')}")
        print(f"Formatted: {data.get('formatted')}")
        return data

    async def test_fetch_webpage(self):
        """Test webpage fetching"""
        result = await self.call_mcp_method("tools/call", {
            "name": "fetch_webpage",
            "arguments": {
                "url": "https://example.com",
                "max_length": 500
            }
        })
        
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(content)
        
        print(f"Total URLs: {data.get('total_urls')}")
        print(f"Successful: {data.get('successful')}")
        print(f"Failed: {data.get('failed')}")
        if data.get('results'):
            first_result = data['results'][0]
            print(f"Content length: {first_result.get('content_length', 0)} chars")
        return data

    async def test_tool_planner(self):
        """Test tool planner"""
        result = await self.call_mcp_method("tools/call", {
            "name": "tool_planner",
            "arguments": {
                "task": "Find recent news about artificial intelligence",
                "max_steps": 3
            }
        })
        
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(content)
        
        print(f"Task: {data.get('task')}")
        print(f"Steps planned: {len(data.get('plan', []))}")
        if data.get('plan'):
            for i, step in enumerate(data['plan'][:3], 1):
                print(f"  Step {i}: {step.get('tool')} - {step.get('reasoning', 'N/A')[:50]}...")
        return data

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 MCP SERVER TEST SUITE")
        print("="*60)
        print(f"Server URL: {self.server_url}")

        # Test health endpoint
        await self.test("Health Check", self.check_health)

        # Test MCP protocol
        await self.test("List Tools", self.test_tools_list)
        await self.test("DateTime Plugin", self.test_datetime)
        await self.test("Search Plugin", self.test_search)
        await self.test("Fetch Webpage Plugin", self.test_fetch_webpage)
        await self.test("Tool Planner Plugin", self.test_tool_planner)

        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        print("="*60)

        return self.failed == 0


async def main():
    """Main test runner"""
    import sys
    
    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else SERVER_URL
    
    tester = MCPTester(server_url)
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
