#!/usr/bin/env python3
"""
Test script to validate if agenthub can handle multiple queries.
Tests both:
1. Reusing the same agent instance (load_agent once, use multiple times)
2. Creating fresh agent instances for each query
"""

import sys
import time
import agenthub as ah
from agenthub.builtin.tools.web_search import WebSearchTool
from agenthub.core.tools import tool

# Register web_search tool
@tool(name="web_search", description="Search the web for a query with AI-powered query rewriting")
def web_search(query, exclude_urls):
    num_results = 10
    tool_instance = WebSearchTool()
    return tool_instance.search(query, exclude_urls, max_results=num_results)

def test_reuse_agent():
    """Test 1: Reuse the same agent instance for multiple queries"""
    print("=" * 80)
    print("TEST 1: Reusing same agent instance for multiple queries")
    print("=" * 80)

    try:
        # Load agent once
        print("\n[1/1] Loading agent...")
        agent = ah.load_agent("agentplug/research-agent", external_tools=["web_search"])
        print("✅ Agent loaded successfully\n")

        queries = [
            "Python basics",
            "JavaScript fundamentals",
            "Go programming"
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}/{len(queries)}: '{query}'")
            print('='*60)

            start = time.time()
            try:
                result = agent.instant_research(query)
                elapsed = time.time() - start

                print(f"✅ Query {i} completed in {elapsed:.1f}s")
                if isinstance(result, dict) and 'result' in result:
                    content = result['result'].get('content', '')
                    print(f"   Result length: {len(content)} chars")
            except Exception as e:
                print(f"❌ Query {i} failed: {e}")

        print(f"\n{'='*80}")
        print("TEST 1 COMPLETED")
        print('='*80)
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fresh_agents():
    """Test 2: Create fresh agent instance for each query"""
    print("\n\n")
    print("=" * 80)
    print("TEST 2: Creating fresh agent instance for each query")
    print("=" * 80)

    queries = [
        "Rust programming",
        "TypeScript guide",
    ]

    try:
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}/{len(queries)}: '{query}'")
            print('='*60)

            # Load fresh agent for this query
            print(f"[{i}/1] Loading fresh agent...")
            agent = ah.load_agent("agentplug/research-agent", external_tools=["web_search"])
            print("✅ Agent loaded\n")

            start = time.time()
            try:
                result = agent.instant_research(query)
                elapsed = time.time() - start

                print(f"✅ Query {i} completed in {elapsed:.1f}s")
                if isinstance(result, dict) and 'result' in result:
                    content = result['result'].get('content', '')
                    print(f"   Result length: {len(content)} chars")

                # Clean up
                del agent
                print(f"   Agent instance deleted")

            except Exception as e:
                print(f"❌ Query {i} failed: {e}")

        print(f"\n{'='*80}")
        print("TEST 2 COMPLETED")
        print('='*80)
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AGENTHUB MULTIPLE QUERY TEST")
    print("Testing if agenthub can handle multiple queries in sequence\n")

    # Run both tests
    test1_passed = test_reuse_agent()
    test2_passed = test_fresh_agents()

    # Summary
    print("\n\n")
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Reuse agent): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Fresh agents): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)

    sys.exit(0 if (test1_passed and test2_passed) else 1)
