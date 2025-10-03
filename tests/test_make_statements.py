#!/usr/bin/env python3
"""
Test script to analyze the make statement parsing issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_make_statements():
    """Test make statements that are currently failing."""

    checker = OverpassQLSyntaxChecker()

    # Simplified versions of the failing queries focusing on make statement
    test_queries = [
        # Basic make statement
        "make stat user=_.val",
        # Make with multiple assignments
        "make stat user=_.val, num=count(nwr)",
        # For loop with make (simplified from query 2)
        "for(user()) { make stat user=_.val, num=count(nwr); out; }",
        # Make with underscore variable (query 6)
        'make out _row="row type id lat lon name"',
        # Make with identifier (query 13)
        "make nom _row=_.val",
        # CSV output with special columns (query 6)
        '[out:csv("_row",::type,::id,::user,::lat,::lon,"name";false)]',
        # CSV output (query 17)
        "[out:csv(::type, ::id, name, admin_level, parent)]",
        # Convert statement (query 7)
        'convert rel ::id = id(), name=t["name"];',
        # Different syntaxes to test
        "make result name=_.val",
        'make result name=t["name"]',
        "make result value=count(ways)",
    ]

    print("Testing make statements...")
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
    test_make_statements()
