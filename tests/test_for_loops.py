#!/usr/bin/env python3
"""
Test script to analyze the for loop parsing issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_for_loops():
    """Test for loop statements that are currently failing."""

    checker = OverpassQLSyntaxChecker()

    # Test various for loop constructs
    test_queries = [
        # Basic for loops that should work
        "for(user()) { out; }",
        'for(t["name"]) { out; }',
        # Problematic syntax from failing queries
        'for .all (t["name"]) { out; }',
        'for .all(t["name"]) { out; }',
        # Alternative syntax variations
        "for (.all) { out; }",
        '.all; for(t["name"]) { out; }',
        # Complex scenarios like in the failing query
        (
            'for .all (t["name"]){ if (count(nodes)+count(ways)+count(relations) > 10) '
            "{ make numerous name=_.val; }}"
        ),
        # Test with different set references
        'for .result (t["key"]) { out; }',
        'for ._  (t["value"]) { out; }',
    ]

    print("Testing for loop statements...")
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
    test_for_loops()
