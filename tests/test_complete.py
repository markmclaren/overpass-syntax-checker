#!/usr/bin/env python3
"""
Test script to analyze the complete statement parsing issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_complete_statements():
    """Test complete statement variants."""

    checker = OverpassQLSyntaxChecker()

    test_queries = [
        # Basic complete statements
        "complete",
        "complete;",
        "complete { out; }",
        # Complete with parameters (the problematic ones)
        "complete(30)",
        "complete(30);",
        "complete(30) { out; }",
        "complete(30){ out; }",
        # From the failing query
        'complete(30){way["waterway"~"river"]; out;}',
        # Other variants
        "complete(10) { node; out; }",
        "complete(50){ rel; out; }",
    ]

    print("Testing complete statements...")
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
    test_complete_statements()
