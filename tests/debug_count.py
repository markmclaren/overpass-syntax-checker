#!/usr/bin/env python3
"""
Debug script for the count(nwr) issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def debug_count_function():
    """Debug the count(nwr) parsing issue."""

    checker = OverpassQLSyntaxChecker()

    # Test various count functions
    test_queries = [
        "count(ways)",
        "count(nodes)",
        "count(relations)",
        "count(nwr)",
        "make stat num=count(ways)",
        "make stat num=count(nwr)",
        "make stat num=count(relations)",
    ]

    print("Testing count functions...")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        try:
            result = checker.check_syntax(query)
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            print(f"Query {i}: {status}")
            print(f"  {query}")
            if not result["valid"]:
                for error in result["errors"]:
                    print(f"  Error: {error}")
            print()
        except Exception as e:
            print(f"Query {i}: 💥 EXCEPTION")
            print(f"  {query}")
            print(f"  Exception: {e}")
            print()


if __name__ == "__main__":
    debug_count_function()
